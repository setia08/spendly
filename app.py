import sqlite3

from flask import Flask, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash

import datetime

from database.db import (
    create_user,
    get_db,
    get_expenses_by_user,
    get_user_by_email,
    get_user_by_id,
    init_db,
    seed_db,
)

CATEGORY_ACCENTS = {
    "Food": "food",
    "Transport": "transport",
    "Bills": "bills",
    "Health": "health",
    "Entertainment": "entertainment",
    "Shopping": "shopping",
    "Other": "other",
}

app = Flask(__name__)
app.secret_key = "dev-secret-key"

with app.app_context():
    init_db()
    seed_db()


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")

    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")
    confirm_password = request.form.get("confirm_password", "")

    if not name or not email or not password or not confirm_password:
        flash("All fields are required.")
        return render_template("register.html")

    if password != confirm_password:
        flash("Passwords do not match.")
        return render_template("register.html")

    try:
        create_user(name, email, password)
    except sqlite3.IntegrityError:
        flash("Email already registered.")
        return render_template("register.html")

    flash("Account created. Please sign in.", "success")
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")

    user = get_user_by_email(email)
    if user is None or not check_password_hash(user["password_hash"], password):
        flash("Invalid email or password.")
        return render_template("login.html")

    session["user_id"] = user["id"]
    flash("Signed in successfully.", "success")
    return redirect(url_for("landing"))


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


@app.route("/logout")
def logout():
    session.pop("user_id", None)
    return redirect(url_for("landing"))


@app.route("/profile")
def profile():
    user_id = session.get("user_id")
    if user_id is None:
        flash("Please sign in to continue.")
        return redirect(url_for("login"))

    user = get_user_by_id(user_id)
    if user is None:
        session.pop("user_id", None)
        flash("Please sign in to continue.")
        return redirect(url_for("login"))

    member_since = datetime.datetime.strptime(
        user["created_at"], "%Y-%m-%d %H:%M:%S"
    ).strftime("%B %Y")

    today = datetime.date.today()
    preset = request.args.get("preset", "")
    raw_from = request.args.get("from", "").strip()
    raw_to = request.args.get("to", "").strip()

    date_from = date_to = None

    if raw_from or raw_to:
        preset = ""
        try:
            if raw_from:
                datetime.date.fromisoformat(raw_from)
                date_from = raw_from
            if raw_to:
                datetime.date.fromisoformat(raw_to)
                date_to = raw_to
            if date_from and date_to and date_from > date_to:
                flash("From date is after to date — showing all expenses.")
                date_from = date_to = None
        except ValueError:
            flash("Invalid date — showing all expenses.")
            date_from = date_to = None
    elif preset == "month":
        date_from = today.replace(day=1).isoformat()
        date_to = today.isoformat()
    elif preset == "3m":
        date_from = (today - datetime.timedelta(days=90)).isoformat()
        date_to = today.isoformat()
    elif preset == "6m":
        date_from = (today - datetime.timedelta(days=180)).isoformat()
        date_to = today.isoformat()
    else:
        preset = "all"

    expenses = get_expenses_by_user(user_id, date_from, date_to)

    total_spent = sum(e["amount"] for e in expenses)
    transaction_count = len(expenses)

    category_totals = {}
    for e in expenses:
        category_totals[e["category"]] = category_totals.get(e["category"], 0) + e["amount"]

    ranked_categories = sorted(category_totals.items(), key=lambda kv: kv[1], reverse=True)
    top_category = ranked_categories[0][0] if ranked_categories else None
    max_category_total = ranked_categories[0][1] if ranked_categories else 0

    category_breakdown = [
        {
            "category": category,
            "accent": CATEGORY_ACCENTS.get(category, "other"),
            "total": total,
            "percent": round((total / max_category_total) * 100) if max_category_total else 0,
        }
        for category, total in ranked_categories
    ]

    return render_template(
        "profile.html",
        user=user,
        member_since=member_since,
        expenses=expenses[:10],
        category_accents=CATEGORY_ACCENTS,
        total_spent=total_spent,
        transaction_count=transaction_count,
        top_category=top_category,
        category_breakdown=category_breakdown,
        active_preset=preset,
        filter_from=date_from or "",
        filter_to=date_to or "",
    )


@app.route("/expenses/add")
def add_expense():
    return "Add expense — coming in Step 7"


@app.route("/expenses/<int:id>/edit")
def edit_expense(id):
    return "Edit expense — coming in Step 8"


@app.route("/expenses/<int:id>/delete")
def delete_expense(id):
    return "Delete expense — coming in Step 9"


if __name__ == "__main__":
    app.run(debug=True, port=5001)
