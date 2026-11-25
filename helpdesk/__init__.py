import os
import sqlite3

import click
from flask import Flask, flash, redirect, request, url_for
from werkzeug.security import generate_password_hash

from .db import close_db, get_db, init_db


def create_app():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    app = Flask(__name__, root_path=base_dir)
    app.config["SECRET_KEY"] = os.environ.get(
        "SECRET_KEY", "dev-only-secret-key-change-in-production"
    )
    app.config["SUPPORT_SIGNUP_KEY"] = os.environ.get("SUPPORT_SIGNUP_KEY", "")
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024
    app.config["UPLOAD_FOLDER"] = os.environ.get(
        "UPLOAD_FOLDER", os.path.join(base_dir, "uploads")
    )
    app.config["DATABASE"] = os.environ.get(
        "DATABASE_PATH", os.path.join(base_dir, "data", "helpdesk.db")
    )
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(os.path.dirname(app.config["DATABASE"]), exist_ok=True)

    app.teardown_appcontext(close_db)

    @app.after_request
    def set_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "img-src 'self' data:; "
            "font-src 'self' https://cdn.jsdelivr.net"
        )
        return response

    with app.app_context():
        init_db()

    from .admin import admin_bp
    from .auth import auth_bp
    from .tickets import tickets_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(tickets_bp)
    app.register_blueprint(admin_bp)

    @app.errorhandler(413)
    def file_too_large(error):
        flash("Uploaded file is too large (max 5 MB).", "error")
        return redirect(request.referrer or url_for("tickets.new_ticket")), 413

    @app.cli.command("create-support")
    @click.argument("username")
    @click.argument("email")
    @click.option(
        "--password",
        prompt=True,
        hide_input=True,
        confirmation_prompt=True,
        help="Password for the support account.",
    )
    def create_support_command(username, email, password):
        """Create (or update) a support/admin account."""
        from . import models

        db = get_db()
        password_hash = generate_password_hash(password)
        existing = models.get_user_by_username(db, username)
        if existing is not None:
            models.update_user_credentials(db, existing["id"], password_hash, "support")
            click.echo(f"Support account '{username}' updated.")
            return
        try:
            models.create_user(db, username, email, password_hash, role="support")
            click.echo(f"Support account '{username}' created.")
        except sqlite3.IntegrityError:
            click.echo("That email is already used by another account.", err=True)
            raise SystemExit(1)

    return app
