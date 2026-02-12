from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from godweb.models import Product, Order, Transaction
from godweb.extensions import db
from datetime import datetime
import os

store_bp = Blueprint('store', __name__)

@store_bp.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')

    query = Product.query

    if search:
        query = query.filter(Product.name.contains(search) | Product.description.contains(search))

    products = query.order_by(Product.created_at.desc()).paginate(page=page, per_page=12)

    return render_template('store/index.html', products=products, search=search)

@store_bp.route('/<int:product_id>')
def detail(product_id):
    product = Product.query.get_or_404(product_id)
    return render_template('store/detail.html', product=product)

@store_bp.route('/<int:product_id>/buy', methods=['POST'])
@login_required
def buy(product_id):
    product = Product.query.get_or_404(product_id)

    # Check if product has inventory file
    if not product.inventory_file:
        flash('Sản phẩm chưa có hàng!', 'error')
        return redirect(url_for('store.detail', product_id=product_id))

    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], product.inventory_file)

    if not os.path.exists(filepath):
        flash('File tài khoản không tồn tại!', 'error')
        return redirect(url_for('store.detail', product_id=product_id))

    # Read file and get first line
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f.readlines() if line.strip()]

    if not lines:
        flash('Sản phẩm đã hết hàng!', 'error')
        product.stock = 0
        db.session.commit()
        return redirect(url_for('store.detail', product_id=product_id))

    # Check balance
    if current_user.godcoin_balance < product.price:
        flash('Số dư GodCoin không đủ! Vui lòng nạp thêm.', 'error')
        return redirect(url_for('wallet.topup'))

    # Get first account and remove it from file
    account_info = lines[0]
    remaining_lines = lines[1:]

    # Write remaining lines back to file
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write('\n'.join(remaining_lines))

    # Process purchase
    current_user.godcoin_balance -= product.price
    product.stock = len(remaining_lines)
    product.sold_count = (product.sold_count or 0) + 1

    order = Order(
        user_id=current_user.id,
        product_id=product_id,
        account_info=account_info,
        price=product.price
    )
    db.session.add(order)

    transaction = Transaction(
        user_id=current_user.id,
        type='purchase',
        amount=-product.price,
        description=f'Mua sản phẩm: {product.name}'
    )
    db.session.add(transaction)

    db.session.commit()

    flash('Mua hàng thành công! Xem thông tin tài khoản trong lịch sử mua hàng.', 'success')
    return redirect(url_for('profile.orders'))

@store_bp.route('/history')
@login_required
def history():
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    return render_template('store/history.html', orders=orders)
