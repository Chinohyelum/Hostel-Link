from flask import Blueprint, render_template, request, redirect, url_for, flash
from extensions import get_db
from routes.decorators import admin_login_required
import time

cancellation_bp = Blueprint("cancellation", __name__)

@cancellation_bp.route("/admin/cancellation-requests", methods=["GET", "POST"])
@admin_login_required
def cancellation_requests():
    db = get_db()

    # ---------- POST: approve/reject ----------
    if request.method == "POST":
        req_id = request.form.get("request_id", "").strip()
        action = request.form.get("action", "").strip().lower()

        if not req_id.isdigit() or action not in ("approve", "reject"):
            flash("Invalid action.")
            return redirect(url_for("cancellation.cancellation_requests"))

        req_row = db.execute(
            "SELECT * FROM cancellation_requests WHERE id=?",
            (int(req_id),)
        ).fetchone()

        if not req_row:
            flash("Cancellation request not found.")
            return redirect(url_for("cancellation.cancellation_requests"))

        if req_row["status"] != "pending":
            flash("This request has already been processed.")
            return redirect(url_for("cancellation.cancellation_requests"))

        if action == "reject":
            db.execute(
                "UPDATE cancellation_requests SET status=?, decided_at=? WHERE id=?",
                ("rejected", int(time.time()), int(req_id))
            )
            db.commit()
            flash("Cancellation request rejected.")
            return redirect(url_for("cancellation.cancellation_requests"))

        # ---------- APPROVE: free student's bunk ----------
        student_id = req_row["student_id"]

        # Find the bunk currently occupied by this student
        bunk = db.execute(
            "SELECT * FROM bunks WHERE student_id=? AND occupied=1 LIMIT 1",
            (student_id,)
        ).fetchone()

        if bunk:
            db.execute(
                "UPDATE bunks SET occupied=0, student_id=NULL WHERE id=?",
                (bunk["id"],)
            )

        db.execute(
            "UPDATE cancellation_requests SET status=?, decided_at=? WHERE id=?",
            ("approved", int(time.time()), int(req_id))
        )
        db.commit()

        flash("Cancellation approved. Student allocation cleared.")
        return redirect(url_for("cancellation.cancellation_requests"))

    # ---------- GET: show requests ----------
    requests = db.execute("""
        SELECT
            c.id,
            c.status,
            c.created_at,
            s.full_name AS full_name,
            r.room_number AS room_number
        FROM cancellation_requests c
        JOIN students s ON s.id = c.student_id
        JOIN rooms r ON r.id = c.room_id
        ORDER BY c.created_at DESC
    """).fetchall()

    return render_template("admin/cancellation_requests.html", requests=requests)
