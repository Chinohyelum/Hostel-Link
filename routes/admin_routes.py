from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from extensions import get_db, save_file
from werkzeug.security import generate_password_hash
from routes.decorators import admin_login_required
import os
import time
import re

admin_bp = Blueprint("admin_bp", __name__)

admin_bp = Blueprint("admin", __name__)

# ---------------- SESSION PROTECTION DECORATOR ----------------
def admin_login_required(f):
    from functools import wraps
    from flask import abort
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "admin_id" not in session:
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated_function

# ---------------- DASHBOARD ----------------
@admin_bp.route("/admin/dashboard")
@admin_login_required
def dashboard():
    return render_template("admin/dashboard.html")

# ---------------- CREATE ADMIN ----------------
@admin_bp.route("/admin/create-admin", methods=["GET", "POST"])
@admin_login_required
def create_admin():
    if request.method == "POST":
        first_name = request.form["first_name"].strip()
        last_name = request.form["last_name"].strip()
        nickname = request.form["nickname"].strip()
        email = request.form["email"].strip()
        password = request.form["password"].strip()
        confirm_password = request.form["confirm_password"].strip()

        # Server-side validation
        if not all([first_name, last_name, email, password, confirm_password]):
            flash("All required fields must be filled")
            return redirect(url_for("admin.create_admin"))

        if password != confirm_password:
            flash("Passwords do not match")
            return redirect(url_for("admin.create_admin"))

        if len(password) < 6:
            flash("Password must be at least 6 characters")
            return redirect(url_for("admin.create_admin"))

        db = get_db()
        # Check if email exists
        existing = db.execute("SELECT * FROM admins WHERE email = ?", (email,)).fetchone()
        if existing:
            flash("Email already exists")
            return redirect(url_for("admin.create_admin"))

        db.execute(
            "INSERT INTO admins (first_name, last_name, nickname, email, password) VALUES (?, ?, ?, ?, ?)",
            (first_name, last_name, nickname, email, generate_password_hash(password))
        )
        db.commit()
        flash("New admin created successfully!")
        return redirect(url_for("admin.create_admin"))

    return render_template("admin/create_admin.html")

# ---------------- CREATE STUDENT ----------------
@admin_bp.route("/admin/create-student", methods=["GET", "POST"])
@admin_login_required
def create_student():
    if request.method == "POST":
        full_name = request.form["full_name"].strip()
        matric_no = request.form["matric_no"].strip()
        email = request.form["email"].strip()
        password = request.form["password"].strip()
        confirm_password = request.form["confirm_password"].strip()

        # Server-side validation
        if not all([full_name, matric_no, email, password, confirm_password]):
            flash("All required fields must be filled")
            return redirect(url_for("admin.create_student"))

        if password != confirm_password:
            flash("Passwords do not match")
            return redirect(url_for("admin.create_student"))

        if len(password) < 6:
            flash("Password must be at least 6 characters")
            return redirect(url_for("admin.create_student"))

        db = get_db()
        # Check if email or matric exists
        existing_email = db.execute("SELECT * FROM students WHERE email = ?", (email,)).fetchone()
        existing_matric = db.execute("SELECT * FROM students WHERE matric_no = ?", (matric_no,)).fetchone()
        if existing_email:
            flash("Email already exists")
            return redirect(url_for("admin.create_student"))
        if existing_matric:
            flash("Matric number already exists")
            return redirect(url_for("admin.create_student"))

        db.execute(
            "INSERT INTO students (full_name, matric_no, email, password) VALUES (?, ?, ?, ?)",
            (full_name, matric_no, email, generate_password_hash(password))
        )
        db.commit()
        flash("New student created successfully!")
        return redirect(url_for("admin.create_student"))

    return render_template("admin/create_student.html")

# ------------------- CANCELLATION REQUESTS ----------------
@admin_bp.route("/admin/cancellation-requests")
@admin_login_required
def cancellation_requests():
    db = get_db()
    requests = db.execute("""
        SELECT cr.id, s.full_name, r.room_number, cr.status, cr.created_at
        FROM cancellation_requests cr
        JOIN students s ON cr.student_id = s.id
        JOIN rooms r ON cr.room_id = r.id
        ORDER BY cr.created_at DESC
    """).fetchall()
    return render_template("admin/cancellation_requests.html", requests=requests)

# ------------------- ROOM SWAP REQUESTS ----------------

@admin_bp.route("/admin/room-swap-requests", methods=["GET", "POST"])
@admin_login_required
def room_swap_requests():
    db = get_db()

    if request.method == "POST":
        action = request.form.get("action")
        request_id = request.form.get("request_id")

        # Fetch the swap request
        swap_req = db.execute("SELECT * FROM room_swap_requests WHERE id = ?", (request_id,)).fetchone()
        if not swap_req:
            flash("Request not found")
            return redirect(url_for("admin.room_swap_requests"))

        if action == "approve":
            # Swap students: we assume each room has a bunk assigned (student_id in bunk)
            # Fetch current and requested rooms
            db.execute("""
                UPDATE bunks
                SET student_id = CASE
                    WHEN student_id = ? THEN NULL
                    WHEN student_id IS NULL AND id = ? THEN ?
                    ELSE student_id
                END
                WHERE room_id IN (?, ?)
            """, (swap_req['student_id'], swap_req['requested_room_id'], swap_req['student_id'], swap_req['current_room_id'], swap_req['requested_room_id']))

            db.execute("UPDATE room_swap_requests SET status = 'approved' WHERE id = ?", (request_id,))
            db.commit()
            flash("Room swap approved")

        elif action == "reject":
            db.execute("UPDATE room_swap_requests SET status = 'rejected' WHERE id = ?", (request_id,))
            db.commit()
            flash("Room swap rejected")

        return redirect(url_for("admin.room_swap_requests"))

    # Fetch all swap requests
    requests = db.execute("""
        SELECT rs.id, s.full_name, cr.room_number AS current_room, rr.room_number AS requested_room, rs.status, rs.created_at
        FROM room_swap_requests rs
        JOIN students s ON rs.student_id = s.id
        JOIN rooms cr ON rs.current_room_id = cr.id
        JOIN rooms rr ON rs.requested_room_id = rr.id
        ORDER BY rs.created_at DESC
    """).fetchall()

    return render_template("admin/room_swap_requests.html", requests=requests)


# ---------------- ADMIN PROFILE ----------------
@admin_bp.route("/admin/profile", methods=["GET", "POST"])
@admin_login_required
def admin_profile():
    db = get_db()
    admin_id = 1  # Replace with dynamic ID from session if using login

    # Fetch admin data
    admin = db.execute("SELECT * FROM admins WHERE id=?", (admin_id,)).fetchone()
    if not admin:
        flash("Admin not found")
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        first_name = request.form.get("first_name").strip()
        last_name = request.form.get("last_name").strip()
        nickname = request.form.get("nickname").strip()
        email = request.form.get("email").strip()
        role = request.form.get("role").strip()

        # Profile picture upload
        file = request.files.get("profile_picture")
        if file and file.filename:
            filename = save_file(file, folder="uploads/profile_pics")
            admin_picture = filename
        else:
            admin_picture = admin["profile_picture"]

        # Update DB
        db.execute("""
            UPDATE admins SET
                first_name=?,
                last_name=?,
                nickname=?,
                email=?,
                role=?,
                profile_picture=?
            WHERE id=?
        """, (first_name, last_name, nickname, email, role, admin_picture, admin_id))
        db.commit()
        flash("Profile updated successfully!")
        return redirect(url_for("admin.admin_profile"))

    return render_template("admin/admin_profile.html", admin=admin)