# Celestial Path overhaul — test plan

PR: https://github.com/phamanqpidxj/GodWEB/pull/29
Target: local Flask app at `http://localhost:5050` (auth-gated; logged in as `reviewer@example.com / Password1!` before recording starts).

Seeded data:
- 1 user `daoist_le` (reviewer)
- 1 free post (Mortal)
- 1 premium post (Immortal, `is_premium=True`, `premium_price=199`)
- 1 store product
- 1 admin-style notification (so the silk ticker has content to shimmer over)

## Primary flow (1 continuous recording)

Each step lists **expected** vs **fail** so a broken implementation is visibly different.

### 1. Home page in dark realm (default)
- **Action:** open `http://localhost:5050/` post-login.
- **Assert (Mortal vs Immortal cards):** the blog grid renders at least one card with class `xx-mortal-card` AND one with class `xx-immortal-card` (verified via DOM annotation) — expected: 1 of each visible.
- **Assert (Immortal aura):** the premium card "Phù Chú Cấm — Bát Quái Trận Đồ Tuyệt Mật" shows a **conic-gradient ring** around its border (gold → purple → jade → crimson). The Mortal card next to it shows **no** rotating ring — only soft drop shadow and brushstroke top/bottom rules.
- **Assert (Talisman badge):** the premium card's "Premium" badge has the paper-charm look (gold gradient, red stamp seal on the left, asymmetric corner radius). On the Mortal card there is no premium badge at all.
- **Assert (dark-text safety net):** every visible heading and body paragraph on the page has a measurable luminance ≥ that of `#888` (silver-white / pale-blue), not near-black. I will sample with `getComputedStyle` on at least one `h3.card-title` and one `p.card-text` and read the value into the recording.
- **Fail signal:** Yin-Yang ring absent OR premium aura missing OR any sampled `card-title` reports `rgb(0,…)` / `rgb(28, 41, 51)` (the old `--dark-color`).

### 2. Yin-Yang theme toggle (desktop)
- **Action:** click the round button in the navbar (`#toggleSiteTheme`).
- **Assert (rotation):** the `.theme-yinyang-ring` element's computed `transform` changes from `matrix(1, 0, 0, 1, …)` (≈ `rotate(0deg)`) to `matrix(-1, …, -1, …)` (≈ `rotate(180deg)`).
- **Assert (icon swap):** the moon SVG was visible before, the sun SVG is visible after (verified by `display` computed style — the inactive one is `none`).
- **Assert (root class):** `document.documentElement.classList` flips from `theme-dark` to `theme-light`.
- **Assert (persistence):** `localStorage.getItem('siteTheme')` reads `'light'` after the click; reload the page and the realm stays light. Reload again and toggle back — value should now be `'dark'`.
- **Fail signal:** ring doesn't rotate, OR both icons visible at once, OR `localStorage.siteTheme` is missing/unchanged, OR class doesn't flip.

### 3. Heavenly Realm visual sanity
- **Assert:** after toggling to light mode, the page background turns light, headings render dark (`#1e293b`), and the Immortal card switches to porcelain/gold aura (the conic gradient still rotates but uses gold→purple→jade→crimson palette).
- **Fail signal:** the page stays dark, OR the Immortal card's border disappears entirely in light mode.

### 4. Silk shimmer on announcement ticker
- **Action:** wait ~6s on the homepage with the ticker visible. Verify the `.site-ticker::after` sheen sweeps across the bar.
- **Assert:** during a recorded clip of ~7s I should be able to see at least one diagonal shimmer pass cross the ticker. Because pseudo-elements aren't directly observable, I will also verify the rule exists with `getComputedStyle(siteTicker, '::after').animationName === 'xxSilkShimmer'` and the animation is not `paused`.
- **Fail signal:** no shimmer pass during the clip AND the computed `animation-name` on `::after` is `none`.

### 5. Hover ascend + mist on Immortal card (dark realm)
- **Action:** toggle back to dark, scroll to the premium post, hover the card.
- **Assert:** the card's `transform` includes `translateY(-6px)` (or comparable), the conic ring's animation duration shortens (visible as faster rotation), and `.xx-immortal-mist` element exists and becomes opaque.
- **Fail signal:** no lift, OR no `.xx-immortal-mist` element in the DOM, OR mist opacity stays 0.

## Out of scope / regression check (label "Regression")
- `pytest -q` on the PR branch — already green in CI (1 passed). I will NOT re-run unit tests in the recording.

## Pass/fail summary
Test passes iff **all** assertions in steps 1–5 hold AND CI is green. Anything ambiguous will be reported as `untested` rather than glossed over.
