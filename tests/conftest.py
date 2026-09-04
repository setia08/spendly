import os
import tempfile

import pytest

import database.db as db_module
import app as app_module


@pytest.fixture
def app():
    """Flask app wired to an isolated, temporary SQLite DB (never spendly.db)."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)

    original_path = db_module.DB_PATH
    db_module.DB_PATH = path
    # app.py imported get_db/init_db etc. by name, so patch its references too.
    app_module.get_db = db_module.get_db

    db_module.init_db()
    # Deliberately skip seed_db() so tests control their own fixtures.

    flask_app = app_module.app
    flask_app.config.update(TESTING=True)

    yield flask_app

    db_module.DB_PATH = original_path
    os.remove(path)


@pytest.fixture
def client(app):
    return app.test_client()


def register_user(client, name="Test User", email="test@example.com", password="password123"):
    return client.post(
        "/register",
        data={
            "name": name,
            "email": email,
            "password": password,
            "confirm_password": password,
        },
        follow_redirects=True,
    )


def login_user(client, email="test@example.com", password="password123"):
    return client.post(
        "/login",
        data={"email": email, "password": password},
        follow_redirects=True,
    )


@pytest.fixture
def registered_user(client):
    """Registers and logs in a user, returns their DB id."""
    register_user(client)
    login_user(client)
    user = db_module.get_user_by_email("test@example.com")
    return user["id"]


def add_expense(user_id, amount, category, date, description=""):
    conn = db_module.get_db()
    conn.execute(
        """
        INSERT INTO expenses (user_id, amount, category, date, description)
        VALUES (?, ?, ?, ?, ?)
        """,
        (user_id, amount, category, date, description),
    )
    conn.commit()
    conn.close()
