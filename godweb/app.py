import logging
import os
import secrets
import time
from urllib.parse import urlparse
from flask import Flask, url_for, request, abort
from sqlalchemy import inspect, text
from flask_login import current_user
from werkzeug.middleware.proxy_fix import ProxyFix
from godweb.extensions import db, login_manager, csrf

DEFAULT_DEV_SECRET_KEY = 'godweb-dev-secret-key-do-not-use-in-production'
FALLBACK_SECRET_FILE = os.environ.get(
    'GODWEB_FALLBACK_SECRET_FILE', '/tmp/godweb-fallback-secret'
)

logger = logging.getLogger(__name__)


def _load_or_create_persistent_secret(path: str) -> str:
    """Atomically share a random SECRET_KEY across gunicorn workers.

    Multiple workers in the same dyno call ``create_app`` independently; if each
    generated its own random key, sessions issued by worker A would not verify
    on worker B and the user would appear logged out on every other request.
    Persisting the first-generated key to a file solves this for the lifetime
    of the dyno.
    """
    for _ in range(20):
        try:
            fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            try:
                os.write(fd, secrets.token_urlsafe(48).encode())
            finally:
                os.close(fd)
        except FileExistsError:
            pass
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            if content:
                return content
        except FileNotFoundError:
            pass
        time.sleep(0.05)
    # Last resort: in-process random key. Better than crashing the dyno.
    return secrets.token_urlsafe(48)


def create_app():
    app = Flask(__name__)

    is_prod_like = os.environ.get('FLASK_ENV') == 'production' or bool(os.environ.get('DYNO'))

    # SECRET_KEY: prefer env, otherwise fall back to a key persisted on disk so
    # all gunicorn workers in this dyno share the same value (sessions survive
    # the lifetime of the dyno even if the operator hasn't set the env var).
    secret_key = os.environ.get('SECRET_KEY')
    if not secret_key:
        if is_prod_like:
            secret_key = _load_or_create_persistent_secret(FALLBACK_SECRET_FILE)
            logger.warning(
                'SECRET_KEY env var is not set in a production-like environment; '
                'using a persisted random key from %s. Set SECRET_KEY in your '
                'platform config (e.g. `heroku config:set SECRET_KEY=...`) so '
                'sessions survive dyno restarts.', FALLBACK_SECRET_FILE,
            )
        else:
            secret_key = DEFAULT_DEV_SECRET_KEY
    app.config['SECRET_KEY'] = secret_key

    # Honor the X-Forwarded-* headers set by Heroku's router so Flask sees the
    # client IP, https scheme, and original host. Required for url_for(_external=True)
    # and for cookie/Secure semantics behind the proxy.
    if is_prod_like:
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

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

    app.config['WTF_CSRF_TIME_LIMIT'] = None
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['SESSION_COOKIE_SECURE'] = is_prod_like
    app.config['REMEMBER_COOKIE_HTTPONLY'] = True
    app.config['REMEMBER_COOKIE_SAMESITE'] = 'Lax'
    app.config['REMEMBER_COOKIE_SECURE'] = is_prod_like
    app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10 MB

    # Create upload folder if not exists
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    # Initialize extensions
    db.init_app(app)
    csrf.init_app(app)
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

    @app.context_processor
    def inject_notifications():
        if not current_user.is_authenticated:
            return {'navbar_notifications': [], 'unread_notification_count': 0}

        from godweb.models import Notification, NotificationRead

        notifications = Notification.query.order_by(Notification.created_at.desc()).limit(12).all()
        if not notifications:
            return {'navbar_notifications': [], 'unread_notification_count': 0}

        read_ids = {
            row.notification_id
            for row in NotificationRead.query.filter_by(user_id=current_user.id).all()
        }

        navbar_notifications = []
        unread_count = 0
        for item in notifications:
            is_read = item.id in read_ids
            if not is_read:
                unread_count += 1
            navbar_notifications.append({
                'id': item.id,
                'content': item.content,
                'created_at': item.created_at,
                'is_read': is_read
            })

        return {
            'navbar_notifications': navbar_notifications,
            'unread_notification_count': unread_count
        }

    @app.before_request
    def enforce_same_origin_for_mutations():
        if request.method not in ('POST', 'PUT', 'PATCH', 'DELETE'):
            return

        source = request.headers.get('Origin') or request.headers.get('Referer')
        if not source:
            return

        parsed = urlparse(source)
        if not parsed.netloc or parsed.netloc != request.host:
            abort(403)

    @app.after_request
    def add_security_headers(response):
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=()'
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdnjs.cloudflare.com; "
            "font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com data:; "
            "img-src 'self' https: data:; "
            "connect-src 'self'; "
            "frame-ancestors 'self';"
        )
        return response

    # Import and register blueprints
    from godweb.routes.main import main_bp
    from godweb.routes.auth import auth_bp
    from godweb.routes.blog import blog_bp
    from godweb.routes.store import store_bp
    from godweb.routes.wallet import wallet_bp
    from godweb.routes.profile import profile_bp
    from godweb.routes.admin import admin_bp

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

        def safe_add_column(sql):
            try:
                db.session.execute(text(sql))
                db.session.commit()
            except Exception as exc:
                db.session.rollback()
                # Gunicorn multi-worker boot can race on ALTER TABLE; ignore duplicate-column errors.
                message = str(exc).lower()
                if 'duplicate column name' not in message and 'already exists' not in message:
                    raise

        inspector = inspect(db.engine)
        if 'users' in inspector.get_table_names():
            columns = [column['name'] for column in inspector.get_columns('users')]
            if 'recovery_number' not in columns:
                safe_add_column('ALTER TABLE users ADD COLUMN recovery_number VARCHAR(20)')

        if 'products' in inspector.get_table_names():
            product_columns = [column['name'] for column in inspector.get_columns('products')]
            if 'parse_mode' not in product_columns:
                safe_add_column("ALTER TABLE products ADD COLUMN parse_mode VARCHAR(20) DEFAULT 'line'")
            if 'inventory_type' not in product_columns:
                safe_add_column("ALTER TABLE products ADD COLUMN inventory_type VARCHAR(20) DEFAULT 'file'")
            if 'inventory_folder_path' not in product_columns:
                safe_add_column("ALTER TABLE products ADD COLUMN inventory_folder_path VARCHAR(255)")
            if 'inventory_data' not in product_columns:
                safe_add_column("ALTER TABLE products ADD COLUMN inventory_data TEXT")
            db.session.execute(text("UPDATE products SET parse_mode = 'line' WHERE parse_mode IS NULL"))
            db.session.execute(text("UPDATE products SET inventory_type = 'file' WHERE inventory_type IS NULL"))
            db.session.commit()

        # Rescue any legacy filesystem inventory into the database BEFORE Heroku
        # ephemeral storage wipes it on the next dyno restart. Idempotent.
        try:
            from godweb.models import Product, ProductInventoryAccount
            from godweb.utils import list_inventory_folder_files, read_inventory_folder_account
            upload_folder = app.config.get('UPLOAD_FOLDER')
            if upload_folder and os.path.isdir(upload_folder):
                for product in Product.query.all():
                    inv_type = getattr(product, 'inventory_type', 'file') or 'file'
                    if inv_type == 'folder':
                        existing_count = ProductInventoryAccount.query.filter_by(product_id=product.id).count()
                        if existing_count == 0 and getattr(product, 'inventory_folder_path', None):
                            folder_path = os.path.join(upload_folder, product.inventory_folder_path)
                            if os.path.isdir(folder_path):
                                for fname in list_inventory_folder_files(folder_path):
                                    try:
                                        content = read_inventory_folder_account(folder_path, fname)
                                    except OSError:
                                        continue
                                    db.session.add(ProductInventoryAccount(
                                        product_id=product.id,
                                        filename=fname,
                                        content=content,
                                    ))
                                product.stock = ProductInventoryAccount.query.filter_by(product_id=product.id).count()
                    else:
                        if not getattr(product, 'inventory_data', None) and product.inventory_file:
                            filepath = os.path.join(upload_folder, product.inventory_file)
                            if os.path.isfile(filepath):
                                try:
                                    with open(filepath, 'r', encoding='utf-8', errors='replace') as fh:
                                        product.inventory_data = fh.read()
                                except OSError:
                                    pass
                db.session.commit()
        except Exception as exc:
            db.session.rollback()
            app.logger.warning('Inventory rescue migration skipped: %s', exc)

        from godweb.models import User
        # Bootstrap an admin only when explicit env vars are supplied. This
        # avoids shipping a known admin@godweb.com / admin123 account.
        admin_email = os.environ.get('ADMIN_EMAIL')
        admin_password = os.environ.get('ADMIN_PASSWORD')
        if admin_email and admin_password:
            existing_admin = User.query.filter_by(email=admin_email).first()
            if not existing_admin:
                admin = User(
                    username=os.environ.get('ADMIN_USERNAME', 'admin'),
                    email=admin_email,
                    role='admin',
                    godcoin_balance=int(os.environ.get('ADMIN_INITIAL_GODCOIN', '0') or 0),
                )
                admin.set_password(admin_password)
                db.session.add(admin)
                db.session.commit()

    return app

# Create app instance for gunicorn (Heroku)
app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
