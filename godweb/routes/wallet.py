import secrets
from datetime import datetime, timedelta, timezone

from flask import (
    Blueprint, render_template, request, redirect, url_for, flash,
    current_app, jsonify,
)
from flask_login import login_required, current_user

from godweb.extensions import db, csrf
from godweb.models import Topup, Transaction, User
from godweb.vnpay import (
    VNPayConfigError, build_payment_url, get_config, verify_response,
    IPN_INVALID_AMOUNT, IPN_INVALID_SIGNATURE, IPN_ORDER_ALREADY_CONFIRMED,
    IPN_ORDER_NOT_FOUND, IPN_SUCCESS, IPN_UNKNOWN_ERROR,
)

wallet_bp = Blueprint('wallet', __name__)

VND_PER_GODCOIN = 1000
VNPAY_TZ = timezone(timedelta(hours=7))  # Asia/Ho_Chi_Minh; VNPay expects this for vnp_CreateDate


def _vnpay_txn_ref(topup_id: int) -> str:
    """Build a unique merchant reference for a topup.

    Format ``GODWEB-<topup_id>-<8-char-random>`` keeps the topup id readable in
    VNPay's merchant admin while still being unique across attempts (a user
    could retry the same topup row, but each attempt should have its own ref).
    """
    return f'GODWEB-{topup_id}-{secrets.token_hex(4).upper()}'


def _client_ip() -> str:
    """Return the client IP, taking ProxyFix-corrected ``remote_addr``."""
    return request.remote_addr or '127.0.0.1'


@wallet_bp.route('/')
@login_required
def index():
    transactions = Transaction.query.filter_by(user_id=current_user.id)\
        .order_by(Transaction.created_at.desc()).limit(10).all()
    return render_template('wallet/index.html', transactions=transactions)


@wallet_bp.route('/topup', methods=['GET', 'POST'])
@login_required
def topup():
    if request.method == 'POST':
        amount = request.form.get('amount', type=int)
        method = request.form.get('method')

        if not amount or amount < 10000:
            flash('Số tiền nạp tối thiểu là 10,000 VNĐ!', 'error')
            return render_template('wallet/topup.html')

        if method not in ('momo', 'bank', 'vnpay'):
            flash('Phương thức thanh toán không hợp lệ!', 'error')
            return render_template('wallet/topup.html')

        godcoin_amount = amount // VND_PER_GODCOIN

        topup_request = Topup(
            user_id=current_user.id,
            amount=amount,
            godcoin_amount=godcoin_amount,
            method=method,
        )
        db.session.add(topup_request)
        db.session.commit()

        if method == 'vnpay':
            return redirect(url_for('wallet.vnpay_create', topup_id=topup_request.id))

        flash(
            f'Yêu cầu nạp {godcoin_amount} GodCoin đã được gửi! '
            'Vui lòng chuyển khoản và chờ admin xác nhận.',
            'success',
        )
        return redirect(url_for('wallet.topup_history'))

    return render_template('wallet/topup.html')


@wallet_bp.route('/topup/history')
@login_required
def topup_history():
    topups = Topup.query.filter_by(user_id=current_user.id)\
        .order_by(Topup.created_at.desc()).all()
    return render_template('wallet/topup_history.html', topups=topups)


@wallet_bp.route('/transactions')
@login_required
def transactions():
    page = request.args.get('page', 1, type=int)
    transactions = Transaction.query.filter_by(user_id=current_user.id)\
        .order_by(Transaction.created_at.desc()).paginate(page=page, per_page=20)
    return render_template('wallet/transactions.html', transactions=transactions)


# ---------------------------------------------------------------------------
# VNPay payment flow
# ---------------------------------------------------------------------------

@wallet_bp.route('/vnpay/create/<int:topup_id>')
@login_required
def vnpay_create(topup_id):
    """Build the signed VNPay redirect URL for ``topup_id`` and 302 to it."""
    topup_obj = Topup.query.get_or_404(topup_id)
    if topup_obj.user_id != current_user.id:
        flash('Yêu cầu nạp không thuộc về bạn!', 'error')
        return redirect(url_for('wallet.topup'))
    if topup_obj.method != 'vnpay':
        flash('Yêu cầu nạp này không dùng VNPay.', 'error')
        return redirect(url_for('wallet.topup_history'))
    if topup_obj.status != 'pending':
        flash('Yêu cầu nạp này đã được xử lý.', 'info')
        return redirect(url_for('wallet.topup_history'))

    try:
        cfg = get_config()
    except VNPayConfigError:
        current_app.logger.error('VNPay credentials missing; cannot start payment.')
        flash(
            'Cổng thanh toán VNPay chưa được cấu hình. Vui lòng liên hệ admin.',
            'error',
        )
        return redirect(url_for('wallet.topup'))

    if not topup_obj.vnp_txn_ref:
        topup_obj.vnp_txn_ref = _vnpay_txn_ref(topup_obj.id)
        db.session.commit()

    create_dt = datetime.now(VNPAY_TZ)
    expire_dt = create_dt + timedelta(minutes=15)
    return_url = current_app.config.get('VNPAY_RETURN_URL') \
        or url_for('wallet.vnpay_return', _external=True)

    params = {
        'vnp_Version': '2.1.0',
        'vnp_Command': 'pay',
        'vnp_TmnCode': cfg['tmn_code'],
        'vnp_Amount': str(topup_obj.amount * 100),  # VNPay expects smallest unit
        'vnp_CurrCode': 'VND',
        'vnp_TxnRef': topup_obj.vnp_txn_ref,
        # VNPay spec requires Vietnamese without diacritics and no special characters.
        'vnp_OrderInfo': f'Nap {topup_obj.godcoin_amount} GodCoin user {topup_obj.user_id}',
        'vnp_OrderType': 'other',
        'vnp_Locale': request.args.get('locale', 'vn'),
        'vnp_ReturnUrl': return_url,
        'vnp_IpAddr': _client_ip(),
        'vnp_CreateDate': create_dt.strftime('%Y%m%d%H%M%S'),
        'vnp_ExpireDate': expire_dt.strftime('%Y%m%d%H%M%S'),
    }
    bank_code = request.args.get('bank_code', '').strip()
    if bank_code:
        params['vnp_BankCode'] = bank_code

    pay_url = build_payment_url(params, cfg['hash_secret'], cfg['pay_url'])
    return redirect(pay_url)


@wallet_bp.route('/vnpay/return')
@login_required
def vnpay_return():
    """Render the user-visible result page after VNPay redirects them back.

    GodCoin is **not** credited here — that is the IPN endpoint's job. This
    route only verifies the signature and shows a status message so the user
    knows whether the gateway considers the payment successful.
    """
    try:
        cfg = get_config()
    except VNPayConfigError:
        flash('Cổng thanh toán VNPay chưa được cấu hình.', 'error')
        return redirect(url_for('wallet.topup_history'))

    params = request.args.to_dict()
    sig_ok = verify_response(params, cfg['hash_secret'])
    response_code = params.get('vnp_ResponseCode', '')
    txn_ref = params.get('vnp_TxnRef', '')
    amount_raw = params.get('vnp_Amount', '0')
    try:
        amount_vnd = int(amount_raw) // 100
    except (TypeError, ValueError):
        amount_vnd = 0

    topup_obj = Topup.query.filter_by(vnp_txn_ref=txn_ref).first() if txn_ref else None
    success = sig_ok and response_code == '00'
    return render_template(
        'wallet/vnpay_return.html',
        success=success,
        sig_ok=sig_ok,
        response_code=response_code,
        amount_vnd=amount_vnd,
        topup=topup_obj,
        params=params,
    )


@wallet_bp.route('/vnpay/ipn', methods=['GET', 'POST'])
@csrf.exempt
def vnpay_ipn():
    """Server-to-server callback from VNPay confirming payment status.

    This is the **authoritative** signal that money actually moved. We:
    1. Verify the HMAC-SHA512 signature; reject otherwise.
    2. Look up the topup by ``vnp_TxnRef``.
    3. Validate that the gateway-reported amount matches what we charged.
    4. On success, credit GodCoin exactly once (idempotent: already-confirmed
       topups return ``02`` so VNPay doesn't keep retrying).

    VNPay expects a JSON body with ``RspCode`` + ``Message``; anything else
    causes them to retry the IPN repeatedly.
    """
    # VNPay sends params in the query string for both GET and POST IPN. Merge
    # to be defensive against either delivery mode.
    params = {}
    params.update(request.args.to_dict())
    params.update(request.form.to_dict())

    try:
        cfg = get_config()
    except VNPayConfigError:
        current_app.logger.error('VNPay IPN received but credentials are not configured.')
        return jsonify(IPN_UNKNOWN_ERROR)

    if not verify_response(params, cfg['hash_secret']):
        current_app.logger.warning('VNPay IPN: invalid signature for ref=%s',
                                   params.get('vnp_TxnRef'))
        return jsonify(IPN_INVALID_SIGNATURE)

    txn_ref = params.get('vnp_TxnRef', '')
    response_code = params.get('vnp_ResponseCode', '')
    transaction_status = params.get('vnp_TransactionStatus', '')
    transaction_no = params.get('vnp_TransactionNo', '')
    try:
        ipn_amount_vnd = int(params.get('vnp_Amount', '0')) // 100
    except (TypeError, ValueError):
        ipn_amount_vnd = -1

    topup_obj = Topup.query.filter_by(vnp_txn_ref=txn_ref).first()
    if topup_obj is None:
        return jsonify(IPN_ORDER_NOT_FOUND)

    if topup_obj.amount != ipn_amount_vnd:
        current_app.logger.warning(
            'VNPay IPN amount mismatch ref=%s expected=%s got=%s',
            txn_ref, topup_obj.amount, ipn_amount_vnd,
        )
        return jsonify(IPN_INVALID_AMOUNT)

    if topup_obj.status != 'pending':
        # Already credited (or rejected). Tell VNPay so they stop retrying.
        return jsonify(IPN_ORDER_ALREADY_CONFIRMED)

    topup_obj.vnp_transaction_no = transaction_no
    topup_obj.vnp_response_code = response_code

    if response_code == '00' and transaction_status == '00':
        user = User.query.get(topup_obj.user_id)
        if user is None:
            db.session.commit()
            return jsonify(IPN_ORDER_NOT_FOUND)
        user.godcoin_balance = (user.godcoin_balance or 0) + topup_obj.godcoin_amount
        topup_obj.status = 'approved'
        topup_obj.processed_at = datetime.utcnow()
        db.session.add(Transaction(
            user_id=user.id,
            type='topup',
            amount=topup_obj.godcoin_amount,
            description=f'Nạp GodCoin qua VNPay (ref {txn_ref})',
        ))
        db.session.commit()
        return jsonify(IPN_SUCCESS)

    # Gateway reported a non-success code; mark rejected so further IPN
    # retries are short-circuited but we keep the response code for support.
    topup_obj.status = 'rejected'
    topup_obj.processed_at = datetime.utcnow()
    db.session.commit()
    return jsonify(IPN_SUCCESS)
