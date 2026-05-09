"""Tests for the new admin features:

1. /admin/api/pending-topups-count JSON endpoint
2. Search in admin posts
3. Auto-cleanup of old orders
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta

from tests.conftest import extract_csrf_token


def _create_admin(app, email='admin@example.com', password='admin-123'):
    from godweb.extensions import db
    from godweb.models import User
    with app.app_context():
        user = User(
            username='admin',
            email=email,
            recovery_number='0000',
            role='admin',
            godcoin_balance=0,
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return user.id


def _create_user(app, email='user@example.com', password='user-1234'):
    from godweb.extensions import db
    from godweb.models import User
    with app.app_context():
        user = User(
            username='testuser',
            email=email,
            recovery_number='1111',
            godcoin_balance=0,
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return user.id


def _login(client, email, password):
    token = extract_csrf_token(client.get('/auth/login').data.decode())
    resp = client.post('/auth/login', data={
        'email': email,
        'password': password,
        'csrf_token': token,
    })
    assert resp.status_code == 302


# ── pending-topups-count endpoint ──────────────────────────────────────

def test_pending_topups_count_returns_zero_initially(app, client):
    _create_admin(app)
    _login(client, 'admin@example.com', 'admin-123')

    resp = client.get('/admin/api/pending-topups-count')
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data['count'] == 0


def test_pending_topups_count_reflects_pending_requests(app, client):
    admin_id = _create_admin(app)
    user_id = _create_user(app)
    _login(client, 'admin@example.com', 'admin-123')

    from godweb.extensions import db
    from godweb.models import Topup
    with app.app_context():
        db.session.add(Topup(user_id=user_id, amount=50000, godcoin_amount=50,
                             method='momo', status='pending'))
        db.session.add(Topup(user_id=user_id, amount=20000, godcoin_amount=20,
                             method='bank', status='approved'))
        db.session.commit()

    resp = client.get('/admin/api/pending-topups-count')
    data = json.loads(resp.data)
    assert data['count'] == 1


def test_pending_topups_count_requires_admin(app, client):
    _create_user(app)
    _login(client, 'user@example.com', 'user-1234')

    resp = client.get('/admin/api/pending-topups-count', follow_redirects=False)
    assert resp.status_code == 302


# ── admin posts search ─────────────────────────────────────────────────

def test_admin_posts_search_filters_by_title(app, client):
    admin_id = _create_admin(app)
    _login(client, 'admin@example.com', 'admin-123')

    from godweb.extensions import db
    from godweb.models import Post
    with app.app_context():
        db.session.add(Post(title='Hello World', content='body', author_id=admin_id))
        db.session.add(Post(title='Python Tips', content='body', author_id=admin_id))
        db.session.commit()

    resp = client.get('/admin/posts?type=free&search=Hello')
    html = resp.data.decode()
    assert 'Hello World' in html
    assert 'Python Tips' not in html


# ── old order auto-cleanup ─────────────────────────────────────────────

def test_old_orders_are_pruned(app):
    from godweb.extensions import db
    from godweb.models import Order, Product

    user_id = _create_user(app)

    with app.app_context():
        product = Product(
            name='Demo', description='d', price=10,
            stock=0, inventory_file='x', inventory_data='',
            parse_mode='line', inventory_type='file',
        )
        db.session.add(product)
        db.session.commit()
        pid = product.id

        old_order = Order(
            user_id=user_id, product_id=pid,
            account_info='old', price=10,
            created_at=datetime.utcnow() - timedelta(days=31),
        )
        new_order = Order(
            user_id=user_id, product_id=pid,
            account_info='new', price=10,
            created_at=datetime.utcnow(),
        )
        db.session.add_all([old_order, new_order])
        db.session.commit()
        assert Order.query.count() == 2

    from godweb.app import ORDER_RETENTION_DAYS
    with app.app_context():
        cutoff = datetime.utcnow() - timedelta(days=ORDER_RETENTION_DAYS)
        Order.query.filter(Order.created_at < cutoff).delete(synchronize_session=False)
        db.session.commit()
        assert Order.query.count() == 1
        remaining = Order.query.first()
        assert remaining.account_info == 'new'


def test_old_orders_pruned_by_first_request_hook(app, client):
    """The before_request hook must clean up on the very first request after
    process start, even though the in-memory throttle has not been seeded yet.
    A previous bug initialized the throttle to ``0.0`` which, combined with
    ``time.monotonic()`` (also small at process start), caused cleanup to be
    skipped for the first ORDER_CLEANUP_INTERVAL_SECONDS of uptime.
    """
    from godweb.extensions import db
    from godweb.models import Order, Product

    user_id = _create_user(app)

    with app.app_context():
        product = Product(
            name='Demo2', description='d', price=10,
            stock=0, inventory_file='x', inventory_data='',
            parse_mode='line', inventory_type='file',
        )
        db.session.add(product)
        db.session.commit()
        pid = product.id

        db.session.add(Order(
            user_id=user_id, product_id=pid,
            account_info='ancient', price=10,
            created_at=datetime.utcnow() - timedelta(days=45),
        ))
        db.session.add(Order(
            user_id=user_id, product_id=pid,
            account_info='fresh', price=10,
            created_at=datetime.utcnow(),
        ))
        db.session.commit()
        assert Order.query.count() == 2

    # Any request triggers @app.before_request → cleanup_old_orders_periodically.
    client.get('/auth/login')

    with app.app_context():
        remaining = Order.query.all()
        assert len(remaining) == 1
        assert remaining[0].account_info == 'fresh'
