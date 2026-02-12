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

        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash('Đăng ký thành công! Vui lòng đăng nhập.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Đã đăng xuất thành công!', 'success')
    return redirect(url_for('main.home'))
