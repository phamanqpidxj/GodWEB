import os
from flask import Flask, url_for
from extensions import db, login_manager

def create_app():
    app = Flask(__name__)

    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'godweb-secret-key-change-in-production')

    # Database configuration
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        # Fix for Heroku postgres URL (postgres:// -> postgresql://)
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    else:
        # Use SQLite for local development
        basedir = os.path.abspath(os.path.dirname(__file__))
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'instance', 'godweb.db')

    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')

    # Create upload folder if not exists
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Vui lòng đăng nhập để tiếp tục.'

    # Add custom Jinja2 filter for image URLs
    @app.template_filter('image_url')
    def image_url_filter(image_path):
        """Convert image path to full URL (supports both Cloudinary and local files)"""
        if not image_path:
            return ''
        # If it's already a full URL (Cloudinary), return as-is
        if image_path.startswith('http://') or image_path.startswith('https://'):
            return image_path
        # Otherwise, it's a local filename - use the upload route
        return url_for('main.uploaded_file', filename=image_path)

    # Import and register blueprints
    from routes.main import main_bp
    from routes.auth import auth_bp
    from routes.blog import blog_bp
    from routes.store import store_bp
    from routes.wallet import wallet_bp
    from routes.profile import profile_bp
    from routes.admin import admin_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(blog_bp, url_prefix='/blog')
    app.register_blueprint(store_bp, url_prefix='/store')
    app.register_blueprint(wallet_bp, url_prefix='/wallet')
    app.register_blueprint(profile_bp, url_prefix='/profile')
    app.register_blueprint(admin_bp, url_prefix='/admin')

    # Create database tables
    with app.app_context():
        db.create_all()

        from models import User
        # Create default admin if not exists
        admin = User.query.filter_by(email='admin@godweb.com').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@godweb.com',
                role='admin',
                godcoin_balance=10000
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()

    return app

# Create app instance for gunicorn (Heroku)
app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
