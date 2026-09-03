# Spec: Login and Logout

## Overview
Implement session-based authentication so registered users can sign in and out of Spendly. This step upgrades the existing stub `GET /login` route into a full `GET`/`POST` route that verifies credentials against the `users` table and starts a Flask session, and turns the `GET /logout` stub into a route that clears the session. Every page that currently shows generic "Sign in" / "Get started" nav links should reflect whether a user is logged in. This is the gate that all future user-scoped features (profile, expenses) depend on.

## Depends on
- Step 01 — Database setup (`users` table, `get_db()`)
- Step 02 — Registration (`create_user()`, users can already be created with hashed passwords)

## Routes
- `GET /login` — render login form — public (already exists as stub, upgrade it)
- `POST /login` — verify email/password, start session, redirect to landing page — public
- `GET /logout` — clear session, redirect to landing page — logged-in (already exists as stub returning placeholder text, replace it)

## Database changes
No database changes. The existing `users` table (id, name, email, password_hash, created_at) already stores everything needed to authenticate.

A new DB helper must be added to `database/db.py`:
- `get_user_by_email(email)` — runs a parameterised `SELECT` against `users` for the given email and returns the row (or `None` if not found), for use during login.

## Templates
- **Modify:** `templates/login.html`
  - Change the form to post to `url_for('login')` instead of the hardcoded `"/login"` string
  - Add a block to display a flashed error message (e.g. "Invalid email or password") the same way `register.html` does
  - Keep all existing visual design
- **Modify:** `templates/base.html`
  - Nav links become conditional: when a user is logged in, show "Sign out" (`url_for('logout')`) and a link to `/profile`; when logged out, keep the existing "Sign in" / "Get started" links

## Files to change
- `app.py` — upgrade `login()` to handle `GET` and `POST`, verify credentials with `werkzeug.security.check_password_hash`, and set `session['user_id']`; replace the `logout()` placeholder to clear the session and redirect
- `database/db.py` — add `get_user_by_email()` helper
- `templates/login.html` — wire up form action and flash message display
- `templates/base.html` — make nav links session-aware

## Files to create
None.

## New dependencies
No new dependencies. Uses Flask's built-in `session`, `flash`, `redirect`, `url_for`, and `werkzeug.security.check_password_hash` (already installed).

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only — never use f-strings in SQL
- Passwords hashed with `werkzeug` — verify with `check_password_hash`, never compare plaintext
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Use `url_for()` for every internal link — never hardcode URLs
- Store only `user_id` in the session, never the password or password hash
- On successful login, `flash` a success message and `redirect` to the landing page
- On failed login (unknown email or wrong password), flash a single generic "Invalid email or password" error — do not reveal whether the email exists — and re-render the form without redirecting
- `logout()` must clear the session (`session.clear()` or `session.pop('user_id', ...)`) even if no user is logged in, and redirect to the landing page
- Use `abort(405)` if an unsupported HTTP method reaches `/login`

## Definition of done
- [ ] `GET /login` renders the login form without errors
- [ ] Submitting valid credentials logs the user in and redirects to the landing page
- [ ] Submitting an unknown email re-renders the form with "Invalid email or password", no session created
- [ ] Submitting a known email with the wrong password re-renders the form with "Invalid email or password", no session created
- [ ] After logging in, the nav bar shows "Sign out" instead of "Sign in" / "Get started"
- [ ] Visiting `/logout` while logged in clears the session and redirects to the landing page, and the nav reverts to "Sign in" / "Get started"
- [ ] Visiting `/logout` while already logged out does not error and redirects to the landing page
