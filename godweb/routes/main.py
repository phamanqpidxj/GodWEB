from flask import Blueprint, render_template, send_from_directory, current_app
from godweb.models import Post, Product, Category
import os

main_bp = Blueprint('main', __name__)

@main_bp.route('/uploads/<filename>')
def uploaded_file(filename):
    """Serve uploaded files"""
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
