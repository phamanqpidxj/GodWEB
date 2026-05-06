"""Smoke tests: app boots and the auth gate behaves correctly."""


def test_anonymous_homepage_redirects_to_login(client):
    """Anonymous users are redirected to the login page."""
    response = client.get('/', follow_redirects=False)
    assert response.status_code == 302
    assert '/auth/login' in response.headers['Location']


def test_anonymous_blog_redirects_to_login(client):
    response = client.get('/blog/', follow_redirects=False)
    assert response.status_code == 302
    assert '/auth/login' in response.headers['Location']


def test_anonymous_store_redirects_to_login(client):
    response = client.get('/store/', follow_redirects=False)
    assert response.status_code == 302
    assert '/auth/login' in response.headers['Location']


def test_login_page_is_public(client):
    response = client.get('/auth/login')
    assert response.status_code == 200
    assert b'GodWeb' in response.data


def test_register_page_is_public(client):
    response = client.get('/auth/register')
    assert response.status_code == 200


def test_security_headers_present(client):
    response = client.get('/auth/login')
    for header in (
        'X-Frame-Options',
        'X-Content-Type-Options',
        'Referrer-Policy',
        'Content-Security-Policy',
    ):
        assert header in response.headers, f'Missing header {header}'
