# Spec: Add Expense

## Overview
The `/expenses/add` route is currently a stub that returns the plain text "Add expense — coming in Step 7". This step implements the first write operation for expense data: a form that lets a signed-in user record a new expense (amount, category, date, description) which is inserted into the `expenses` table. This is the first of the three expense-CRUD steps (add, edit, delete) and establishes the pattern — auth-gated form route, server-side validation, parameterised insert — that Steps 8 and 9 will reuse.

## Depends on
- Step 01 (Database Setup) — `expenses` table and `get_db()` must exist.
- Step 03 (Login and Logout) — session-based auth used to identify the current user.
- Step 06 (Date Filter for Profile Page) — profile page already renders the expense list this feature adds to.

## Routes
- `GET /expenses/add` — render the add-expense form — logged-in only
- `POST /expenses/add` — validate input and insert a new expense row for the signed-in user, then redirect to `/profile` — logged-in only

## Database changes
No database changes. The `expenses` table (`database/db.py`) already has the required columns: `user_id`, `amount`, `category`, `date`, `description`, `created_at`. This step adds a new `create_expense(user_id, amount, category, date, description)` function to `database/db.py` that performs a parameterised `INSERT`, following the pattern of `create_user`.

## Templates
- **Create:** `templates/add_expense.html` — form with fields for amount, category (select, using the existing `CATEGORY_ACCENTS` keys in `app.py`), date, and description; extends `base.html`
- **Modify:** None required. `templates/profile.html` already lists expenses and will pick up new rows automatically on next load.

## Files to change
- `app.py` — replace the `add_expense` stub with `GET`/`POST` handling: auth gate, form validation, call `create_expense`, flash + redirect
- `database/db.py` — add `create_expense(user_id, amount, category, date, description)`

## Files to create
- `templates/add_expense.html`

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only
- Passwords hashed with werkzeug (not applicable to this feature, but preserve existing hashing elsewhere)
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Auth-gate both `GET` and `POST` the same way `/profile` does (redirect to `/login` with a flash message if `session.get("user_id")` is missing or the user no longer exists)
- Validate on the server: amount must be a positive number, category must be one of the known `CATEGORY_ACCENTS` keys, date must be a valid ISO date (`datetime.date.fromisoformat`), description is optional
- On validation failure, re-render `add_expense.html` with a flash message and the submitted values preserved (do not lose user input)
- On success, flash a success message and redirect to `/profile`

## Definition of done
- [ ] Visiting `/expenses/add` while logged out redirects to `/login` with a flash message
- [ ] Visiting `/expenses/add` while logged in shows a form with amount, category, date, and description fields
- [ ] Submitting the form with valid data creates a new row in `expenses` for the current user and redirects to `/profile`
- [ ] The new expense appears in the profile page's expense list and totals after redirect
- [ ] Submitting a negative or non-numeric amount shows a validation error and does not insert a row
- [ ] Submitting an invalid/unknown category shows a validation error and does not insert a row
- [ ] Submitting an invalid date shows a validation error and does not insert a row
- [ ] Submitting with description left blank still succeeds (description is optional)
- [ ] Submitted values are preserved in the form after a validation error
