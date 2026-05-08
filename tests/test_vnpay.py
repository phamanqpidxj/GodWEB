"""Tests for the VNPay payment integration.

These cover the offline cryptographic helpers (sign/verify, URL building) and
the IPN endpoint contract — happy path, signature failure, amount mismatch,
order not found, and idempotency on a second IPN for the same ref.
"""
from __future__ import annotations

import hashlib
import hmac
from urllib.parse import quote_plus

import pytest

from godweb.extensions import db
from godweb.models import Topup, Transaction, User
from godweb.vnpay import build_payment_url, sign, verify_response


TEST_TMN = 'TESTTMN1'
TEST_SECRET = 'SECRETSECRET12345678'


# ---- sign / verify ---------------------------------------------------------

def test_sign_matches_reference_implementation():
    """Manually compute the HMAC-SHA512 to confirm we match VNPay's spec."""
    params = {
        'vnp_Amount': '10000000',
        'vnp_Command': 'pay',
        'vnp_TmnCode': TEST_TMN,
        'vnp_TxnRef': 'ABC123',
        'vnp_Version': '2.1.0',
    }
    canonical = '&'.join(
        f'{quote_plus(k)}={quote_plus(v)}'
        for k, v in sorted(params.items())
    )
    expected = hmac.new(
        TEST_SECRET.encode(), canonical.encode(), hashlib.sha512,
    ).hexdigest()
    assert sign(params, TEST_SECRET) == expected


def test_sign_ignores_non_vnp_keys_and_empty_values():
    base = {'vnp_TmnCode': TEST_TMN, 'vnp_Amount': '100'}
    extra = {**base, 'foo': 'bar', 'vnp_Skip': '', 'vnp_None': None}
    assert sign(base, TEST_SECRET) == sign(extra, TEST_SECRET)


def test_verify_response_round_trip():
    params = {
        'vnp_Amount': '10000000',
        'vnp_TxnRef': 'GODWEB-1-ABCD',
        'vnp_ResponseCode': '00',
    }
    sig = sign(params, TEST_SECRET)
    assert verify_response({**params, 'vnp_SecureHash': sig}, TEST_SECRET)


def test_verify_response_rejects_tampered_amount():
    params = {
        'vnp_Amount': '10000000',
        'vnp_TxnRef': 'GODWEB-1-ABCD',
        'vnp_ResponseCode': '00',
    }
    sig = sign(params, TEST_SECRET)
    tampered = {**params, 'vnp_Amount': '99999900', 'vnp_SecureHash': sig}
    assert not verify_response(tampered, TEST_SECRET)


def test_verify_response_rejects_missing_hash():
    assert not verify_response({'vnp_Amount': '1'}, TEST_SECRET)


def test_build_payment_url_contains_signed_query():
    params = {
        'vnp_Version': '2.1.0',
        'vnp_TmnCode': TEST_TMN,
        'vnp_Amount': '10000000',
        'vnp_TxnRef': 'GODWEB-7-XYZ',
    }
    url = build_payment_url(params, TEST_SECRET, 'https://example/vpcpay.html')
    assert url.startswith('https://example/vpcpay.html?')
    assert 'vnp_SecureHash=' in url
    # Confirm the URL we hand to the user round-trips through verify_response.
    query = url.split('?', 1)[1]
    parsed = dict(part.split('=', 1) for part in query.split('&'))
    assert verify_response(
        {k: v for k, v in parsed.items()},
        TEST_SECRET,
    )


# ---- IPN endpoint ----------------------------------------------------------

@pytest.fixture()
def vnpay_app(app, monkeypatch):
    """App fixture with VNPay env vars wired up."""
    monkeypatch.setenv('VNPAY_TMN_CODE', TEST_TMN)
    monkeypatch.setenv('VNPAY_HASH_SECRET', TEST_SECRET)
    monkeypatch.setenv('VNPAY_URL', 'https://sandbox.vnpayment.vn/paymentv2/vpcpay.html')
    return app


@pytest.fixture()
def vnpay_topup(vnpay_app):
    with vnpay_app.app_context():
        user = User(
            username='vnpay_user',
            email='v@example.com',
            password_hash='x',
            godcoin_balance=0,
        )
        db.session.add(user)
        db.session.commit()
        topup_obj = Topup(
            user_id=user.id,
            amount=100000,
            godcoin_amount=100,
            method='vnpay',
            status='pending',
            vnp_txn_ref='GODWEB-1-CAFEBABE',
        )
        db.session.add(topup_obj)
        db.session.commit()
        return {'user_id': user.id, 'topup_id': topup_obj.id, 'txn_ref': topup_obj.vnp_txn_ref}


def _signed_ipn_params(txn_ref: str, amount_vnd: int, response_code='00', transaction_status='00'):
    params = {
        'vnp_Amount': str(amount_vnd * 100),
        'vnp_BankCode': 'NCB',
        'vnp_OrderInfo': 'Nap GodCoin',
        'vnp_PayDate': '20251101120000',
        'vnp_ResponseCode': response_code,
        'vnp_TmnCode': TEST_TMN,
        'vnp_TransactionNo': '14000000',
        'vnp_TransactionStatus': transaction_status,
        'vnp_TxnRef': txn_ref,
    }
    params['vnp_SecureHash'] = sign(params, TEST_SECRET)
    return params


def test_ipn_credits_godcoin_on_success(client, vnpay_app, vnpay_topup):
    params = _signed_ipn_params(vnpay_topup['txn_ref'], 100000)
    resp = client.get('/wallet/vnpay/ipn', query_string=params)
    assert resp.status_code == 200
    assert resp.get_json() == {'RspCode': '00', 'Message': 'Confirm Success'}
    with vnpay_app.app_context():
        user = User.query.get(vnpay_topup['user_id'])
        topup_obj = Topup.query.get(vnpay_topup['topup_id'])
        assert user.godcoin_balance == 100
        assert topup_obj.status == 'approved'
        assert topup_obj.vnp_transaction_no == '14000000'
        assert Transaction.query.filter_by(user_id=user.id, type='topup').count() == 1


def test_ipn_is_idempotent(client, vnpay_app, vnpay_topup):
    params = _signed_ipn_params(vnpay_topup['txn_ref'], 100000)
    first = client.get('/wallet/vnpay/ipn', query_string=params)
    second = client.get('/wallet/vnpay/ipn', query_string=params)
    assert first.get_json()['RspCode'] == '00'
    assert second.get_json()['RspCode'] == '02'  # already confirmed
    with vnpay_app.app_context():
        user = User.query.get(vnpay_topup['user_id'])
        # Critical: balance must NOT double-credit on a retry.
        assert user.godcoin_balance == 100
        assert Transaction.query.filter_by(user_id=user.id, type='topup').count() == 1


def test_ipn_rejects_invalid_signature(client, vnpay_app, vnpay_topup):
    params = _signed_ipn_params(vnpay_topup['txn_ref'], 100000)
    params['vnp_SecureHash'] = 'a' * 128  # wrong hash
    resp = client.get('/wallet/vnpay/ipn', query_string=params)
    assert resp.get_json()['RspCode'] == '97'
    with vnpay_app.app_context():
        topup_obj = Topup.query.get(vnpay_topup['topup_id'])
        assert topup_obj.status == 'pending'  # untouched


def test_ipn_rejects_amount_mismatch(client, vnpay_app, vnpay_topup):
    params = _signed_ipn_params(vnpay_topup['txn_ref'], 50000)  # paid less
    resp = client.get('/wallet/vnpay/ipn', query_string=params)
    assert resp.get_json()['RspCode'] == '04'
    with vnpay_app.app_context():
        topup_obj = Topup.query.get(vnpay_topup['topup_id'])
        assert topup_obj.status == 'pending'


def test_ipn_rejects_unknown_order(client, vnpay_app):
    params = _signed_ipn_params('GODWEB-NOPE', 100000)
    resp = client.get('/wallet/vnpay/ipn', query_string=params)
    assert resp.get_json()['RspCode'] == '01'


def test_ipn_marks_failed_payment_rejected(client, vnpay_app, vnpay_topup):
    params = _signed_ipn_params(vnpay_topup['txn_ref'], 100000, response_code='24')
    resp = client.get('/wallet/vnpay/ipn', query_string=params)
    assert resp.get_json()['RspCode'] == '00'
    with vnpay_app.app_context():
        user = User.query.get(vnpay_topup['user_id'])
        topup_obj = Topup.query.get(vnpay_topup['topup_id'])
        assert topup_obj.status == 'rejected'
        assert topup_obj.vnp_response_code == '24'
        assert user.godcoin_balance == 0
