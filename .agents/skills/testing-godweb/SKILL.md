---
name: testing-godweb
description: End-to-end testing patterns for the GodWEB Flask app — admin login, admin destructive routes (delete product/post/topup), capturing HTTP redirects, and the admin-seed password gotcha. Use when verifying any admin-area UI change or testing routes that redirect after POST.
---

# Testing GodWEB end-to-end

GodWEB is a small Flask app (gunicorn + SQLAlchemy + SQLite locally, Postgres in prod). Most non-trivial test scenarios involve the admin area, which is gated by `@login_required` + `@admin_required` decorators on every route under `/admin/*`.

## Dev server

```bash
cd /home/ubuntu/repos/GodWEB
ADMIN_EMAIL='admin@test.local' \
ADMIN_PASSWORD='admin-test-1234' \
nohup .venv/bin/gunicorn godweb.app:app -b 127.0.0.1:5000 -w 1 --timeout 60 \
  > /tmp/dev_server.log 2>&1 &
```

The app auto-seeds an admin user from `ADMIN_EMAIL`/`ADMIN_PASSWORD` env vars (see `godweb/app.py:507-525`).

## Gotcha — admin password only set on first creation

The seed logic is guarded by `if not existing_admin:` — once `admin@test.local` exists in `instance/godweb.db`, **changing `ADMIN_PASSWORD` between runs is a no-op**. Login will silently fail with the new password.

If you hit this (Playwright lands on `/auth/login?next=/admin/...` after submitting credentials), reset the password directly:

```python
from godweb.app import create_app
from godweb.extensions import db
from godweb.models import User
app = create_app()
with app.app_context():
    u = User.query.filter_by(email='admin@test.local').first()
    u.set_password('admin-test-1234')
    db.session.commit()
```

Do NOT delete and recreate the admin row — that can break FK references from existing test data.

## E2E pattern: Playwright over CDP, visible browser

The VM exposes Chrome's CDP at `http://localhost:29229`. Connecting via Playwright reuses the same browser instance shown on the desktop, so the recording captures every click while the script can also intercept network and run JS evaluations.

```python
from playwright.async_api import async_playwright

async with async_playwright() as p:
    browser = await p.chromium.connect_over_cdp('http://127.0.0.1:29229')
    ctx = browser.contexts[0]
    page = ctx.pages[0] if ctx.pages else await ctx.new_page()
```

## Capturing HTTP status on routes that redirect

Flask admin destructive routes (`POST /admin/products/<id>/delete`, `/admin/posts/<id>/delete`, topup approve/reject) return `302` on success and `500` on failure, then redirect to a list view. From inside the page JS context you can only observe the *final* page (200), not the original POST status.

Use `page.on('response')` to capture the POST response before the redirect:

```python
delete_responses = []

def on_response(resp):
    if resp.request.method == 'POST' and resp.url.endswith('/delete'):
        delete_responses.append({'url': resp.url, 'status': resp.status})

page.on('response', on_response)
```

Then assert `resp['status'] == 302` after the click.

## Auto-accepting native confirm() dialogs

Destructive buttons in templates use vanilla `onclick="return confirm('Xác nhận xóa?')"`. Playwright must register a dialog handler **before** the click:

```python
page.on('dialog', lambda d: asyncio.create_task(d.accept()))
```

## Adversarial assertion design for destructive routes

For any delete-with-cascade or bulk-mutation route:

1. **Always include an unrelated row in the setup** that the operation should NOT touch. Asserting the row survives catches over-delete regressions a simple before/after count would miss.
2. **Match flash text exactly** (not just "contains 'success'"). The route has two code paths with slightly different messages (`Xóa sản phẩm thành công!` vs `Xóa sản phẩm thành công! Đã xóa kèm N đơn hàng liên quan.`). A regression that flashes the same text for both would only be caught by exact match.
3. **Capture the POST status from network events**, not from `page.url`. After redirect both 200 (error page) and 302 (success) land on the same final URL.

## Selectors for the admin products list

`godweb/templates/admin/products.html` renders one `<tr>` per product. The delete form is:

```html
<form method="POST" action="{{ url_for('admin.delete_product', product_id=product.id) }}" style="display: inline;">
  <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
  <button type="submit" class="btn btn-danger btn-sm" onclick="return confirm('Xác nhận xóa?')">
```

Reliable Playwright selector for a specific product's delete button:

```python
f"tr:has-text('{product_name}') form[action$='/admin/products/{product_id}/delete'] button[type=submit]"
```

## Recording maximization

Before starting `recording_start`, maximize Chrome:

```bash
sudo apt-get install -y wmctrl >/dev/null 2>&1
wmctrl -r :ACTIVE: -b add,maximized_vert,maximized_horz
```

Do NOT use `xdotool key super+Up` — many WMs tile to half-screen with that shortcut.

## Devin secrets needed

None — local-only credentials (`admin@test.local` / `admin-test-1234`) are fine for testing. Do not check real admin credentials into env config; they should remain session-scoped.
