from flask import Blueprint, render_template, send_from_directory, current_app, jsonify, abort
from flask_login import login_required, current_user
from godweb.extensions import db
from godweb.models import Post, Product, Category, Notification, NotificationRead
import os

main_bp = Blueprint('main', __name__)

@main_bp.route('/uploads/<filename>')
def uploaded_file(filename):
    """Serve uploaded files"""
    normalized = filename.lower()
    if normalized.endswith('.txt') or normalized.startswith('inventory_'):
        abort(404)

    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)

@main_bp.route('/')
def home():
    # Sort: Admin Pin > User Pin > Newest
    featured_posts = Post.query.order_by(Post.pin_priority.desc(), Post.created_at.desc()).limit(6).all()
    featured_products = Product.query.filter(Product.stock > 0).order_by(Product.created_at.desc()).limit(6).all()
    return render_template('home.html', posts=featured_posts, products=featured_products)

@main_bp.route('/about')
def about():
    return render_template('about.html')

@main_bp.route('/contact')
def contact():
    return render_template('contact.html')

@main_bp.route('/terms')
def terms():
    return render_template('terms.html')


@main_bp.route('/notifications/<int:notification_id>/read', methods=['POST'])
@login_required
def read_notification(notification_id):
    notification = Notification.query.get_or_404(notification_id)

    already_read = NotificationRead.query.filter_by(
        user_id=current_user.id,
        notification_id=notification.id
    ).first()

    if not already_read:
        db.session.add(NotificationRead(user_id=current_user.id, notification_id=notification.id))
        db.session.commit()

    unread_count = db.session.query(Notification.id).outerjoin(
        NotificationRead,
        db.and_(
            NotificationRead.notification_id == Notification.id,
            NotificationRead.user_id == current_user.id
        )
    ).filter(NotificationRead.id.is_(None)).count()

    return jsonify({'success': True, 'unread_count': unread_count})
