# Spec: Profile Page Design

## Overview
Replace the placeholder `/profile` route ("Profile page — coming in Step 4") with a real, logged-in-only profile page that shows the signed-in user's account details (name, email, member-since date). This is the first user-scoped page in Spendly and establishes the pattern (auth-gating a route, reading the current user from the session) that later expense-management steps will reuse.

## Depends on
- Step 01 — Database setup (`users` table, `get_db()`)
- Step 02 — Registration (`create_user()`)
- Step 03 — Login and Logout (session-based auth, `session['user_id']`, session-aware nav)

## Routes
- `GET /profile` — render the current user's profile — logged-in only (already exists as stub, upgrade it)

Unauthenticated requests to `GET /profile` must redirect to `GET /login` (flash a message such as "Please sign in to continue.") rather than erroring.

## Database changes
No database changes. The existing `users` table (id, name, email, password_hash, created_at) already stores everything the profile page displays.

A new DB helper must be added to `database/db.py`:
- `get_user_by_id(user_id)` — runs a parameterised `SELECT` against `users` for the given id and returns the row (or `None` if not found), for use when rendering the profile page.

## Templates
- **Create:** `templates/profile.html`
  - Extends `base.html`
  - Displays the user's name, email, and formatted "member since" date (derived from `created_at`)
  - Uses existing CSS variables/design tokens from `static/css/style.css` — no new hardcoded colors
- **Modify:** None required beyond what Step 03 already made session-aware (nav already links to `/profile`).

## Files to change
- `app.py` — replace the `profile()` placeholder: require `session['user_id']` (redirect to `login` with a flash message if absent), fetch the user with `get_user_by_id()`, and render `profile.html`
- `database/db.py` — add `get_user_by_id()` helper

## Files to create
- `templates/profile.html`

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only — never use f-strings in SQL
- Passwords hashed with `werkzeug` — the profile page must never display or expose `password_hash`
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Use `url_for()` for every internal link — never hardcode URLs
- Store only `user_id` in the session — continue reading it from `session.get('user_id')`
- If `session['user_id']` is missing, redirect to `login()` with a flash message; do not render `profile.html` for anonymous visitors
- If the `user_id` in the session refers to a user that no longer exists, clear the session and redirect to `login()`

## Definition of done
- [ ] Visiting `/profile` while logged out redirects to `/login` with a flash message, no error
- [ ] Visiting `/profile` while logged in renders the profile page showing the correct name, email, and member-since date for the signed-in user
- [ ] The profile page's `password_hash` is never present in the rendered HTML
- [ ] The nav's "Profile" link (added in Step 03) correctly opens this page
- [ ] Profile page visually matches the rest of the site (fonts, spacing, CSS variables) with no hardcoded hex colors
