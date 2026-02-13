from flask import Blueprint, render_template, request, redirect, url_for, flash
from extensions import get_db
from routes.decorators import admin_login_required
import time
import os
from werkzeug.utils import secure_filename

hostel_bp = Blueprint("hostel", __name__)

# ---------------- CREATE HOSTEL ----------------
# ---------------- CREATE HOSTEL ----------------
@hostel_bp.route("/admin/hostels", methods=["GET", "POST"])
@admin_login_required
def create_hostel():
    """
    Page: create_hostel.html
    - Shows form to create a new hostel
    - Lists all hostels with a 'Manage' button
    """
    db = get_db()

    if request.method == "POST":
        name = request.form["name"].strip()
        gender = request.form.get("gender", "").strip()
        faculty = request.form.get("faculty", "").strip()

        if not name or not gender:
            flash("Please enter hostel name and select gender")
            return redirect(url_for("hostel.create_hostel"))

        # ---- NEW: handle optional image upload ----
        image_filename = None
        file = request.files.get("hostel_image")

        if file and file.filename:
            if allowed_file(file.filename):
                # Make filename unique to avoid overwriting
                original = secure_filename(file.filename)
                ext = original.rsplit(".", 1)[1].lower()
                image_filename = f"{uuid4().hex}.{ext}"

                upload_dir = os.path.join(current_app.static_folder, UPLOAD_SUBFOLDER)
                os.makedirs(upload_dir, exist_ok=True)

                save_path = os.path.join(upload_dir, image_filename)
                file.save(save_path)
            else:
                flash("Invalid image type. Use png, jpg, jpeg, gif, or webp.")
                return redirect(url_for("hostel.create_hostel"))

        # ---- UPDATED INSERT: now includes image ----
        db.execute(
            "INSERT INTO hostels (name, gender, faculty, image, created_at) VALUES (?,?,?,?,?)",
            (name, gender, faculty, image_filename, int(time.time()))
        )
        db.commit()

        flash("Hostel created successfully!")
        return redirect(url_for("hostel.create_hostel"))

    # (Keep your existing GET logic below exactly as you already have it)
    # Example (only if you already do it):
    # hostels = db.execute("SELECT * FROM hostels ORDER BY created_at DESC").fetchall()
    # return render_template("create_hostel.html", hostels=hostels, ...)

    # If your existing code already returns render_template here, leave it as-is.



    # Fetch hostels and number of free bunks for each
    hostels = db.execute("""
        SELECT h.*,
        (SELECT COUNT(*) FROM bunks b
         JOIN rooms r ON b.room_id=r.id
         WHERE r.hostel_id=h.id AND b.occupied=0) AS free_bunks
        FROM hostels h
    """).fetchall()

    return render_template("admin/create_hostel.html", hostels=hostels)


# ---------------- MANAGE HOSTEL ----------------
@hostel_bp.route("/admin/hostel/<int:hostel_id>")
@admin_login_required
def manage_hostel(hostel_id):
    """
    Page: manage_hostels.html
    - Shows hostel details
    - Shows all rooms + bunks
    - Allows adding rooms/bunks dynamically
    """
    db = get_db()

    # Get hostel details
    hostel = db.execute("SELECT * FROM hostels WHERE id=?", (hostel_id,)).fetchone()
    if not hostel:
        flash("Hostel not found")
        return redirect(url_for("hostel.create_hostel"))

    # Get rooms for this hostel
    rooms = db.execute("SELECT * FROM rooms WHERE hostel_id=?", (hostel_id,)).fetchall()

    room_data = []
    for room in rooms:
        # Access row columns via dict-like keys to avoid AttributeError
        room_id = room["id"]  # <-- this fixes the 'sqlite3.Row has no attribute id'
        bunks = db.execute("SELECT * FROM bunks WHERE room_id=?", (room_id,)).fetchall()
        room_data.append({"room": room, "bunks": bunks})

    return render_template(
        "admin/manage_hostels.html",
        hostel=hostel,
        room_data=room_data
    )
