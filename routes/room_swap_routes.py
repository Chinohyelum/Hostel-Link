from flask import Blueprint, render_template, request, redirect, url_for, flash
from extensions import get_db
from routes.decorators import admin_login_required
import time

room_swap_bp = Blueprint("room_swap", __name__)


def _get_free_bunk_in_room(db, room_id: int):
    """Return a free bunk row in a room (occupied=0), else None."""
    return db.execute(
        "SELECT * FROM bunks WHERE room_id=? AND occupied=0 ORDER BY id ASC LIMIT 1",
        (room_id,)
    ).fetchone()


@room_swap_bp.route("/admin/room-swap-requests", methods=["GET", "POST"])
@admin_login_required
def room_swap_requests():
    db = get_db()

    # ---------------- HANDLE APPROVE/REJECT ----------------
    if request.method == "POST":
        req_id = request.form.get("request_id", "").strip()
        action = request.form.get("action", "").strip().lower()

        if not req_id.isdigit() or action not in ("approve", "reject"):
            flash("Invalid request action.")
            return redirect(url_for("room_swap.room_swap_requests"))

        req_row = db.execute(
            "SELECT * FROM room_swap_requests WHERE id=?",
            (int(req_id),)
        ).fetchone()

        if not req_row:
            flash("Swap request not found.")
            return redirect(url_for("room_swap.room_swap_requests"))

        if req_row["status"] != "pending":
            flash("This request has already been processed.")
            return redirect(url_for("room_swap.room_swap_requests"))

        # Reject: simplest path
        if action == "reject":
            db.execute(
                "UPDATE room_swap_requests SET status=?, decided_at=? WHERE id=?",
                ("rejected", int(time.time()), int(req_id))
            )
            db.commit()
            flash("Swap request rejected.")
            return redirect(url_for("room_swap.room_swap_requests"))

        # Approve: move student to requested room if possible
        student_id = req_row["student_id"]
        requested_room_id = req_row["requested_room_id"]

        # Check student currently occupies a bunk
        current_bunk = db.execute(
            "SELECT * FROM bunks WHERE student_id=? AND occupied=1 LIMIT 1",
            (student_id,)
        ).fetchone()

        if not current_bunk:
            flash("Student has no current bunk allocation; cannot swap.")
            db.execute(
                "UPDATE room_swap_requests SET status=?, decided_at=? WHERE id=?",
                ("rejected", int(time.time()), int(req_id))
            )
            db.commit()
            return redirect(url_for("room_swap.room_swap_requests"))

        # Find a free bunk in requested room
        free_bunk = _get_free_bunk_in_room(db, requested_room_id)
        if not free_bunk:
            flash("Requested room is currently full. Cannot approve.")
            return redirect(url_for("room_swap.room_swap_requests"))

        # Perform swap (really: relocate student)
        # 1) free current bunk
        db.execute(
            "UPDATE bunks SET occupied=0, student_id=NULL WHERE id=?",
            (current_bunk["id"],)
        )

        # 2) occupy new bunk
        db.execute(
            "UPDATE bunks SET occupied=1, student_id=? WHERE id=?",
            (student_id, free_bunk["id"])
        )

        # 3) mark request approved
        db.execute(
            "UPDATE room_swap_requests SET status=?, decided_at=? WHERE id=?",
            ("approved", int(time.time()), int(req_id))
        )

        db.commit()
        flash("Swap request approved and student moved successfully.")
        return redirect(url_for("room_swap.room_swap_requests"))

    # ---------------- GET: SHOW REQUESTS ----------------
    # We join to display room numbers and student name like your HTML expects:
    # req.full_name, req.current_room, req.requested_room, req.status, req.created_at
    requests = db.execute("""
        SELECT
            rs.id,
            rs.status,
            rs.created_at,
            s.full_name AS full_name,
            cr.room_number AS current_room,
            rr.room_number AS requested_room
        FROM room_swap_requests rs
        JOIN students s ON s.id = rs.student_id
        JOIN rooms cr ON cr.id = rs.current_room_id
        JOIN rooms rr ON rr.id = rs.requested_room_id
        ORDER BY rs.created_at DESC
    """).fetchall()

    return render_template("admin/room_swap_requests.html", requests=requests)
