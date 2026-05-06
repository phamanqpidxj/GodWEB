import logging
import os
import secrets
import time
from datetime import timedelta
from urllib.parse import urlparse
from flask import Flask, url_for, request, abort, redirect, session, flash
from flask_wtf.csrf import CSRFError
from sqlalchemy import inspect, text, create_engine
from flask_login import current_user
from werkzeug.middleware.proxy_fix import ProxyFix
from godweb.extensions import db, login_manager, csrf

def _init_sentry(is_prod_like: bool) -> None:
    """Wire Sentry up if SENTRY_DSN is set.

    Heroku's Sentry add-on auto-injects ``SENTRY_DSN``. We only call
    ``sentry_sdk.init`` when the DSN is present so local dev runs and the
    test-suite never talk to Sentry. Errors come with Flask request and
    SQLAlchemy query context, plus the Heroku release tag when available.
    """
    dsn = os.environ.get('SENTRY_DSN')
    if not dsn:
        if is_prod_like:
            logger.info('SENTRY_DSN not set; Sentry error reporting disabled.')
        return

    try:
        import sentry_sdk
        from sentry_sdk.integrations.flask import FlaskIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
    except ImportError:
        logger.warning('sentry-sdk is not installed; SENTRY_DSN ignored.')
        return

    environment = (
        os.environ.get('SENTRY_ENVIRONMENT')
        or ('production' if is_prod_like else 'development')
    )
    release = (
        os.environ.get('SENTRY_RELEASE')
        or os.environ.get('HEROKU_SLUG_COMMIT')
        or os.environ.get('HEROKU_RELEASE_VERSION')
    )

    def _sample_rate(env_name: str, default: float) -> float:
        raw = os.environ.get(env_name)
        if raw is None:
            return default
        try:
            value = float(raw)
        except ValueError:
            return default
        return max(0.0, min(1.0, value))

    sentry_sdk.init(
        dsn=dsn,
        environment=environment,
        release=release,
        integrations=[FlaskIntegration(), SqlalchemyIntegration()],
        traces_sample_rate=_sample_rate('SENTRY_TRACES_SAMPLE_RATE', 0.1),
        profiles_sample_rate=_sample_rate('SENTRY_PROFILES_SAMPLE_RATE', 0.0),
        send_default_pii=False,
    )
    logger.info(
        'Sentry initialized (environment=%s release=%s).',
        environment, release or '<unset>',
    )


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


def _load_or_create_persistent_secret_db(database_url):
    """Persist SECRET_KEY in the application database.

    Heroku's filesystem (incl. ``/tmp``) is wiped on every dyno restart, which
    rotates any file-based fallback key roughly every 24h and silently logs
    every user out. Storing the key in Postgres makes it stable for the
    lifetime of the database, so 'Remember me' cookies actually survive.
    """
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    engine = create_engine(database_url, pool_pre_ping=True)
    try:
        with engine.begin() as conn:
            conn.execute(text(
                "CREATE TABLE IF NOT EXISTS app_secrets ("
                "  key VARCHAR(64) PRIMARY KEY,"
                "  value TEXT NOT NULL,"
                "  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
                ")"
            ))
            row = conn.execute(
                text("SELECT value FROM app_secrets WHERE key = :k"),
                {'k': 'session_secret'},
            ).fetchone()
            if row and row[0]:
                return row[0]
            new_secret = secrets.token_urlsafe(48)
            try:
                conn.execute(
                    text("INSERT INTO app_secrets (key, value) VALUES (:k, :v)"),
                    {'k': 'session_secret', 'v': new_secret},
                )
                return new_secret
            except Exception:
                # Lost a race with another worker; re-read the row they inserted.
                row = conn.execute(
                    text("SELECT value FROM app_secrets WHERE key = :k"),
                    {'k': 'session_secret'},
                ).fetchone()
                if row and row[0]:
                    return row[0]
                return new_secret
    finally:
        engine.dispose()


# Endpoints reachable without authentication. Everything else requires
# a logged-in user (see ``require_login_globally`` below).
PUBLIC_ENDPOINTS = frozenset({
    'static',
    'auth.login',
    'auth.register',
    'auth.forgot_password',
})


def create_app():
    app = Flask(__name__)

    is_prod_like = os.environ.get('FLASK_ENV') == 'production' or bool(os.environ.get('DYNO'))

    _init_sentry(is_prod_like)

    # SECRET_KEY: prefer env, otherwise fall back to a key persisted on disk so
    # all gunicorn workers in this dyno share the same value (sessions survive
    # the lifetime of the dyno even if the operator hasn't set the env var).
    secret_key = os.environ.get('SECRET_KEY')
    if not secret_key:
        if is_prod_like:
            db_url_for_secret = os.environ.get('DATABASE_URL')
            if db_url_for_secret:
                try:
                    secret_key = _load_or_create_persistent_secret_db(db_url_for_secret)
                    logger.info(
                        'SECRET_KEY loaded from app_secrets table; sessions survive dyno restarts.'
                    )
                except Exception as exc:
                    logger.warning('DB-backed SECRET_KEY load failed (%s); falling back to filesystem.', exc)
            if not secret_key:
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
    # 'Remember me' must keep the user signed in for at least a week even
    # if the dyno restarts. Both the session cookie and the remember-me
    # cookie need a 7-day lifetime; the login route flips session.permanent
    # so the session cookie obeys PERMANENT_SESSION_LIFETIME.
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
    app.config['REMEMBER_COOKIE_DURATION'] = timedelta(days=7)
    app.config['REMEMBER_COOKIE_REFRESH_EACH_REQUEST'] = True
    app.config['SESSION_REFRESH_EACH_REQUEST'] = True
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
    login_manager.login_message_category = 'info'
    login_manager.refresh_view = 'auth.login'

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
    def require_login_globally():
        """Force authentication site-wide except for the auth blueprint and assets.

        Anonymous visitors hitting any other endpoint are redirected to the
        login page; the original URL is preserved via the ``next`` parameter
        so they land back where they started after signing in.
        """
        endpoint = request.endpoint
        if endpoint is None:
            return None
        if current_user.is_authenticated:
            return None
        if endpoint in PUBLIC_ENDPOINTS:
            return None
        # Allow blueprint-scoped static endpoints too (e.g. 'admin.static').
        if endpoint.endswith('.static'):
            return None
        if request.method in ('POST', 'PUT', 'PATCH', 'DELETE'):
            # 401 instead of a redirect makes the gate obvious to API callers.
            abort(401)
        # Pass the original path+query as a relative URL so the login route's
        # open-redirect guard (which rejects absolute URLs) honors it.
        next_target = request.full_path if request.query_string else request.path
        if next_target.endswith('?'):
            next_target = next_target[:-1]
        return redirect(url_for('auth.login', next=next_target))

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

    @app.errorhandler(CSRFError)
    def handle_csrf_error(error):
        """Recover gracefully from CSRF failures (e.g. stale session cookies).

        After a SECRET_KEY rotation the browser's old session cookie can no
        longer be deserialized, so the form's CSRF token has nothing to
        validate against and Flask-WTF returns a bare ``400`` page. Wipe the
        stale session, flash a friendly message and bounce back to the login
        form so a fresh session + token are issued automatically.
        """
        session.clear()
        flash('Phiên làm việc đã hết hạn, vui lòng thử lại.', 'warning')
        next_target = request.args.get('next') or request.form.get('next')
        if next_target and next_target.startswith('/') and not next_target.startswith('//'):
            return redirect(url_for('auth.login', next=next_target))
        return redirect(url_for('auth.login'))

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
