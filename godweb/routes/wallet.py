from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from godweb.models import Transaction, Topup
from godweb.extensions import db
from godweb.utils import upload_image as upload_image_util
from datetime import datetime

wallet_bp = Blueprint('wallet', __name__)

# Topup amount constraints
TOPUP_MIN_VND = 10000
TOPUP_MAX_VND = 50000000

# Preset amounts for quick selection
TOPUP_PRESETS = [
    {'value': 10000, 'label': '10,000'},
    {'value': 20000, 'label': '20,000'},
    {'value': 50000, 'label': '50,000'},
    {'value': 100000, 'label': '100,000'},
    {'value': 200000, 'label': '200,000'},
    {'value': 500000, 'label': '500,000'},
    {'value': 1000000, 'label': '1,000,000'},
]

@wallet_bp.route('/')
@login_required
def index():
    transactions = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.created_at.desc()).limit(10).all()
    pending_topups = Topup.query.filter_by(user_id=current_user.id, status='pending').count()
    return render_template('wallet/index.html', transactions=transactions, pending_topups=pending_topups)

@wallet_bp.route('/topup', methods=['GET', 'POST'])
@login_required
def topup():
    if request.method == 'POST':
        amount = request.form.get('amount', type=int)
        method = request.form.get('method')
        note = (request.form.get('note') or '').strip()[:255]

        if not amount or amount < TOPUP_MIN_VND:
            flash(f'Số tiền nạp tối thiểu là {TOPUP_MIN_VND:,.0f} VNĐ!', 'error')
            return render_template('wallet/topup.html', presets=TOPUP_PRESETS,
                                   min_amount=TOPUP_MIN_VND, max_amount=TOPUP_MAX_VND)

        if amount > TOPUP_MAX_VND:
            flash(f'Số tiền nạp tối đa là {TOPUP_MAX_VND:,.0f} VNĐ!', 'error')
            return render_template('wallet/topup.html', presets=TOPUP_PRESETS,
                                   min_amount=TOPUP_MIN_VND, max_amount=TOPUP_MAX_VND)

        if method not in ['momo', 'bank']:
            flash('Phương thức thanh toán không hợp lệ!', 'error')
            return render_template('wallet/topup.html', presets=TOPUP_PRESETS,
                                   min_amount=TOPUP_MIN_VND, max_amount=TOPUP_MAX_VND)

        # Calculate GodCoin (1000 VND = 1 GodCoin)
        godcoin_amount = amount // 1000

        # Handle proof image upload
        proof_url = None
        proof_file = request.files.get('proof_image')
        if proof_file and proof_file.filename:
            proof_url = upload_image_util(proof_file, folder='topup_proofs')

        topup_request = Topup(
            user_id=current_user.id,
            amount=amount,
            godcoin_amount=godcoin_amount,
            method=method,
            proof_image=proof_url,
            note=note if note else None,
        )
        db.session.add(topup_request)
        db.session.commit()

        flash(f'Yêu cầu nạp {godcoin_amount} GodCoin đã được gửi! Vui lòng chuyển khoản và chờ admin xác nhận.', 'success')
        return redirect(url_for('wallet.topup_history'))

    return render_template('wallet/topup.html', presets=TOPUP_PRESETS,
                           min_amount=TOPUP_MIN_VND, max_amount=TOPUP_MAX_VND)

@wallet_bp.route('/topup/<int:topup_id>/cancel', methods=['POST'])
@login_required
def cancel_topup(topup_id):
    topup_req = Topup.query.get_or_404(topup_id)

    if topup_req.user_id != current_user.id:
        flash('Bạn không có quyền thực hiện thao tác này!', 'error')
        return redirect(url_for('wallet.topup_history'))

    if topup_req.status != 'pending':
        flash('Chỉ có thể hủy yêu cầu đang chờ duyệt!', 'error')
        return redirect(url_for('wallet.topup_history'))

    topup_req.status = 'cancelled'
    topup_req.processed_at = datetime.utcnow()
    db.session.commit()

    flash('Đã hủy yêu cầu nạp tiền!', 'success')
    return redirect(url_for('wallet.topup_history'))

@wallet_bp.route('/topup/history')
@login_required
def topup_history():
    topups = Topup.query.filter_by(user_id=current_user.id).order_by(Topup.created_at.desc()).all()
    return render_template('wallet/topup_history.html', topups=topups)

@wallet_bp.route('/transactions')
@login_required
def transactions():
    page = request.args.get('page', 1, type=int)
    transactions = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.created_at.desc()).paginate(page=page, per_page=20)
    return render_template('wallet/transactions.html', transactions=transactions)
