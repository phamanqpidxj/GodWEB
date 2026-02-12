from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from godweb.models import Post, Category, Comment, PostPurchase, Transaction
from godweb.extensions import db
from sqlalchemy import func

blog_bp = Blueprint('blog', __name__)

@blog_bp.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    category_id = request.args.get('category', type=int)
    search = request.args.get('search', '')

    query = Post.query

    if category_id:
        query = query.filter_by(category_id=category_id)

    # Case-insensitive search using LOWER()
    if search:
        search_lower = search.lower()
        query = query.filter(
            func.lower(Post.title).contains(search_lower) |
            func.lower(Post.content).contains(search_lower)
        )

    # Sort: Admin Pin (2) > User Pin (1) > Newest (by created_at)
    posts = query.order_by(Post.pin_priority.desc(), Post.created_at.desc()).paginate(page=page, per_page=9)
    categories = Category.query.all()

    return render_template('blog/index.html', posts=posts, categories=categories,
                          current_category=category_id, search=search)

@blog_bp.route('/<int:post_id>/pin', methods=['POST'])
@login_required
def pin_post(post_id):
    post = Post.query.get_or_404(post_id)

    # Check permission
    if current_user.is_admin():
        # Admin can pin any post with highest priority
        if post.pin_priority == 2:
            # Unpin
            post.pin_priority = 0
            post.pinned_by = None
            flash('Đã bỏ ghim bài viết!', 'success')
        else:
            # Pin as admin
            post.pin_priority = 2
            post.pinned_by = 'admin'
            flash('Đã ghim bài viết (Admin)!', 'success')
    else:
        # User can only pin their own posts
        if post.author_id != current_user.id:
            flash('Bạn không có quyền ghim bài viết này!', 'error')
            return redirect(url_for('blog.detail', post_id=post_id))

        # User cannot unpin admin's pin
        if post.pinned_by == 'admin':
            flash('Bạn không thể bỏ ghim bài viết do Admin ghim!', 'error')
            return redirect(url_for('blog.detail', post_id=post_id))

        if post.pin_priority == 1:
            # Unpin
            post.pin_priority = 0
            post.pinned_by = None
            flash('Đã bỏ ghim bài viết!', 'success')
        else:
            # Pin as user
            post.pin_priority = 1
            post.pinned_by = 'user'
            flash('Đã ghim bài viết!', 'success')

    db.session.commit()
    return redirect(url_for('blog.detail', post_id=post_id))

    return render_template('blog/index.html', posts=posts, categories=categories,
                          current_category=category_id, search=search)

@blog_bp.route('/<int:post_id>')
def detail(post_id):
    post = Post.query.get_or_404(post_id)
    post.views += 1
    db.session.commit()

    # Check if user has purchased premium content
    has_access = False
    if not post.is_premium:
        has_access = True
    elif current_user.is_authenticated:
        if current_user.is_admin():
            has_access = True
        elif PostPurchase.query.filter_by(user_id=current_user.id, post_id=post_id).first():
            has_access = True

    comments = Comment.query.filter_by(post_id=post_id).order_by(Comment.created_at.desc()).all()

    return render_template('blog/detail.html', post=post, has_access=has_access, comments=comments)

@blog_bp.route('/<int:post_id>/purchase', methods=['POST'])
@login_required
def purchase(post_id):
    post = Post.query.get_or_404(post_id)

    if not post.is_premium:
        return redirect(url_for('blog.detail', post_id=post_id))

    # Check if already purchased
    if PostPurchase.query.filter_by(user_id=current_user.id, post_id=post_id).first():
        flash('Bạn đã mua bài viết này rồi!', 'info')
        return redirect(url_for('blog.detail', post_id=post_id))

    # Check balance
    if current_user.godcoin_balance < post.premium_price:
        flash('Số dư GodCoin không đủ! Vui lòng nạp thêm.', 'error')
        return redirect(url_for('wallet.topup'))

    # Deduct balance and create purchase
    current_user.godcoin_balance -= post.premium_price

    purchase = PostPurchase(user_id=current_user.id, post_id=post_id, price=post.premium_price)
    db.session.add(purchase)

    transaction = Transaction(
        user_id=current_user.id,
        type='purchase',
        amount=-post.premium_price,
        description=f'Mua bài viết: {post.title}'
    )
    db.session.add(transaction)

    db.session.commit()

    flash('Mua bài viết thành công!', 'success')
    return redirect(url_for('blog.detail', post_id=post_id))

@blog_bp.route('/<int:post_id>/comment', methods=['POST'])
@login_required
def add_comment(post_id):
    post = Post.query.get_or_404(post_id)
    content = request.form.get('content')

    if content:
        comment = Comment(content=content, author_id=current_user.id, post_id=post_id)
        db.session.add(comment)
        db.session.commit()
        flash('Bình luận đã được thêm!', 'success')

    return redirect(url_for('blog.detail', post_id=post_id))
