import functools
import sqlite3

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash

from . import models
from .db import get_db

auth_bp = Blueprint("auth", __name__)


def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if "user_id" not in session:
            flash("Please log in first.", "warning")
            return redirect(url_for("auth.login", next=request.path))
        return view(**kwargs)

    return wrapped_view


def support_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if session.get("role") != "support":
            flash("This area requires a support account.", "error")
            return redirect(url_for("tickets.dashboard"))
        return view(**kwargs)

    return wrapped_view


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm", "")

        errors = []
        if len(username) < 3:
            errors.append("Username must be at least 3 characters long.")
        if "@" not in email or "." not in email:
            errors.append("Please enter a valid email address.")
        if len(password) < 6:
            errors.append("Password must be at least 6 characters long.")
        if password != confirm:
            errors.append("Passwords do not match.")

        if not errors:
            try:
                models.create_user(
                    get_db(),
                    username,
                    email,
                    generate_password_hash(password),
                    role="client",
                )
                flash("Registration successful. Please log in.", "success")
                return redirect(url_for("auth.login"))
            except sqlite3.IntegrityError:
                errors.append("Username or email is already taken.")

        for error in errors:
            flash(error, "error")

    return render_template("register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = models.get_user_by_username(get_db(), username)

        if user is None or not check_password_hash(user["password_hash"], password):
            flash("Invalid username or password.", "error")
        else:
            session.clear()
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["role"] = user["role"]
            flash(f"Welcome back, {user['username']}!", "success")
            next_url = request.args.get("next")
            if next_url and next_url.startswith("/"):
                return redirect(next_url)
            return redirect(url_for("tickets.dashboard"))

    return render_template("login.html")


@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))
