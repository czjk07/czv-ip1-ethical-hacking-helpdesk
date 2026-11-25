from flask import (
    Blueprint,
    abort,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from . import models
from .auth import login_required, support_required
from .db import get_db

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/admin")
@login_required
@support_required
def admin_panel():
    db = get_db()
    tickets = models.list_all_tickets(db)
    support_users = models.list_support_users(db)
    return render_template(
        "admin.html",
        tickets=tickets,
        statuses=models.STATUSES,
        support_users=support_users,
    )


@admin_bp.route("/admin/ticket/<int:ticket_id>/status", methods=["POST"])
@login_required
@support_required
def change_status(ticket_id):
    status = request.form.get("status", "")
    note = request.form.get("note", "").strip()
    if status not in models.STATUSES:
        flash("Invalid status value.", "error")
        return redirect(url_for("admin.admin_panel"))

    ticket = models.get_ticket(get_db(), ticket_id)
    if ticket is None:
        abort(404)

    if status == "Closed" and not note:
        flash("A resolution note is required when closing a ticket.", "error")
        return redirect(url_for("admin.admin_panel"))

    db = get_db()
    if status == "Closed":
        models.add_comment(db, ticket_id, session["user_id"], note)
    models.update_ticket_status(db, ticket_id, status)
    flash(f"Ticket #{ticket_id} status changed to '{status}'.", "success")
    return redirect(url_for("admin.admin_panel"))


@admin_bp.route("/admin/ticket/<int:ticket_id>/assign", methods=["POST"])
@login_required
@support_required
def assign(ticket_id):
    ticket = models.get_ticket(get_db(), ticket_id)
    if ticket is None:
        abort(404)

    raw = request.form.get("assignee_id", "").strip()
    if raw == "":
        models.assign_ticket(get_db(), ticket_id, None)
        flash(f"Ticket #{ticket_id} unassigned.", "success")
        return redirect(url_for("admin.admin_panel"))

    try:
        assignee_id = int(raw)
    except ValueError:
        flash("Invalid assignee.", "error")
        return redirect(url_for("admin.admin_panel"))

    assignee = models.get_user(get_db(), assignee_id)
    if assignee is None or assignee["role"] != "support":
        flash("Assignee must be a support user.", "error")
        return redirect(url_for("admin.admin_panel"))

    models.assign_ticket(get_db(), ticket_id, assignee_id)
    flash(f"Ticket #{ticket_id} assigned to {assignee['username']}.", "success")
    return redirect(url_for("admin.admin_panel"))
