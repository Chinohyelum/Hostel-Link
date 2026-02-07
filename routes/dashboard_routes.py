from flask import Blueprint, render_template, redirect, url_for, session, flash
from extensions import get_db
from routes.decorators import admin_login_required

dashboard_bp = Blueprint("dashboard", __name__)

@dashboard_bp.route("/admin/dashboard")
@admin_login_required
def admin_dashboard():
    db = get_db()

    # ✅ Use session admin id if you store it during login
    admin_id = session.get("admin_id")

    # Fallback (so it still works even if you haven't stored admin_id yet)
    if not admin_id:
        admin = db.execute("SELECT * FROM admins ORDER BY id ASC LIMIT 1").fetchone()
    else:
        admin = db.execute("SELECT * FROM admins WHERE id=?", (admin_id,)).fetchone()

    if not admin:
        flash("Admin not found. Please login again.")
        return redirect(url_for("auth.login"))

    # Optional summary counts (safe even if tables empty)
    hostel_count = db.execute("SELECT COUNT(*) AS c FROM hostels").fetchone()["c"] if db else 0

    # These tables might not exist in early development; wrap in try
    try:
        room_swap_pending = db.execute(
            "SELECT COUNT(*) AS c FROM room_swap_requests WHERE status='pending'"
        ).fetchone()["c"]
    except Exception:
        room_swap_pending = 0

    try:
        cancel_pending = db.execute(
            "SELECT COUNT(*) AS c FROM cancellation_requests WHERE status='pending'"
        ).fetchone()["c"]
    except Exception:
        cancel_pending = 0

    return render_template(
        "admin/dashboard.html",
        admin=admin,
        hostel_count=hostel_count,
        room_swap_pending=room_swap_pending,
        cancel_pending=cancel_pending
    )
