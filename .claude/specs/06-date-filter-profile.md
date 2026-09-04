# Spec: Date Filter for Profile Page

## Overview
The `/profile` page currently shows only account details (name, email, member-since). This step adds the user's expense history to the profile page — a list of their expenses pulled from the `expenses` table — along with a date-range filter (from/to) so the user can narrow the list down to a specific period. This is the first step that surfaces expense data anywhere in the UI, ahead of the add/edit/delete CRUD steps (Steps 7–9) which remain stubs.

## Depends on
- Step 01 — Database setup (`expenses` table, `get_db()`)
- Step 03 — Login and Logout (session-based auth)
- Step 04 — Profile Page Design (`/profile` route, `profile.html`, auth-gating pattern)

## Routes
- `GET /profile` — modify existing route to also fetch and display the current user's expenses — logged-in only (already exists)
  - Accepts optional query params `from` and `to` (ISO `YYYY-MM-DD`) to filter the expense list by date range
  - `GET /profile?from=2026-08-01&to=2026-08-31` — filtered view, same route/template

No new routes; the existing `/profile` route is extended.

## Database changes
No schema changes. The existing `expenses` table (id, user_id, amount, category, date, description, created_at) already has everything needed.

New DB helpers must be added to `database/db.py`:
- `get_expenses_by_user(user_id, date_from=None, date_to=None)` — runs a parameterised `SELECT` against `expenses` for the given `user_id`, ordered by `date DESC`. When `date_from`/`date_to` are provided, adds `AND date >= ?` / `AND date <= ?` conditions (still parameterised, never string-built). Returns all matching rows.

## Templates
- **Modify:** `templates/profile.html`
  - Add a date-range filter form (`from` and `to` date inputs, submit via `GET` so the filter is bookmarkable/shareable) above the expense list
  - Add an expense list section below the existing account-details card: each row shows date, category, description, amount
  - If no expenses match the filter (or the user has none), show an empty-state message instead of an empty table
  - Uses existing CSS variables/design tokens — no new hardcoded colors

## Files to change
- `app.py` — extend `profile()`: read optional `from`/`to` query params, call `get_expenses_by_user()`, pass `expenses` (and the current filter values, to repopulate the form) into the template context
- `database/db.py` — add `get_expenses_by_user()` helper

## Files to create
No new files.

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only — never use f-strings in SQL, including for the optional date-range conditions
- Passwords hashed with werkzeug
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Use `url_for()` for the filter form's action and any internal links
- Only ever query expenses belonging to `session['user_id']` — never trust a user-supplied `user_id`
- If `from` is after `to`, ignore the filter and show all expenses rather than erroring (flash a gentle message)
- Invalid or malformed date query params must not crash the route — fall back to showing unfiltered expenses

## Definition of done
- [ ] Visiting `/profile` while logged in shows the existing account details plus a list of the signed-in user's expenses, most recent first
- [ ] Submitting the date-range filter form re-renders `/profile` with only expenses whose `date` falls within `[from, to]`
- [ ] Clearing the filter (or visiting `/profile` with no query params) shows all of the user's expenses again
- [ ] A user with no expenses in the selected range sees an empty-state message, not a broken/empty table
- [ ] Visiting `/profile?from=...&to=...` while logged out still redirects to `/login`, same as before
- [ ] One user's expenses never appear on another user's profile page, even by guessing/editing query params
- [ ] Malformed date values in `from`/`to` (e.g. non-date text) don't crash the page
- [ ] Profile page visually matches the rest of the site (fonts, spacing, CSS variables) with no hardcoded hex colors
