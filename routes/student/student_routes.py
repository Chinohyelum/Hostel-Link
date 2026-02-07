from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from models.student_model import get_student_by_matric, verify_student_password
from models.student_reset_model import create_reset_token, get_reset_by_token, mark_token_used
import os
from extensions import get_db
from werkzeug.utils import secure_filename
from flask import current_app
from routes.decorators import student_login_required
from models.student_model import (
    get_student_by_id,
    update_student_profile,
    email_in_use_by_other_student
)
from models.booking_model import (
    get_all_hostels, get_rooms_by_hostel, get_available_bunks_by_room,
    create_booking, get_student_bookings
)
from models.booking_model import (
    get_student_active_room_id,
    get_all_hostels, get_rooms_by_hostel, get_available_bunks_by_room
)
from models.student_swap_submit_model import create_room_swap_request
from models.swap_details_model import save_swap_details
from models.student_cancellation_submit_model import (
    get_student_active_room_id,
    create_cancellation_request,
    get_student_cancellation_requests
)
from models.booking_model import get_student_current_allocation
from models.student_model import get_student_by_id
from models.rating_model import (
    get_student_current_allocation_ids,
    upsert_rating,
    get_student_ratings
)

from models.notification_model import get_student_notifications




student_bp = Blueprint("student", __name__, url_prefix="/student")


@student_bp.get("/login")
def login_page():
    if session.get("student_id"):
        return redirect(url_for("student.dashboard"))
    return render_template("student/login.html")


@student_bp.post("/login")
def login():
    matric_no = request.form.get("matric_no", "").strip()
    password = request.form.get("password", "")

    if not matric_no or not password:
        flash("Matric number and password are required.", "error")
        return redirect(url_for("student.login_page"))

    student = get_student_by_matric(matric_no)
    if not student or not verify_student_password(student, password):
        flash("Invalid matric number or password.", "error")
        return redirect(url_for("student.login_page"))

    # success: create student session
    session.clear()
    session["student_id"] = student["id"]
    session["student_matric_no"] = student["matric_no"]
    session["student_full_name"] = student["full_name"]
    session["student_email"] = student["email"]

    flash("Login successful.", "success")
    return redirect(url_for("student.dashboard"))


@student_bp.get("/dashboard")
def dashboard():
    if not session.get("student_id"):
        flash("Please log in to continue.", "error")
        return redirect(url_for("student.login_page"))

    return render_template("student/dashboard.html")


@student_bp.get("/logout")
def logout():
    session.pop("student_id", None)
    session.pop("student_matric_no", None)
    session.pop("student_full_name", None)
    session.pop("student_email", None)
    flash("Logged out successfully.", "success")
    return redirect(url_for("student.login_page"))


# 

import secrets
from datetime import datetime
from flask import render_template, request, redirect, url_for, flash

from models.student_model import get_student_by_email, update_student_password
from models.student_reset_model import create_reset_token, get_reset_by_token, mark_token_used

# ---------- FORGOT PASSWORD ----------
@student_bp.get("/forgot-password")
def forgot_password_page():
    return render_template("student/forgot_password.html")

@student_bp.post("/forgot-password")
def forgot_password_submit():
    email = request.form.get("email", "").strip().lower()

    if not email:
        flash("Email is required.", "error")
        return redirect(url_for("student.forgot_password_page"))

    student = get_student_by_email(email)

    # IMPORTANT SECURITY: do not reveal if email exists
    # Always show same message
    if student:
        token = secrets.token_urlsafe(32)
        create_reset_token("student", student["id"], token, minutes_valid=30)

        reset_link = url_for("student.reset_password_page", token=token, _external=True)

        # For now: print link to your terminal (works without email service)
        print("\n===== STUDENT RESET LINK =====")
        print(reset_link)
        print("===== END RESET LINK =====\n")

    flash("If that email exists, a reset link has been sent (check console for now).", "success")
    return redirect(url_for("student.login_page"))


# ---------- RESET PASSWORD ----------
@student_bp.get("/reset-password/<token>")
def reset_password_page(token):
    reset_row = get_reset_by_token(token)
    if not reset_row:
        flash("Invalid or expired reset link.", "error")
        return redirect(url_for("student.forgot_password_page"))

    if reset_row["used"] == 1:
        flash("This reset link has already been used.", "error")
        return redirect(url_for("student.forgot_password_page"))

    # Check expiry
    try:
        expires_at = datetime.fromisoformat(reset_row["expires_at"])
        if datetime.now() > expires_at:
            flash("This reset link has expired. Request a new one.", "error")
            return redirect(url_for("student.forgot_password_page"))
    except Exception:
        flash("Reset link is invalid. Request a new one.", "error")
        return redirect(url_for("student.forgot_password_page"))

    return render_template("student/reset_password.html", token=token)


@student_bp.post("/reset-password/<token>")
def reset_password_submit(token):
    password = request.form.get("password", "")
    confirm = request.form.get("confirm_password", "")

    if not password or not confirm:
        flash("All fields are required.", "error")
        return redirect(url_for("student.reset_password_page", token=token))

    if len(password) < 6:
        flash("Password must be at least 6 characters.", "error")
        return redirect(url_for("student.reset_password_page", token=token))

    if password != confirm:
        flash("Passwords do not match.", "error")
        return redirect(url_for("student.reset_password_page", token=token))

    reset_row = get_reset_by_token(token)
    if not reset_row or reset_row["used"] == 1:
        flash("Invalid or expired reset link.", "error")
        return redirect(url_for("student.forgot_password_page"))

    # expiry check again
    try:
        expires_at = datetime.fromisoformat(reset_row["expires_at"])
        if datetime.now() > expires_at:
            flash("This reset link has expired. Request a new one.", "error")
            return redirect(url_for("student.forgot_password_page"))
    except Exception:
        flash("Reset link is invalid. Request a new one.", "error")
        return redirect(url_for("student.forgot_password_page"))

    # reset_row["user_id"] is student.id
    update_student_password(reset_row["user_id"], password)
    mark_token_used(reset_row["id"])

    flash("Password reset successful. Please log in.", "success")
    return redirect(url_for("student.login_page"))


# For student profile management (bonus, not in initial requirements)
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@student_bp.route("/profile", methods=["GET"])
@student_login_required
def profile_page():
    student_id = session.get("student_id")
    student = get_student_by_id(student_id)
    return render_template("student/profile.html", student=student)


@student_bp.route("/profile", methods=["POST"])
@student_login_required
def profile_update():
    student_id = session.get("student_id")
    student = get_student_by_id(student_id)

    full_name = request.form.get("full_name", "").strip()
    email = request.form.get("email", "").strip().lower()

    if not full_name or not email:
        flash("Full name and email are required.", "error")
        return redirect(url_for("student.profile_page"))

    # Prevent email conflicts
    if email_in_use_by_other_student(email, student_id):
        flash("That email is already in use by another student.", "error")
        return redirect(url_for("student.profile_page"))

    # Handle profile picture upload (optional)
    file = request.files.get("profile_pic")
    filename_to_save = None

    if file and file.filename:
        if not allowed_file(file.filename):
            flash("Invalid image type. Use png, jpg, jpeg, or webp.", "error")
            return redirect(url_for("student.profile_page"))

        safe_name = secure_filename(file.filename)
        ext = safe_name.rsplit(".", 1)[1].lower()

        # create unique filename
        filename_to_save = f"student_{student_id}.{ext}"

        # upload folder: static/uploads (you already have this)
        upload_folder = os.path.join(current_app.root_path, "static", "uploads")
        os.makedirs(upload_folder, exist_ok=True)

        file_path = os.path.join(upload_folder, filename_to_save)
        file.save(file_path)

    update_student_profile(student_id, full_name, email, filename_to_save)

    # Update session values so UI immediately reflects changes
    session["student_full_name"] = full_name
    session["student_email"] = email

    flash("Profile updated successfully.", "success")
    return redirect(url_for("student.profile_page"))


# For booking management
@student_bp.route("/book-hostel", methods=["GET"])
@student_login_required
def book_hostel_page():
    hostels = get_all_hostels()
    return render_template("student/book_hostel.html", hostels=hostels)


@student_bp.route("/api/rooms/<int:hostel_id>", methods=["GET"])
@student_login_required
def student_rooms_api(hostel_id):
    rooms = get_rooms_by_hostel(hostel_id)
    return jsonify([{"id": r["id"], "room_number": r["room_number"]} for r in rooms])


@student_bp.route("/api/bunks/<int:room_id>", methods=["GET"])
@student_login_required
def student_bunks_api(room_id):
    bunks = get_available_bunks_by_room(room_id)
    return jsonify([{"id": b["id"], "bunk_label": b["bunk_label"]} for b in bunks])


@student_bp.route("/book-hostel", methods=["POST"])
@student_login_required
def book_hostel_submit():
    student_id = session.get("student_id")
    hostel_id = request.form.get("hostel_id")
    room_id = request.form.get("room_id")
    bunk_id = request.form.get("bunk_id")

    if not hostel_id or not room_id or not bunk_id:
        flash("Please select hostel, room, and bunk.", "error")
        return redirect(url_for("student.book_hostel_page"))

    ok, msg = create_booking(student_id, int(hostel_id), int(room_id), int(bunk_id))
    flash(msg, "success" if ok else "error")
    return redirect(url_for("student.book_hostel_page"))


@student_bp.route("/booking-history", methods=["GET"])
@student_login_required
def booking_history():
    student_id = session.get("student_id")
    bookings = get_student_bookings(student_id)
    return render_template("student/booking_history.html", bookings=bookings)


# Swap + Submit route

@student_bp.route("/swap-request", methods=["GET"])
@student_login_required
def swap_request_page():
    hostels = get_all_hostels()
    return render_template("student/swap_request.html", hostels=hostels)


@student_bp.route("/swap-request", methods=["POST"])
@student_login_required
def swap_request_submit():
    student_id = session.get("student_id")

    current_room_id = get_student_active_room_id(student_id)
    if not current_room_id:
        flash("You need an active booking before requesting a swap.", "error")
        return redirect(url_for("student.swap_request_page"))

    hostel_id = request.form.get("hostel_id")
    requested_room_id = request.form.get("room_id")
    requested_bunk_id = request.form.get("bunk_id")
    reason = request.form.get("reason", "").strip()

    if not hostel_id or not requested_room_id or not requested_bunk_id:
        flash("Please select hostel, room and bunk.", "error")
        return redirect(url_for("student.swap_request_page"))

    # confirm bunk belongs to requested room and is available
    db = get_db()
    bunk = db.execute("""
        SELECT id, room_id, occupied
        FROM bunks
        WHERE id = ?
    """, (int(requested_bunk_id),)).fetchone()

    if not bunk or bunk["room_id"] != int(requested_room_id):
        flash("Invalid bunk selection.", "error")
        return redirect(url_for("student.swap_request_page"))

    if bunk["occupied"] == 1:
        flash("That bunk is already occupied. Choose another.", "error")
        return redirect(url_for("student.swap_request_page"))

    ok, swap_id, msg = create_room_swap_request(
        student_id,
        int(current_room_id),
        int(requested_room_id)
    )

    if not ok:
        flash(msg, "error")
        return redirect(url_for("student.swap_request_page"))

    # store the requested bunk + reason without changing admin table
    save_swap_details(swap_id, int(requested_bunk_id), reason)

    flash("Swap request submitted and sent to admin for approval.", "success")
    return redirect(url_for("student.swap_request_page"))


# cancellation routes
@student_bp.route("/cancel-booking", methods=["GET"])
@student_login_required
def cancel_booking_page():
    student_id = session.get("student_id")
    room_id = get_student_active_room_id(student_id)
    requests = get_student_cancellation_requests(student_id)
    return render_template("student/cancel_booking.html", room_id=room_id, requests=requests)


@student_bp.route("/cancel-booking", methods=["POST"])
@student_login_required
def cancel_booking_submit():
    student_id = session.get("student_id")
    room_id = get_student_active_room_id(student_id)

    if not room_id:
        flash("You do not have an active room allocation to cancel.", "error")
        return redirect(url_for("student.cancel_booking_page"))

    ok, msg = create_cancellation_request(student_id, room_id)
    flash(msg, "success" if ok else "error")
    return redirect(url_for("student.cancel_booking_page"))


# # temporary placeholder until oommate feature is wired

# @student_bp.route("/roommates", methods=["GET"])
# @student_login_required
# def roommates_page():
#     # temporary placeholder until roommates feature is wired
#     return "Roommates page coming soon"


# Roommates routes
@student_bp.route("/roommates", methods=["GET"])
@student_login_required
def roommates_page():
    student_id = session.get("student_id")
    allocation = get_student_current_allocation(student_id)

    if not allocation:
        flash("You don’t have an active booking yet. Book a hostel to see roommates.", "error")
        return redirect(url_for("student.book_hostel_page"))

    db = get_db()
    roommates = db.execute("""
        SELECT s.id,
               s.matric_no,
               s.full_name,
               COALESCE(NULLIF(s.nickname,''), s.full_name) AS display_name,
               s.department
        FROM bunks k
        JOIN students s ON s.id = k.occupied_by
        WHERE k.room_id = ?
          AND k.occupied = 1
          AND k.occupied_by IS NOT NULL
          AND s.id != ?
        ORDER BY display_name
    """, (allocation["room_id"], student_id)).fetchall()

    return render_template(
        "student/roommates.html",
        allocation=allocation,
        roommates=roommates
    )


# ----------------------------HOSTEL CARD ROUTES----------------------------
@student_bp.route("/hostel-card", methods=["GET"])
@student_login_required
def hostel_card_page():
    student_id = session.get("student_id")
    allocation = get_student_current_allocation(student_id)

    if not allocation:
        flash("You don’t have an active booking yet, so you can’t print a hostel card.", "error")
        return redirect(url_for("student.book_hostel_page"))

    student = get_student_by_id(student_id)
    return render_template("student/hostel_card.html", student=student, allocation=allocation)


# ----------------------------RATING ROUTES----------------------------@student_bp.route("/ratings", methods=["GET"])
@student_bp.route("/ratings", methods=["GET"])
@student_login_required
def ratings_page():
    student_id = session.get("student_id")
    allocation = get_student_current_allocation_ids(student_id)
    ratings = get_student_ratings(student_id)
    return render_template("student/ratings.html", allocation=allocation, ratings=ratings)


@student_bp.route("/ratings", methods=["POST"])
@student_login_required
def ratings_submit():
    student_id = session.get("student_id")
    allocation = get_student_current_allocation_ids(student_id)

    if not allocation:
        flash("You need an active booking before submitting ratings.", "error")
        return redirect(url_for("student.ratings_page"))

    target = request.form.get("target")  # hostel | room
    rating = request.form.get("rating")
    comment = request.form.get("comment", "")

    try:
        rating = int(rating)
    except:
        rating = 0

    if rating < 1 or rating > 5:
        flash("Rating must be between 1 and 5.", "error")
        return redirect(url_for("student.ratings_page"))

    hostel_id = allocation["hostel_id"]
    room_id = allocation["room_id"] if target == "room" else None

    ok, msg = upsert_rating(student_id, hostel_id, room_id, rating, comment)
    flash(msg, "success" if ok else "error")
    return redirect(url_for("student.ratings_page"))


# -------------------------------LOGOUT-------------------------
@student_bp.route("/logout", methods=["GET"])
def student_logout():
    # Remove only student session keys
    session.pop("student_id", None)
    session.pop("student_matric_no", None)   # if you store it
    session.pop("student_name", None)        # if you store it

    flash("You have been logged out.", "success")
    return redirect(url_for("student.login_page"))


# ----------------------------NOTIFICATIONS----------------------------
@student_bp.route("/notifications", methods=["GET"])
@student_login_required
def notifications_page():
    student_id = session.get("student_id")
    notifications = get_student_notifications(student_id)
    return render_template("student/notifications.html", notifications=notifications)

# Bell notifications counter 

@student_bp.app_context_processor
def inject_notification_count():
    from flask import session
    student_id = session.get("student_id")
    if not student_id:
        return dict(notification_count=0)

    notifications = get_student_notifications(student_id)

    # Count only unresolved items (pending)
    count = sum(1 for n in notifications if n["status"] == "pending")

    return dict(notification_count=count)
