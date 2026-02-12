from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import Order, Transaction, PostPurchase
from extensions import db
import os
from werkzeug.utils import secure_filename

profile_bp = Blueprint('profile', __name__)

@profile_bp.route('/')
@login_required
def index():
    recent_transactions = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.created_at.desc()).limit(5).all()
    recent_orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).limit(5).all()
    return render_template('profile/index.html', transactions=recent_transactions, orders=recent_orders)

@profile_bp.route('/edit', methods=['GET', 'POST'])
@login_required
def edit():
    if request.method == 'POST':
        form_type = request.form.get('form_type')

        if form_type == 'profile':
            # Update profile info
            username = request.form.get('username')
            if username and username != current_user.username:
                from models import User
                if User.query.filter_by(username=username).first():
                    flash('Tên người dùng đã tồn tại!', 'error')
                else:
                    current_user.username = username
                    db.session.commit()
                    flash('Cập nhật thông tin thành công!', 'success')

        elif form_type == 'password':
            # Change password
            current_password = request.form.get('current_password')
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')

            if not current_user.check_password(current_password):
                flash('Mật khẩu hiện tại không đúng!', 'error')
            elif new_password != confirm_password:
                flash('Mật khẩu xác nhận không khớp!', 'error')
            elif len(new_password) < 6:
                flash('Mật khẩu mới phải có ít nhất 6 ký tự!', 'error')
            else:
                current_user.set_password(new_password)
                db.session.commit()
                flash('Đổi mật khẩu thành công!', 'success')

        return redirect(url_for('profile.edit'))

    return render_template('profile/edit.html')

@profile_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        if not current_user.check_password(current_password):
            flash('Mật khẩu hiện tại không đúng!', 'error')
        elif new_password != confirm_password:
            flash('Mật khẩu xác nhận không khớp!', 'error')
        elif len(new_password) < 6:
            flash('Mật khẩu mới phải có ít nhất 6 ký tự!', 'error')
        else:
            current_user.set_password(new_password)
            db.session.commit()
            flash('Đổi mật khẩu thành công!', 'success')
            return redirect(url_for('profile.index'))

    return render_template('profile/change_password.html')

@profile_bp.route('/orders')
@login_required
def orders():
    page = request.args.get('page', 1, type=int)
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).paginate(page=page, per_page=10)
    return render_template('profile/orders.html', orders=orders)

@profile_bp.route('/purchases')
@login_required
def purchases():
    page = request.args.get('page', 1, type=int)
    purchases = PostPurchase.query.filter_by(user_id=current_user.id).order_by(PostPurchase.created_at.desc()).paginate(page=page, per_page=10)
    return render_template('profile/purchases.html', purchases=purchases)
