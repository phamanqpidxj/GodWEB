from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from godweb.models import Product, Order, Transaction, User, ProductInventoryAccount
from godweb.extensions import db
from godweb.utils import (
    normalize_inventory_parse_mode,
    parse_inventory_accounts_text,
    serialize_inventory_accounts,
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

def _lock_row(model, row_id):
    """Acquire a row-level lock on (model, row_id) for the current transaction.

    Uses ``SELECT ... FOR UPDATE`` on engines that support it (Postgres, MySQL).
    SQLite ignores the locking hint but its default journal-mode locking already
    serializes write transactions, which is sufficient for tests / local dev.
    """
    query = db.session.query(model).filter(model.id == row_id)
    bind = db.session.get_bind()
    if bind.dialect.name in ('postgresql', 'mysql'):
        query = query.with_for_update()
    return query.first()


@store_bp.route('/<int:product_id>/buy', methods=['POST'])
@login_required
def buy(product_id):
    try:
        # Lock both rows for the duration of the transaction so concurrent
        # buyers can't double-spend the same balance or claim the same account.
        product = _lock_row(Product, product_id)
        if product is None:
            db.session.rollback()
            flash('Sản phẩm không tồn tại!', 'error')
            return redirect(url_for('store.index'))

        user = _lock_row(User, current_user.id)
        if user is None:
            db.session.rollback()
            flash('Phiên đăng nhập không hợp lệ!', 'error')
            return redirect(url_for('auth.login'))

        if user.godcoin_balance < product.price:
            db.session.rollback()
            flash('Số dư GodCoin không đủ! Vui lòng nạp thêm.', 'error')
            return redirect(url_for('wallet.topup'))

        inventory_type = getattr(product, 'inventory_type', 'file') or 'file'
        account_info = None
        remaining_stock = 0

        if inventory_type == 'folder':
            # Inventory accounts are persisted as DB rows so they survive dyno restarts.
            account_query = (
                db.session.query(ProductInventoryAccount)
                .filter_by(product_id=product.id)
                .order_by(ProductInventoryAccount.filename, ProductInventoryAccount.id)
            )
            bind = db.session.get_bind()
            if bind.dialect.name in ('postgresql', 'mysql'):
                account_query = account_query.with_for_update(skip_locked=True)
            account_row = account_query.first()

            if account_row is None:
                product.stock = 0
                db.session.commit()
                flash('Sản phẩm đã hết hàng!', 'error')
                return redirect(url_for('store.detail', product_id=product_id))

            account_info = (account_row.content or '').strip()
            db.session.delete(account_row)
            db.session.flush()
            remaining_stock = (
                db.session.query(ProductInventoryAccount)
                .filter_by(product_id=product.id)
                .count()
            )
        else:
            parse_mode = normalize_inventory_parse_mode(getattr(product, 'parse_mode', 'line'))
            inventory_data = getattr(product, 'inventory_data', None)
            accounts = parse_inventory_accounts_text(inventory_data, parse_mode) if inventory_data else []
            if not accounts:
                if not (inventory_data or product.inventory_file):
                    db.session.rollback()
                    flash('Sản phẩm chưa có hàng!', 'error')
                    return redirect(url_for('store.detail', product_id=product_id))
                product.stock = 0
                db.session.commit()
                flash('Sản phẩm đã hết hàng!', 'error')
                return redirect(url_for('store.detail', product_id=product_id))

            account_info = accounts[0]
            remaining_accounts = accounts[1:]
            product.inventory_data = serialize_inventory_accounts(remaining_accounts, parse_mode)
            remaining_stock = len(remaining_accounts)

        user.godcoin_balance -= product.price
        product.stock = remaining_stock
        product.sold_count = (product.sold_count or 0) + 1

        db.session.add(Order(
            user_id=user.id,
            product_id=product_id,
            account_info=account_info,
            price=product.price,
        ))
        db.session.add(Transaction(
            user_id=user.id,
            type='purchase',
            amount=-product.price,
            description=f'Mua sản phẩm: {product.name}',
        ))

        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    flash('Mua hàng thành công! Xem thông tin tài khoản trong lịch sử mua hàng.', 'success')
    return redirect(url_for('profile.orders'))

@store_bp.route('/history')
@login_required
def history():
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    return render_template('store/history.html', orders=orders)
