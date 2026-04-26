from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from godweb.models import Product, Order, Transaction
from godweb.extensions import db
from godweb.utils import (
    normalize_inventory_parse_mode,
    parse_inventory_accounts,
    write_inventory_accounts,
    consume_inventory_folder_account,
    list_inventory_folder_files,
    read_inventory_folder_account,
)
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

    inventory_type = getattr(product, 'inventory_type', 'file') or 'file'
    upload_folder = current_app.config['UPLOAD_FOLDER']

    account_info = None
    remaining_stock = 0

    # Check balance
    if current_user.godcoin_balance < product.price:
        flash('Số dư GodCoin không đủ! Vui lòng nạp thêm.', 'error')
        return redirect(url_for('wallet.topup'))

    if inventory_type == 'folder':
        if not getattr(product, 'inventory_folder_path', None):
            flash('Sản phẩm chưa có hàng!', 'error')
            return redirect(url_for('store.detail', product_id=product_id))

        folder_path = os.path.join(upload_folder, product.inventory_folder_path)
        if not os.path.isdir(folder_path):
            flash('Thư mục tài khoản không tồn tại!', 'error')
            return redirect(url_for('store.detail', product_id=product_id))

        files = list_inventory_folder_files(folder_path)
        if not files:
            flash('Sản phẩm đã hết hàng!', 'error')
            product.stock = 0
            db.session.commit()
            return redirect(url_for('store.detail', product_id=product_id))

        selected_filename = files[0]
        account_info = read_inventory_folder_account(folder_path, selected_filename)
        consume_inventory_folder_account(folder_path, selected_filename)
        remaining_stock = len(files) - 1
    else:
        # Check if product has legacy inventory file
        if not product.inventory_file:
            flash('Sản phẩm chưa có hàng!', 'error')
            return redirect(url_for('store.detail', product_id=product_id))

        filepath = os.path.join(upload_folder, product.inventory_file)

        if not os.path.exists(filepath):
            flash('File tài khoản không tồn tại!', 'error')
            return redirect(url_for('store.detail', product_id=product_id))

        parse_mode = normalize_inventory_parse_mode(getattr(product, 'parse_mode', 'line'))
        accounts = parse_inventory_accounts(filepath, parse_mode)

        if not accounts:
            flash('Sản phẩm đã hết hàng!', 'error')
            product.stock = 0
            db.session.commit()
            return redirect(url_for('store.detail', product_id=product_id))

        account_info = accounts[0]
        remaining_accounts = accounts[1:]

        # Write remaining accounts back to file using the same format mode
        write_inventory_accounts(filepath, remaining_accounts, parse_mode)
        remaining_stock = len(remaining_accounts)

    # Process purchase
    current_user.godcoin_balance -= product.price
    product.stock = remaining_stock
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
