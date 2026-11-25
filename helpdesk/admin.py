from flask import (
    Blueprint,
    abort,
    flash,
    redirect,
    render_template,
    request,
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
    tickets = models.list_all_tickets(get_db())
    return render_template(
        "admin.html", tickets=tickets, statuses=models.STATUSES
    )


@admin_bp.route("/admin/ticket/<int:ticket_id>/status", methods=["POST"])
@login_required
@support_required
def change_status(ticket_id):
    status = request.form.get("status", "")
    if status not in models.STATUSES:
        flash("Invalid status value.", "error")
        return redirect(url_for("admin.admin_panel"))

    ticket = models.get_ticket(get_db(), ticket_id)
    if ticket is None:
        abort(404)

    models.update_ticket_status(get_db(), ticket_id, status)
    flash(f"Ticket #{ticket_id} status changed to '{status}'.", "success")
    return redirect(url_for("admin.admin_panel"))
