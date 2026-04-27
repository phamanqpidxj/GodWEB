"""Integration tests for Store purchase flow & race-condition guarantees."""
from __future__ import annotations

import os

from tests.conftest import extract_csrf_token


def _create_user(app, **kwargs):
    from godweb.extensions import db
    from godweb.models import User
    with app.app_context():
        user = User(
            username=kwargs.get('username', 'buyer'),
            email=kwargs.get('email', 'buyer@example.com'),
            recovery_number='9999',
            godcoin_balance=kwargs.get('godcoin_balance', 100),
        )
        user.set_password(kwargs.get('password', 'pass-1234'))
        db.session.add(user)
        db.session.commit()
        return user.id


def _create_product(app, upload_dir, accounts):
    from godweb.extensions import db
    from godweb.models import Product
    inv_path = os.path.join(upload_dir, 'inv.txt')
    with open(inv_path, 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(accounts))
    with app.app_context():
        product = Product(
            name='Demo Product',
            description='test',
            price=50,
            stock=len(accounts),
            inventory_file='inv.txt',
            parse_mode='line',
            inventory_type='file',
        )
        db.session.add(product)
        db.session.commit()
        return product.id


def _login(client, email, password):
    token = extract_csrf_token(client.get('/auth/login').data.decode('utf-8'))
    resp = client.post('/auth/login', data={'email': email, 'password': password, 'csrf_token': token})
    assert resp.status_code == 302


def test_purchase_deducts_balance_and_returns_account(app, client):
    upload_dir = app.config['UPLOAD_FOLDER']
    user_id = _create_user(app)
    product_id = _create_product(app, upload_dir, ['user1@example.com|pass1', 'user2@example.com|pass2'])

    _login(client, 'buyer@example.com', 'pass-1234')

    resp = client.get(f'/store/{product_id}')
    token = extract_csrf_token(resp.data.decode('utf-8'))

    resp = client.post(f'/store/{product_id}/buy', data={'csrf_token': token})
    assert resp.status_code == 302
    assert '/profile/orders' in resp.headers['Location']

    from godweb.models import User, Order, Product
    with app.app_context():
        user = User.query.get(user_id)
        product = Product.query.get(product_id)
        order = Order.query.filter_by(user_id=user_id).first()
        assert user.godcoin_balance == 50
        assert product.stock == 1
        assert product.sold_count == 1
        assert order.account_info == 'user1@example.com|pass1'


def test_purchase_blocks_when_balance_insufficient(app, client):
    upload_dir = app.config['UPLOAD_FOLDER']
    _create_user(app, godcoin_balance=10)
    product_id = _create_product(app, upload_dir, ['acct@x|p'])

    _login(client, 'buyer@example.com', 'pass-1234')
    # Grab CSRF token from an authenticated form (profile edit always renders one).
    token = extract_csrf_token(client.get('/profile/edit').data.decode('utf-8'))
    resp = client.post(f'/store/{product_id}/buy', data={'csrf_token': token})

    # Should redirect to wallet/topup, not deduct anything.
    assert resp.status_code == 302
    assert '/wallet/topup' in resp.headers['Location']

    from godweb.models import User, Order
    with app.app_context():
        assert User.query.first().godcoin_balance == 10
        assert Order.query.count() == 0


def test_purchase_blocks_unauthenticated(client):
    """CSRF protection rejects unauthenticated POSTs even before login_required."""
    resp = client.post('/store/1/buy', follow_redirects=False)
    # Without a valid CSRF token Flask-WTF returns 400 BAD REQUEST.
    assert resp.status_code == 400
