from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import Transaction, Topup
from extensions import db

wallet_bp = Blueprint('wallet', __name__)

@wallet_bp.route('/')
@login_required
def index():
    transactions = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.created_at.desc()).limit(10).all()
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

        if method not in ['momo', 'bank']:
            flash('Phương thức thanh toán không hợp lệ!', 'error')
            return render_template('wallet/topup.html')

        # Calculate GodCoin (1000 VND = 1 GodCoin)
        godcoin_amount = amount // 1000

        topup_request = Topup(
            user_id=current_user.id,
            amount=amount,
            godcoin_amount=godcoin_amount,
            method=method
        )
        db.session.add(topup_request)
        db.session.commit()

        flash(f'Yêu cầu nạp {godcoin_amount} GodCoin đã được gửi! Vui lòng chuyển khoản và chờ admin xác nhận.', 'success')
        return redirect(url_for('wallet.topup_history'))

    return render_template('wallet/topup.html')

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
