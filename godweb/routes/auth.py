from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from godweb.models import User
from godweb.extensions import db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = request.form.get('remember', False)

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            login_user(user, remember=remember)
            flash('Đăng nhập thành công!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page if next_page else url_for('main.home'))
        else:
            flash('Email hoặc mật khẩu không đúng!', 'error')

    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))

    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        recovery_number = request.form.get('recovery_number')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password != confirm_password:
            flash('Mật khẩu xác nhận không khớp!', 'error')
            return render_template('auth/register.html')

        if User.query.filter_by(email=email).first():
            flash('Email đã được sử dụng!', 'error')
            return render_template('auth/register.html')

        if User.query.filter_by(username=username).first():
            flash('Tên người dùng đã tồn tại!', 'error')
            return render_template('auth/register.html')

        if not recovery_number or not recovery_number.isdigit() or len(recovery_number) < 4:
            flash('Số khôi phục phải là số và có ít nhất 4 ký tự!', 'error')
            return render_template('auth/register.html')

        user = User(username=username, email=email, recovery_number=recovery_number)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash('Đăng ký thành công! Vui lòng đăng nhập.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html')

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))

    if request.method == 'POST':
        email = request.form.get('email')
        recovery_number = request.form.get('recovery_number')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        if new_password != confirm_password:
            flash('Mật khẩu xác nhận không khớp!', 'error')
            return render_template('auth/forgot_password.html')

        if not recovery_number or not recovery_number.isdigit():
            flash('Số khôi phục không hợp lệ!', 'error')
            return render_template('auth/forgot_password.html')

        user = User.query.filter_by(email=email).first()

        if not user or not user.recovery_number or user.recovery_number != recovery_number:
            flash('Email hoặc số khôi phục không đúng!', 'error')
            return render_template('auth/forgot_password.html')

        if len(new_password) < 6:
            flash('Mật khẩu mới phải có ít nhất 6 ký tự!', 'error')
            return render_template('auth/forgot_password.html')

        user.set_password(new_password)
        db.session.commit()
        login_user(user)
        flash('Đặt lại mật khẩu thành công!', 'success')
        return redirect(url_for('main.home'))

    return render_template('auth/forgot_password.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Đã đăng xuất thành công!', 'success')
    return redirect(url_for('main.home'))
