from flask import Blueprint, request, redirect, url_for, flash
from extensions import get_db
from routes.decorators import admin_login_required

api = Blueprint("hostel_api", __name__)

# ---------------- ADD ROOM ----------------
@api.route("/api/hostel/<int:hostel_id>/room", methods=["POST"])
@admin_login_required
def add_room(hostel_id):
    db = get_db()
    room_number = request.form.get("room_number", "").strip()
    capacity = request.form.get("capacity", "").strip()

    if not room_number or not capacity.isdigit() or int(capacity) <= 0:
        flash("Please enter valid room number and capacity")
        return redirect(url_for("hostel.manage_hostel", hostel_id=hostel_id))

    db.execute(
        "INSERT INTO rooms (hostel_id, room_number, capacity) VALUES (?,?,?)",
        (hostel_id, room_number, int(capacity))
    )
    db.commit()
    flash(f"Room {room_number} added successfully!")
    return redirect(url_for("hostel.manage_hostel", hostel_id=hostel_id))


# ---------------- ADD BUNK ----------------
@api.route("/api/room/<int:room_id>/bunk", methods=["POST"])
@admin_login_required
def add_bunk(room_id):
    db = get_db()
    bunk_label = request.form.get("bunk_label", "").strip()

    if not bunk_label:
        # Retrieve hostel_id for redirect
        hostel_id = db.execute(
            "SELECT hostel_id FROM rooms WHERE id=?", (room_id,)
        ).fetchone()["hostel_id"]
        flash("Bunk label cannot be empty")
        return redirect(url_for("hostel.manage_hostel", hostel_id=hostel_id))

    db.execute(
        "INSERT INTO bunks (room_id, bunk_label) VALUES (?,?)",
        (room_id, bunk_label)
    )
    db.commit()

    # Retrieve hostel_id for redirect
    hostel_id = db.execute(
        "SELECT hostel_id FROM rooms WHERE id=?", (room_id,)
    ).fetchone()["hostel_id"]

    flash(f"Bunk {bunk_label} added successfully!")
    return redirect(url_for("hostel.manage_hostel", hostel_id=hostel_id))
