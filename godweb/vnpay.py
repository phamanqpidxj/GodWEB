"""VNPay payment-gateway helpers.

Implements the request signing and response verification scheme described in
``https://sandbox.vnpayment.vn/apis/docs/thanh-toan-pay/pay.html``:

* Sort every ``vnp_*`` parameter by key.
* URL-encode keys + values with ``quote_plus`` (spaces become ``+``) and join
  with ``&`` to build the canonical "hash data" string.
* Sign that string with HMAC-SHA512 using ``vnp_HashSecret`` as the key, hex
  digest, lowercase / uppercase agnostic. The signature is sent as
  ``vnp_SecureHash``.

The functions here are deliberately framework-agnostic so they can be unit
tested without spinning up a Flask request context.
"""

from __future__ import annotations

import hashlib
import hmac
import os
from typing import Mapping
from urllib.parse import quote_plus, urlencode

DEFAULT_PAY_URL = 'https://sandbox.vnpayment.vn/paymentv2/vpcpay.html'


class VNPayConfigError(RuntimeError):
    """Raised when VNPay credentials are missing in the environment."""


def get_config() -> dict:
    """Load runtime VNPay configuration from environment variables.

    Returns a dict with at least ``tmn_code``, ``hash_secret``, ``pay_url``.
    Raises :class:`VNPayConfigError` if any required value is missing so
    callers can surface a friendly error instead of redirecting the user to
    a half-built payment URL.
    """
    tmn_code = os.environ.get('VNPAY_TMN_CODE', '').strip()
    hash_secret = os.environ.get('VNPAY_HASH_SECRET', '').strip()
    pay_url = os.environ.get('VNPAY_URL', DEFAULT_PAY_URL).strip() or DEFAULT_PAY_URL
    if not tmn_code or not hash_secret:
        raise VNPayConfigError(
            'VNPAY_TMN_CODE and VNPAY_HASH_SECRET must be set in the environment.'
        )
    return {
        'tmn_code': tmn_code,
        'hash_secret': hash_secret,
        'pay_url': pay_url,
    }


def _canonical_data(params: Mapping[str, object]) -> str:
    """Return the ``key=value&...`` string used as HMAC input.

    Only ``vnp_*`` keys with non-empty values participate, matching VNPay's
    reference Python demo. Keys are sorted alphabetically, then encoded with
    ``quote_plus`` so the same scheme is used for hashing and for the final
    URL query string.
    """
    items = sorted(
        (k, v) for k, v in params.items()
        if k.startswith('vnp_') and v not in (None, '')
    )
    return '&'.join(f'{quote_plus(str(k))}={quote_plus(str(v))}' for k, v in items)


def sign(params: Mapping[str, object], hash_secret: str) -> str:
    """Compute the ``vnp_SecureHash`` value for a parameter set."""
    data = _canonical_data(params)
    return hmac.new(
        hash_secret.encode('utf-8'),
        data.encode('utf-8'),
        hashlib.sha512,
    ).hexdigest()


def build_payment_url(params: Mapping[str, object], hash_secret: str, pay_url: str) -> str:
    """Build a fully signed VNPay redirect URL from the supplied parameters."""
    secure_hash = sign(params, hash_secret)
    query = _canonical_data(params)
    # Use the same canonical encoding so the merchant URL exactly matches the
    # bytes that were signed; appending via ``urlencode`` could re-quote
    # characters differently and break verification on VNPay's side.
    return f'{pay_url}?{query}&vnp_SecureHash={secure_hash}'


def verify_response(params: Mapping[str, object], hash_secret: str) -> bool:
    """Return True iff the ``vnp_SecureHash`` in ``params`` is valid.

    The provided hash is removed from the parameter map before recomputing
    the signature, mirroring VNPay's reference implementation.
    """
    received = str(params.get('vnp_SecureHash', '') or '')
    if not received:
        return False
    filtered = {k: v for k, v in params.items() if k not in ('vnp_SecureHash', 'vnp_SecureHashType')}
    expected = sign(filtered, hash_secret)
    # Constant-time comparison; both sides are hex so case-insensitive match.
    return hmac.compare_digest(expected.lower(), received.lower())


# IPN response codes per VNPay spec
IPN_SUCCESS = {'RspCode': '00', 'Message': 'Confirm Success'}
IPN_ORDER_NOT_FOUND = {'RspCode': '01', 'Message': 'Order not Found'}
IPN_ORDER_ALREADY_CONFIRMED = {'RspCode': '02', 'Message': 'Order already confirmed'}
IPN_INVALID_AMOUNT = {'RspCode': '04', 'Message': 'Invalid amount'}
IPN_INVALID_SIGNATURE = {'RspCode': '97', 'Message': 'Invalid Checksum'}
IPN_UNKNOWN_ERROR = {'RspCode': '99', 'Message': 'Unknown error'}


__all__ = [
    'VNPayConfigError',
    'get_config',
    'sign',
    'build_payment_url',
    'verify_response',
    'IPN_SUCCESS',
    'IPN_ORDER_NOT_FOUND',
    'IPN_ORDER_ALREADY_CONFIRMED',
    'IPN_INVALID_AMOUNT',
    'IPN_INVALID_SIGNATURE',
    'IPN_UNKNOWN_ERROR',
]
