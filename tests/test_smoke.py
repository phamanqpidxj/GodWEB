"""Smoke tests: app boots and public pages render."""


def test_homepage_renders(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b'GodWeb' in response.data


def test_blog_index_renders(client):
    response = client.get('/blog/')
    assert response.status_code == 200


def test_store_index_renders(client):
    response = client.get('/store/')
    assert response.status_code == 200


def test_security_headers_present(client):
    response = client.get('/')
    for header in (
        'X-Frame-Options',
        'X-Content-Type-Options',
        'Referrer-Policy',
        'Content-Security-Policy',
    ):
        assert header in response.headers, f'Missing header {header}'
