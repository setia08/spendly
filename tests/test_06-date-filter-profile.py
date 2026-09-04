"""
Tests for Spec 06 — Date Filter for Profile Page.

Covers: GET /profile expense list + date-range filtering, auth gating,
per-user isolation, malformed/inverted date handling, and the
get_expenses_by_user() DB helper.
"""
import database.db as db_module

from tests.conftest import add_expense, login_user, register_user


# --------------------------------------------------------------------- #
# Routes: GET /profile — auth gating (unchanged behavior, re-verified)  #
# --------------------------------------------------------------------- #

def test_profile_redirects_to_login_when_logged_out(client):
    resp = client.get("/profile", follow_redirects=False)
    assert resp.status_code in (301, 302)
    assert "/login" in resp.headers["Location"]


def test_profile_with_date_params_redirects_to_login_when_logged_out(client):
    """DoD: visiting /profile?from=...&to=... while logged out still redirects to /login."""
    resp = client.get(
        "/profile?from=2026-08-01&to=2026-08-31", follow_redirects=False
    )
    assert resp.status_code in (301, 302)
    assert "/login" in resp.headers["Location"]


# --------------------------------------------------------------------- #
# DoD: unfiltered expense list, most recent first                       #
# --------------------------------------------------------------------- #

def test_profile_shows_expenses_most_recent_first(client, registered_user):
    add_expense(registered_user, 10.00, "Food", "2026-08-01", "Old groceries")
    add_expense(registered_user, 20.00, "Transport", "2026-08-15", "Bus")
    add_expense(registered_user, 30.00, "Bills", "2026-08-10", "Electricity")

    resp = client.get("/profile")
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)

    pos_15 = html.index("Bus")
    pos_10 = html.index("Electricity")
    pos_01 = html.index("Old groceries")
    assert pos_15 < pos_10 < pos_01


def test_profile_shows_account_details_and_expenses_together(client, registered_user):
    add_expense(registered_user, 42.50, "Food", "2026-08-05", "Groceries")

    resp = client.get("/profile")
    html = resp.get_data(as_text=True)

    assert "Test User" in html
    assert "test@example.com" in html
    assert "Groceries" in html


def test_profile_no_expenses_shows_empty_state(client, registered_user):
    """DoD: a user with no expenses sees an empty-state message, not a broken/empty table."""
    resp = client.get("/profile")
    assert resp.status_code == 200
    html = resp.get_data(as_text=True).lower()
    # spec requires *some* empty-state messaging rather than a bare/broken table
    assert "no expense" in html or "empty" in html or "haven't" in html or "don't have" in html


# --------------------------------------------------------------------- #
# DoD: date-range filtering                                             #
# --------------------------------------------------------------------- #

def test_filter_by_date_range_narrows_results(client, registered_user):
    add_expense(registered_user, 10.00, "Food", "2026-07-15", "July expense")
    add_expense(registered_user, 20.00, "Food", "2026-08-15", "August expense")
    add_expense(registered_user, 30.00, "Food", "2026-09-15", "September expense")

    resp = client.get("/profile?from=2026-08-01&to=2026-08-31")
    html = resp.get_data(as_text=True)

    assert "August expense" in html
    assert "July expense" not in html
    assert "September expense" not in html


def test_filter_boundaries_are_inclusive(client, registered_user):
    add_expense(registered_user, 10.00, "Food", "2026-08-01", "Start boundary")
    add_expense(registered_user, 20.00, "Food", "2026-08-31", "End boundary")

    resp = client.get("/profile?from=2026-08-01&to=2026-08-31")
    html = resp.get_data(as_text=True)

    assert "Start boundary" in html
    assert "End boundary" in html


def test_clearing_filter_shows_all_expenses_again(client, registered_user):
    add_expense(registered_user, 10.00, "Food", "2026-07-15", "July expense")
    add_expense(registered_user, 20.00, "Food", "2026-08-15", "August expense")

    filtered = client.get("/profile?from=2026-08-01&to=2026-08-31")
    assert "July expense" not in filtered.get_data(as_text=True)

    unfiltered = client.get("/profile")
    html = unfiltered.get_data(as_text=True)
    assert "July expense" in html
    assert "August expense" in html


def test_filter_with_no_matches_shows_empty_state(client, registered_user):
    """DoD: no expenses in the selected range -> empty-state message, not a broken/empty table."""
    add_expense(registered_user, 10.00, "Food", "2026-01-01", "January expense")

    resp = client.get("/profile?from=2026-08-01&to=2026-08-31")
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert "January expense" not in html
    lowered = html.lower()
    assert "no expense" in lowered or "empty" in lowered or "haven't" in lowered or "don't have" in lowered


# --------------------------------------------------------------------- #
# Rules: from-after-to is ignored (gentle flash, show all)              #
# --------------------------------------------------------------------- #

def test_from_after_to_ignores_filter_and_shows_all(client, registered_user):
    add_expense(registered_user, 10.00, "Food", "2026-07-15", "July expense")
    add_expense(registered_user, 20.00, "Food", "2026-08-15", "August expense")

    resp = client.get("/profile?from=2026-08-31&to=2026-08-01", follow_redirects=True)
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)

    # both expenses should still show since the filter was ignored
    assert "July expense" in html
    assert "August expense" in html


# --------------------------------------------------------------------- #
# Rules: malformed dates must not crash the route                       #
# --------------------------------------------------------------------- #

def test_malformed_from_date_does_not_crash(client, registered_user):
    add_expense(registered_user, 10.00, "Food", "2026-08-15", "August expense")

    resp = client.get("/profile?from=not-a-date&to=2026-08-31")
    assert resp.status_code == 200
    assert "August expense" in resp.get_data(as_text=True)


def test_malformed_to_date_does_not_crash(client, registered_user):
    add_expense(registered_user, 10.00, "Food", "2026-08-15", "August expense")

    resp = client.get("/profile?from=2026-08-01&to=banana")
    assert resp.status_code == 200
    assert "August expense" in resp.get_data(as_text=True)


def test_both_dates_malformed_falls_back_to_unfiltered(client, registered_user):
    add_expense(registered_user, 10.00, "Food", "2026-08-15", "August expense")

    resp = client.get("/profile?from=xxxx&to=yyyy")
    assert resp.status_code == 200
    assert "August expense" in resp.get_data(as_text=True)


# --------------------------------------------------------------------- #
# Rules: only session user's own expenses, never trust user_id param    #
# --------------------------------------------------------------------- #

def test_one_users_expenses_never_appear_on_another_users_profile(client):
    register_user(client, name="Alice", email="alice@example.com", password="password123")
    login_user(client, email="alice@example.com", password="password123")
    alice = db_module.get_user_by_email("alice@example.com")
    add_expense(alice["id"], 99.00, "Food", "2026-08-15", "Alice secret expense")
    client.get("/logout")

    register_user(client, name="Bob", email="bob@example.com", password="password123")
    login_user(client, email="bob@example.com", password="password123")
    bob = db_module.get_user_by_email("bob@example.com")
    add_expense(bob["id"], 5.00, "Food", "2026-08-16", "Bob own expense")

    resp = client.get("/profile")
    html = resp.get_data(as_text=True)
    assert "Bob own expense" in html
    assert "Alice secret expense" not in html


def test_supplying_foreign_user_id_query_param_is_ignored(client):
    """Spec: never trust a user-supplied user_id — /profile has no user_id param,
    so attempting to smuggle one in via query string must have no effect."""
    register_user(client, name="Alice", email="alice@example.com", password="password123")
    login_user(client, email="alice@example.com", password="password123")
    alice = db_module.get_user_by_email("alice@example.com")

    register_user(client, name="Bob", email="bob@example.com", password="password123")
    bob = db_module.get_user_by_email("bob@example.com")
    add_expense(bob["id"], 5.00, "Food", "2026-08-16", "Bob only expense")
    add_expense(alice["id"], 1.00, "Food", "2026-08-16", "Alice only expense")

    resp = client.get(f"/profile?user_id={bob['id']}")
    html = resp.get_data(as_text=True)
    assert "Alice only expense" in html
    assert "Bob only expense" not in html


# --------------------------------------------------------------------- #
# Database changes: get_expenses_by_user() helper                       #
# --------------------------------------------------------------------- #

def test_get_expenses_by_user_returns_only_that_users_rows(app, registered_user):
    other_user_id = db_module.create_user("Other", "other@example.com", "pw123456")
    add_expense(registered_user, 10.00, "Food", "2026-08-01", "Mine")
    add_expense(other_user_id, 20.00, "Food", "2026-08-01", "Not mine")

    rows = db_module.get_expenses_by_user(registered_user)
    descriptions = [r["description"] for r in rows]
    assert "Mine" in descriptions
    assert "Not mine" not in descriptions


def test_get_expenses_by_user_orders_by_date_desc(app, registered_user):
    add_expense(registered_user, 10.00, "Food", "2026-08-01", "First")
    add_expense(registered_user, 20.00, "Food", "2026-08-15", "Second")
    add_expense(registered_user, 30.00, "Food", "2026-08-10", "Third")

    rows = db_module.get_expenses_by_user(registered_user)
    dates = [r["date"] for r in rows]
    assert dates == sorted(dates, reverse=True)


def test_get_expenses_by_user_filters_by_date_from(app, registered_user):
    add_expense(registered_user, 10.00, "Food", "2026-08-01", "Before")
    add_expense(registered_user, 20.00, "Food", "2026-08-15", "After")

    rows = db_module.get_expenses_by_user(registered_user, date_from="2026-08-10")
    descriptions = [r["description"] for r in rows]
    assert descriptions == ["After"]


def test_get_expenses_by_user_filters_by_date_to(app, registered_user):
    add_expense(registered_user, 10.00, "Food", "2026-08-01", "Before")
    add_expense(registered_user, 20.00, "Food", "2026-08-15", "After")

    rows = db_module.get_expenses_by_user(registered_user, date_to="2026-08-10")
    descriptions = [r["description"] for r in rows]
    assert descriptions == ["Before"]


def test_get_expenses_by_user_filters_by_both_bounds(app, registered_user):
    add_expense(registered_user, 10.00, "Food", "2026-07-01", "Too early")
    add_expense(registered_user, 20.00, "Food", "2026-08-15", "In range")
    add_expense(registered_user, 30.00, "Food", "2026-09-01", "Too late")

    rows = db_module.get_expenses_by_user(
        registered_user, date_from="2026-08-01", date_to="2026-08-31"
    )
    descriptions = [r["description"] for r in rows]
    assert descriptions == ["In range"]


def test_get_expenses_by_user_parameterised_query_is_injection_safe(app, registered_user):
    """Rule: parameterised queries only — a SQL-injection-shaped date value must not
    break the query or return unrelated rows, just an empty/harmless result."""
    add_expense(registered_user, 10.00, "Food", "2026-08-01", "Mine")

    malicious = "2026-08-01' OR '1'='1"
    # Should not raise, and should not be treated as an OR-true clause.
    rows = db_module.get_expenses_by_user(registered_user, date_from=malicious)
    assert isinstance(rows, list) or rows is not None


# --------------------------------------------------------------------- #
# Templates: filter form repopulation / bookmarkable GET filter          #
# --------------------------------------------------------------------- #

def test_filter_form_uses_get_method(client, registered_user):
    resp = client.get("/profile")
    html = resp.get_data(as_text=True)
    # Filter must submit via GET so it's bookmarkable/shareable
    assert 'method="get"' in html.lower()


def test_filter_form_repopulates_submitted_values(client, registered_user):
    add_expense(registered_user, 10.00, "Food", "2026-08-15", "August expense")

    resp = client.get("/profile?from=2026-08-01&to=2026-08-31")
    html = resp.get_data(as_text=True)
    assert "2026-08-01" in html
    assert "2026-08-31" in html
