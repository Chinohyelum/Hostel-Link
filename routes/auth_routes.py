import random
import time
from flask import Flask, Blueprint, render_template, request, redirect, url_for, session, flash
from extensions import get_db
from werkzeug.security import generate_password_hash, check_password_hash

auth_bp = Blueprint("auth", __name__)

# ---------- LOGIN ----------
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        db = get_db()
        admin = db.execute("SELECT * FROM admins WHERE email = ?", (email,)).fetchone()

        if admin and check_password_hash(admin["password"], password):
            session["admin_id"] = admin["id"]
            session["admin_name"] = admin["nickname"]
            return redirect(url_for("auth.dashboard"))
        flash("Invalid email or password")
    return render_template("auth/login.html")

# ---------- DASHBOARD ----------
@auth_bp.route("/dashboard")
def dashboard():
    if "admin_id" not in session:
        return redirect(url_for("auth.login"))
    return render_template("admin/dashboard.html")

# ---------- FORGOT PASSWORD STEP 1 ----------

@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form["email"].strip()
        db = get_db()
        admin = db.execute("SELECT * FROM admins WHERE email = ?", (email,)).fetchone()

        if not admin:
            flash("Email not found")
            return redirect(url_for("auth.forgot_password"))

        # Fixed code for testing
        code = "1234"
        expires_at = int(time.time()) + 600  # expires in 10 min

        # Insert or update reset code
        db.execute("DELETE FROM password_resets WHERE email = ?", (email,))
        db.execute(
            "INSERT INTO password_resets (email, code, expires_at) VALUES (?, ?, ?)",
            (email, code, expires_at)
        )
        db.commit()

        session["reset_email"] = email
        flash(f"Reset code is {code} (for testing)")
        return redirect(url_for("auth.reset_password"))

    return render_template("auth/forgot.html")


# ---------- RESET PASSWORD STEP 2 ----------
@auth_bp.route("/reset-password", methods=["GET", "POST"])
def reset_password():
    if "reset_email" not in session:
        return redirect(url_for("auth.forgot_password"))

    email = session["reset_email"]
    db = get_db()

    if request.method == "POST":
        code_input = request.form["code"].strip()
        new_pass = request.form["new_password"].strip()
        confirm_pass = request.form["confirm_password"].strip()

        # Get reset record
        record = db.execute("SELECT * FROM password_resets WHERE email = ?", (email,)).fetchone()
        if not record:
            flash("No reset request found")
            return redirect(url_for("auth.forgot_password"))

        # Check code expiry
        if int(time.time()) > record["expires_at"]:
            flash("Code expired")
            return redirect(url_for("auth.forgot_password"))

        # Verify code
        if record["code"] != code_input:
            flash("Invalid code")
            return redirect(url_for("auth.reset_password"))

        # Verify passwords match
        if new_pass != confirm_pass:
            flash("Passwords do not match")
            return redirect(url_for("auth.reset_password"))

        # Update password
        db.execute("UPDATE admins SET password = ? WHERE email = ?", (generate_password_hash(new_pass), email))
        db.execute("DELETE FROM password_resets WHERE email = ?", (email,))
        db.commit()
        session.pop("reset_email", None)

        flash("Password reset successfully")
        return redirect(url_for("auth.dashboard"))

    return render_template("auth/reset.html")

# ---------- LOGOUT ----------
from flask import session, redirect, url_for, flash

@auth_bp.route("/logout")
def logout():
    # Clear admin session (and any other user session keys)
    session.pop("admin_id", None)
    session.pop("student_id", None)   # safe for later when you add students
    session.pop("role", None)
    session.pop("admin_logged_in", None)

    flash("You have been logged out successfully.")
    return redirect(url_for("auth.login"))
