"""Tests for the DB-backed inventory storage that survives dyno restarts."""
from __future__ import annotations

import io
import os
import zipfile

from tests.conftest import extract_csrf_token


def _login(client, email, password):
    token = extract_csrf_token(client.get('/auth/login').data.decode('utf-8'))
    resp = client.post('/auth/login', data={'email': email, 'password': password, 'csrf_token': token})
    assert resp.status_code == 302


def _create_buyer(app, balance=200):
    from godweb.extensions import db
    from godweb.models import User
    with app.app_context():
        user = User(
            username='buyer',
            email='buyer@example.com',
            recovery_number='9999',
            godcoin_balance=balance,
        )
        user.set_password('pass-1234')
        db.session.add(user)
        db.session.commit()


def test_buy_succeeds_when_inventory_file_missing_on_disk(app, client, tmp_path):
    """The whole point of the fix: even if /uploads is wiped, DB content serves the buyer."""
    from godweb.extensions import db
    from godweb.models import Product, User, Order

    _create_buyer(app)
    with app.app_context():
        product = Product(
            name='Heroku Survivor',
            description='inventory persisted in DB',
            price=50,
            stock=2,
            # Filename is metadata only; the actual data is in inventory_data.
            inventory_file='inventory_999.txt',
            inventory_data='acct-A@example.com|passA\nacct-B@example.com|passB',
            parse_mode='line',
            inventory_type='file',
        )
        db.session.add(product)
        db.session.commit()
        product_id = product.id

    # Simulate Heroku ephemeral wipe: nothing exists under UPLOAD_FOLDER.
    upload_dir = app.config['UPLOAD_FOLDER']
    assert not os.path.exists(os.path.join(upload_dir, 'inventory_999.txt'))

    _login(client, 'buyer@example.com', 'pass-1234')
    detail = client.get(f'/store/{product_id}')
    token = extract_csrf_token(detail.data.decode('utf-8'))
    resp = client.post(f'/store/{product_id}/buy', data={'csrf_token': token})
    assert resp.status_code == 302
    assert '/profile/orders' in resp.headers['Location']

    with app.app_context():
        product = Product.query.get(product_id)
        order = Order.query.filter_by(product_id=product_id).first()
        assert order is not None
        assert order.account_info == 'acct-A@example.com|passA'
        assert product.stock == 1
        # Remaining inventory still in DB after consumption.
        assert 'acct-B@example.com|passB' in (product.inventory_data or '')
        assert User.query.filter_by(email='buyer@example.com').first().godcoin_balance == 150


def test_buy_succeeds_for_folder_inventory_when_disk_wiped(app, client):
    """Folder-mode inventory (zip uploads) is now stored as DB rows."""
    from godweb.extensions import db
    from godweb.models import Product, ProductInventoryAccount, Order

    _create_buyer(app)
    with app.app_context():
        product = Product(
            name='Zip Product',
            description='folder inventory in DB',
            price=50,
            stock=3,
            inventory_type='folder',
            parse_mode='line',
        )
        db.session.add(product)
        db.session.flush()
        for fname, content in [
            ('a01.txt', 'acct-A1@example.com|passA1'),
            ('a02.txt', 'acct-A2@example.com|passA2'),
            ('a03.txt', 'acct-A3@example.com|passA3'),
        ]:
            db.session.add(ProductInventoryAccount(
                product_id=product.id,
                filename=fname,
                content=content,
            ))
        db.session.commit()
        product_id = product.id

    _login(client, 'buyer@example.com', 'pass-1234')
    detail = client.get(f'/store/{product_id}')
    token = extract_csrf_token(detail.data.decode('utf-8'))
    resp = client.post(f'/store/{product_id}/buy', data={'csrf_token': token})
    assert resp.status_code == 302

    with app.app_context():
        order = Order.query.filter_by(product_id=product_id).first()
        assert order.account_info == 'acct-A1@example.com|passA1'
        remaining = ProductInventoryAccount.query.filter_by(product_id=product_id).count()
        assert remaining == 2


def test_admin_upload_persists_txt_inventory_to_db(app, client):
    """Uploading a .txt via admin must populate Product.inventory_data."""
    from godweb.extensions import db
    from godweb.models import User, Product

    with app.app_context():
        admin = User(username='adm', email='adm@example.com', role='admin', recovery_number='0000')
        admin.set_password('pass-1234')
        db.session.add(admin)
        product = Product(name='X', description='y', price=10, stock=0, inventory_type='file', parse_mode='line')
        db.session.add(product)
        db.session.commit()
        product_id = product.id

    _login(client, 'adm@example.com', 'pass-1234')
    page = client.get(f'/admin/products/{product_id}/inventory')
    token = extract_csrf_token(page.data.decode('utf-8'))

    payload = {
        'csrf_token': token,
        'parse_mode': 'line',
        'inventory_file': (io.BytesIO(b'acct1@x|p1\nacct2@x|p2\nacct3@x|p3\n'), 'accounts.txt'),
    }
    resp = client.post(
        f'/admin/products/{product_id}/inventory',
        data=payload,
        content_type='multipart/form-data',
    )
    assert resp.status_code in (200, 302)

    with app.app_context():
        product = Product.query.get(product_id)
        assert product.inventory_type == 'file'
        assert product.inventory_data is not None
        assert 'acct1@x|p1' in product.inventory_data
        assert product.stock == 3


def test_admin_upload_persists_zip_inventory_to_db(app, client):
    """Uploading a .zip via admin must populate ProductInventoryAccount rows."""
    from godweb.extensions import db
    from godweb.models import User, Product, ProductInventoryAccount

    with app.app_context():
        admin = User(username='adm', email='adm@example.com', role='admin', recovery_number='0000')
        admin.set_password('pass-1234')
        db.session.add(admin)
        product = Product(name='Y', description='y', price=10, stock=0, inventory_type='file', parse_mode='line')
        db.session.add(product)
        db.session.commit()
        product_id = product.id

    # Build an in-memory zip with a couple of .txt files.
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w') as zf:
        zf.writestr('alpha.txt', 'acct-alpha@x|pa')
        zf.writestr('beta.txt', 'acct-beta@x|pb')
    buf.seek(0)

    _login(client, 'adm@example.com', 'pass-1234')
    token = extract_csrf_token(client.get(f'/admin/products/{product_id}/inventory').data.decode('utf-8'))
    resp = client.post(
        f'/admin/products/{product_id}/inventory',
        data={'csrf_token': token, 'inventory_file': (buf, 'inv.zip')},
        content_type='multipart/form-data',
    )
    assert resp.status_code in (200, 302)

    with app.app_context():
        product = Product.query.get(product_id)
        assert product.inventory_type == 'folder'
        rows = (
            ProductInventoryAccount.query
            .filter_by(product_id=product_id)
            .order_by(ProductInventoryAccount.filename)
            .all()
        )
        assert [r.filename for r in rows] == ['alpha.txt', 'beta.txt']
        assert rows[0].content == 'acct-alpha@x|pa'
        assert product.stock == 2
