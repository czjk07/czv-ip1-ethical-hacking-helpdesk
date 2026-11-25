import os

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
    url_for,
)
from werkzeug.utils import secure_filename

from . import models
from .auth import login_required
from .db import get_db

tickets_bp = Blueprint("tickets", __name__)

ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg"}


def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


def can_view_ticket(ticket):
    return (
        session.get("role") == "support"
        or ticket["user_id"] == session.get("user_id")
    )


@tickets_bp.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("tickets.dashboard"))
    return render_template("index.html")


@tickets_bp.route("/dashboard")
@login_required
def dashboard():
    tickets = models.list_tickets_by_user(get_db(), session["user_id"])
    return render_template("dashboard.html", tickets=tickets)


@tickets_bp.route("/ticket/new", methods=["GET", "POST"])
@login_required
def new_ticket():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        priority = request.form.get("priority", "Medium")
        if priority not in models.PRIORITIES:
            priority = "Medium"

        errors = []
        if not title:
            errors.append("Title is required.")
        if not description:
            errors.append("Description is required.")

        file = request.files.get("attachment")
        if file and file.filename and not allowed_file(file.filename):
            errors.append("Attachment must be a PDF, PNG, JPG or JPEG file.")

        if errors:
            for error in errors:
                flash(error, "error")
            return render_template("ticket_form.html")

        db = get_db()
        ticket_id = models.create_ticket(
            db, session["user_id"], title, description, priority
        )

        if file and file.filename:
            filename = f"{ticket_id}_{secure_filename(file.filename)}"
            file.save(os.path.join(current_app.config["UPLOAD_FOLDER"], filename))
            models.set_ticket_attachment(db, ticket_id, filename)

        flash("Ticket created successfully.", "success")
        return redirect(url_for("tickets.ticket_detail", ticket_id=ticket_id))

    return render_template("ticket_form.html")


@tickets_bp.route("/ticket/<int:ticket_id>")
@login_required
def ticket_detail(ticket_id):
    ticket = models.get_ticket(get_db(), ticket_id)
    if ticket is None or not can_view_ticket(ticket):
        abort(404)
    comments = models.list_comments(get_db(), ticket_id)
    return render_template(
        "ticket_detail.html", ticket=ticket, comments=comments
    )


@tickets_bp.route("/ticket/<int:ticket_id>/comment", methods=["POST"])
@login_required
def add_comment(ticket_id):
    ticket = models.get_ticket(get_db(), ticket_id)
    if ticket is None or not can_view_ticket(ticket):
        abort(404)

    body = request.form.get("body", "").strip()
    if not body:
        flash("Comment cannot be empty.", "error")
    else:
        models.add_comment(get_db(), ticket_id, session["user_id"], body)
        flash("Comment added.", "success")
    return redirect(url_for("tickets.ticket_detail", ticket_id=ticket_id))


@tickets_bp.route("/ticket/<int:ticket_id>/reopen", methods=["POST"])
@login_required
def reopen(ticket_id):
    ticket = models.get_ticket(get_db(), ticket_id)
    if ticket is None or not can_view_ticket(ticket):
        abort(404)

    if ticket["status"] != "Closed":
        flash("Only closed tickets can be reopened.", "error")
        return redirect(url_for("tickets.ticket_detail", ticket_id=ticket_id))

    body = request.form.get("body", "").strip()
    if not body:
        flash("Please add a comment explaining why you are reopening the ticket.", "error")
        return redirect(url_for("tickets.ticket_detail", ticket_id=ticket_id))

    db = get_db()
    models.add_comment(db, ticket_id, session["user_id"], body)
    models.reopen_ticket(db, ticket_id)
    flash("Ticket reopened.", "success")
    return redirect(url_for("tickets.ticket_detail", ticket_id=ticket_id))


@tickets_bp.route("/search")
@login_required
def search():
    query = request.args.get("q", "").strip()
    results = []
    if query:
        user_id = None if session.get("role") == "support" else session["user_id"]
        results = models.search_tickets(get_db(), query, user_id=user_id)
    return render_template("search.html", q=query, results=results)


@tickets_bp.route("/uploads/<path:filename>")
@login_required
def uploaded_file(filename):
    ticket = models.find_ticket_by_attachment(get_db(), filename)
    if ticket is None or not can_view_ticket(ticket):
        abort(404)
    return send_from_directory(current_app.config["UPLOAD_FOLDER"], filename)
