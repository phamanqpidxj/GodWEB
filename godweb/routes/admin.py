from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from godweb.models import User, Post, Category, Product, Transaction, Topup, Order
from godweb.extensions import db
from functools import wraps
import os
from werkzeug.utils import secure_filename
from datetime import datetime
from godweb.utils import upload_image as upload_image_util

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash('Bạn không có quyền truy cập trang này!', 'error')
            return redirect(url_for('main.home'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    stats = {
        'users': User.query.count(),
        'posts': Post.query.count(),
        'products': Product.query.count(),
        'orders': Order.query.count(),
        'pending_topups': Topup.query.filter_by(status='pending').count(),
        'total_godcoin': db.session.query(db.func.sum(User.godcoin_balance)).scalar() or 0
    }
    recent_topups = Topup.query.filter_by(status='pending').order_by(Topup.created_at.desc()).limit(5).all()
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(5).all()
    return render_template('admin/dashboard.html', stats=stats, recent_topups=recent_topups, recent_orders=recent_orders)

# Users Management
@admin_bp.route('/users')
@login_required
@admin_required
def users():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')

    query = User.query

    if search:
        # Search by ID, username or email
        if search.isdigit():
            query = query.filter(User.id == int(search))
        else:
            query = query.filter(
                db.or_(
                    User.username.contains(search),
                    User.email.contains(search)
                )
            )

    users = query.order_by(User.created_at.desc()).paginate(page=page, per_page=20)
    return render_template('admin/users.html', users=users)

@admin_bp.route('/users/quick-add-coin', methods=['POST'])
@login_required
@admin_required
def quick_add_coin():
    user_id = request.form.get('user_id', type=int)
    amount = request.form.get('amount', type=int)
    action = request.form.get('action')

    if not user_id or not amount or amount <= 0:
        flash('Vui lòng nhập đầy đủ ID và số lượng GodCoin!', 'error')
        return redirect(url_for('admin.users'))

    user = User.query.get(user_id)

    if not user:
        flash(f'Không tìm thấy người dùng với ID #{user_id}!', 'error')
        return redirect(url_for('admin.users'))

    if action == 'add':
        user.godcoin_balance += amount
        transaction = Transaction(
            user_id=user_id,
            type='admin_add',
            amount=amount,
            description=f'Admin cộng GodCoin'
        )
        db.session.add(transaction)
        db.session.commit()
        flash(f'Đã cộng {amount} GodCoin cho {user.username} (ID #{user_id})! Số dư mới: {user.godcoin_balance} GC', 'success')
    else:
        if user.godcoin_balance >= amount:
            user.godcoin_balance -= amount
            transaction = Transaction(
                user_id=user_id,
                type='admin_subtract',
                amount=-amount,
                description=f'Admin trừ GodCoin'
            )
            db.session.add(transaction)
            db.session.commit()
            flash(f'Đã trừ {amount} GodCoin của {user.username} (ID #{user_id})! Số dư mới: {user.godcoin_balance} GC', 'success')
        else:
            flash(f'Số dư không đủ để trừ! {user.username} chỉ có {user.godcoin_balance} GC', 'error')

    return redirect(url_for('admin.users'))

@admin_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)

    if request.method == 'POST':
        user.username = request.form.get('username')
        user.email = request.form.get('email')
        user.role = request.form.get('role')
        db.session.commit()
        flash('Cập nhật người dùng thành công!', 'success')
        return redirect(url_for('admin.users'))

    return render_template('admin/edit_user.html', user=user)

@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)

    if user.id == current_user.id:
        flash('Không thể xóa tài khoản đang đăng nhập!', 'error')
        return redirect(url_for('admin.users'))

    if user.is_admin():
        flash('Không thể xóa tài khoản admin!', 'error')
        return redirect(url_for('admin.users'))

    db.session.delete(user)
    db.session.commit()
    flash(f'Đã xóa tài khoản {user.username}!', 'success')
    return redirect(url_for('admin.users'))

@admin_bp.route('/users/<int:user_id>/balance', methods=['POST'])
@login_required
@admin_required
def adjust_balance(user_id):
    user = User.query.get_or_404(user_id)
    amount = request.form.get('amount', type=int)
    action = request.form.get('action')

    if amount and amount > 0:
        if action == 'add':
            user.godcoin_balance += amount
            transaction = Transaction(
                user_id=user_id,
                type='admin_add',
                amount=amount,
                description='Admin cộng GodCoin'
            )
        else:
            if user.godcoin_balance >= amount:
                user.godcoin_balance -= amount
                transaction = Transaction(
                    user_id=user_id,
                    type='admin_subtract',
                    amount=-amount,
                    description='Admin trừ GodCoin'
                )
            else:
                flash('Số dư không đủ để trừ!', 'error')
                return redirect(url_for('admin.users'))

        db.session.add(transaction)
        db.session.commit()
        flash(f'Đã điều chỉnh số dư GodCoin cho {user.username}!', 'success')

    return redirect(url_for('admin.users'))

# Categories Management
@admin_bp.route('/categories')
@login_required
@admin_required
def categories():
    categories = Category.query.all()
    return render_template('admin/categories.html', categories=categories)

@admin_bp.route('/categories/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_category():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')

        if Category.query.filter_by(name=name).first():
            flash('Danh mục đã tồn tại!', 'error')
        else:
            category = Category(name=name, description=description)
            db.session.add(category)
            db.session.commit()
            flash('Tạo danh mục thành công!', 'success')
            return redirect(url_for('admin.categories'))

    return render_template('admin/create_category.html')

@admin_bp.route('/categories/<int:category_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_category(category_id):
    category = Category.query.get_or_404(category_id)
    db.session.delete(category)
    db.session.commit()
    flash('Xóa danh mục thành công!', 'success')
    return redirect(url_for('admin.categories'))

# Posts Management
@admin_bp.route('/posts')
@login_required
@admin_required
def posts():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.created_at.desc()).paginate(page=page, per_page=20)
    return render_template('admin/posts.html', posts=posts)

@admin_bp.route('/posts/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_post():
    categories = Category.query.all()

    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        category_id = request.form.get('category_id', type=int)
        is_premium = request.form.get('is_premium') == 'on'
        premium_price = request.form.get('premium_price', 0, type=int)

        post = Post(
            title=title,
            content=content,
            category_id=category_id if category_id else None,
            is_premium=is_premium,
            premium_price=premium_price if is_premium else 0,
            author_id=current_user.id
        )

        # Handle thumbnail upload
        if 'thumbnail' in request.files:
            file = request.files['thumbnail']
            if file.filename:
                uploaded = upload_image_util(file, folder='godweb/posts')
                if uploaded:
                    post.thumbnail = uploaded

        db.session.add(post)
        db.session.commit()
        flash('Tạo bài viết thành công!', 'success')
        return redirect(url_for('admin.posts'))

    return render_template('admin/create_post.html', categories=categories)

@admin_bp.route('/posts/<int:post_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_post(post_id):
    post = Post.query.get_or_404(post_id)
    categories = Category.query.all()

    if request.method == 'POST':
        post.title = request.form.get('title')
        post.content = request.form.get('content')
        post.category_id = request.form.get('category_id', type=int) or None
        post.is_premium = request.form.get('is_premium') == 'on'
        post.premium_price = request.form.get('premium_price', 0, type=int) if post.is_premium else 0

        if 'thumbnail' in request.files:
            file = request.files['thumbnail']
            if file.filename:
                uploaded = upload_image_util(file, folder='godweb/posts')
                if uploaded:
                    post.thumbnail = uploaded

        db.session.commit()
        flash('Cập nhật bài viết thành công!', 'success')
        return redirect(url_for('admin.posts'))

    return render_template('admin/edit_post.html', post=post, categories=categories)

@admin_bp.route('/upload-image', methods=['POST'])
@login_required
@admin_required
def upload_image():
    """API endpoint to upload images from editor (paste or file upload)"""
    from flask import jsonify

    if 'image' not in request.files:
        return jsonify({'success': False, 'error': 'Không có file ảnh'})

    file = request.files['image']

    # For pasted images, file.filename might be empty or 'image.png'
    # We'll handle this in upload_image_util

    try:
        uploaded = upload_image_util(file, folder='godweb/content')
        if uploaded:
            # Check if it's a full URL (Cloudinary) or local filename
            if uploaded.startswith('http://') or uploaded.startswith('https://'):
                url = uploaded
            else:
                # Local file - generate URL
                url = url_for('main.uploaded_file', filename=uploaded, _external=True)
            return jsonify({'success': True, 'url': url})
        else:
            return jsonify({'success': False, 'error': 'Không thể upload ảnh'})
    except Exception as e:
        print(f"Upload error: {e}")
        return jsonify({'success': False, 'error': str(e)})

@admin_bp.route('/posts/<int:post_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()
    flash('Xóa bài viết thành công!', 'success')
    return redirect(url_for('admin.posts'))

# Products Management
@admin_bp.route('/products')
@login_required
@admin_required
def products():
    page = request.args.get('page', 1, type=int)
    products = Product.query.order_by(Product.created_at.desc()).paginate(page=page, per_page=20)
    return render_template('admin/products.html', products=products)

@admin_bp.route('/products/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_product():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        price = request.form.get('price', type=int)

        product = Product(name=name, description=description, price=price)

        if 'image' in request.files:
            file = request.files['image']
            if file.filename:
                uploaded = upload_image_util(file, folder='godweb/products')
                if uploaded:
                    product.image = uploaded

        db.session.add(product)
        db.session.commit()

        # Handle inventory file upload - save as file
        if 'inventory_file' in request.files:
            inventory_file = request.files['inventory_file']
            if inventory_file.filename:
                # Save file with product id
                inv_filename = f"inventory_{product.id}.txt"
                inv_filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], inv_filename)
                inventory_file.save(inv_filepath)

                # Count lines
                with open(inv_filepath, 'r', encoding='utf-8') as f:
                    lines = [line.strip() for line in f.readlines() if line.strip()]
                    product.stock = len(lines)

                product.inventory_file = inv_filename
                db.session.commit()

        flash('Tạo sản phẩm thành công!', 'success')
        return redirect(url_for('admin.products'))

    return render_template('admin/create_product.html')

@admin_bp.route('/products/<int:product_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)

    if request.method == 'POST':
        product.name = request.form.get('name')
        product.description = request.form.get('description')
        product.price = request.form.get('price', type=int)

        if 'image' in request.files:
            file = request.files['image']
            if file.filename:
                uploaded = upload_image_util(file, folder='godweb/products')
                if uploaded:
                    product.image = uploaded

        db.session.commit()
        flash('Cập nhật sản phẩm thành công!', 'success')
        return redirect(url_for('admin.products'))

    return render_template('admin/edit_product.html', product=product)

@admin_bp.route('/products/<int:product_id>/inventory', methods=['GET', 'POST'])
@login_required
@admin_required
def product_inventory(product_id):
    product = Product.query.get_or_404(product_id)

    if request.method == 'POST':
        if 'inventory_file' in request.files:
            inventory_file = request.files['inventory_file']
            if inventory_file.filename:
                # Save file with product id
                inv_filename = f"inventory_{product.id}.txt"
                inv_filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], inv_filename)
                inventory_file.save(inv_filepath)

                # Count lines
                with open(inv_filepath, 'r', encoding='utf-8') as f:
                    lines = [line.strip() for line in f.readlines() if line.strip()]
                    product.stock = len(lines)

                product.inventory_file = inv_filename
                product.sold_count = 0  # Reset sold count when uploading new file
                db.session.commit()
                flash(f'Đã upload file với {len(lines)} tài khoản!', 'success')

    return render_template('admin/product_inventory.html', product=product)

@admin_bp.route('/products/<int:product_id>/view-file')
@login_required
@admin_required
def view_inventory_file(product_id):
    product = Product.query.get_or_404(product_id)

    if not product.inventory_file:
        flash('Sản phẩm chưa có file tài khoản!', 'error')
        return redirect(url_for('admin.product_inventory', product_id=product_id))

    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], product.inventory_file)

    if not os.path.exists(filepath):
        flash('File không tồn tại!', 'error')
        return redirect(url_for('admin.product_inventory', product_id=product_id))

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    return render_template('admin/view_inventory_file.html', product=product, content=content)

@admin_bp.route('/products/<int:product_id>/download-file')
@login_required
@admin_required
def download_inventory_file(product_id):
    from flask import send_file
    product = Product.query.get_or_404(product_id)

    if not product.inventory_file:
        flash('Sản phẩm chưa có file tài khoản!', 'error')
        return redirect(url_for('admin.product_inventory', product_id=product_id))

    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], product.inventory_file)

    if not os.path.exists(filepath):
        flash('File không tồn tại!', 'error')
        return redirect(url_for('admin.product_inventory', product_id=product_id))

    return send_file(filepath, as_attachment=True, download_name=f"{product.name}_inventory.txt")

@admin_bp.route('/products/<int:product_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)

    # Delete inventory file if exists
    if product.inventory_file:
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], product.inventory_file)
        if os.path.exists(filepath):
            os.remove(filepath)

    db.session.delete(product)
    db.session.commit()
    flash('Xóa sản phẩm thành công!', 'success')
    return redirect(url_for('admin.products'))

# Topup Management
@admin_bp.route('/topups')
@login_required
@admin_required
def topups():
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', 'pending')

    query = Topup.query
    if status:
        query = query.filter_by(status=status)

    topups = query.order_by(Topup.created_at.desc()).paginate(page=page, per_page=20)
    return render_template('admin/topups.html', topups=topups, current_status=status)

@admin_bp.route('/topups/<int:topup_id>/approve', methods=['POST'])
@login_required
@admin_required
def approve_topup(topup_id):
    topup = Topup.query.get_or_404(topup_id)

    if topup.status != 'pending':
        flash('Yêu cầu này đã được xử lý!', 'error')
        return redirect(url_for('admin.topups'))

    topup.status = 'approved'
    topup.processed_at = datetime.utcnow()

    user = User.query.get(topup.user_id)
    user.godcoin_balance += topup.godcoin_amount

    transaction = Transaction(
        user_id=topup.user_id,
        type='topup',
        amount=topup.godcoin_amount,
        description=f'Nạp GodCoin qua {topup.method.upper()}'
    )
    db.session.add(transaction)
    db.session.commit()

    flash(f'Đã duyệt nạp {topup.godcoin_amount} GodCoin cho {user.username}!', 'success')
    return redirect(url_for('admin.topups'))

@admin_bp.route('/topups/<int:topup_id>/reject', methods=['POST'])
@login_required
@admin_required
def reject_topup(topup_id):
    topup = Topup.query.get_or_404(topup_id)

    if topup.status != 'pending':
        flash('Yêu cầu này đã được xử lý!', 'error')
        return redirect(url_for('admin.topups'))

    topup.status = 'rejected'
    topup.processed_at = datetime.utcnow()
    db.session.commit()

    flash('Đã từ chối yêu cầu nạp tiền!', 'success')
    return redirect(url_for('admin.topups'))

# Transactions Log
@admin_bp.route('/transactions')
@login_required
@admin_required
def transactions():
    page = request.args.get('page', 1, type=int)
    transactions = Transaction.query.order_by(Transaction.created_at.desc()).paginate(page=page, per_page=50)
    return render_template('admin/transactions.html', transactions=transactions)

# Orders
@admin_bp.route('/orders')
@login_required
@admin_required
def orders():
    page = request.args.get('page', 1, type=int)
    orders = Order.query.order_by(Order.created_at.desc()).paginate(page=page, per_page=20)
    return render_template('admin/orders.html', orders=orders)
