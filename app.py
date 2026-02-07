import os
from flask import Flask, redirect, url_for
from config import Config
from extensions import close_db, get_db
from datetime import datetime

# Models
from models.admin_model import create_admin_table, seed_default_admin
from models.student_model import create_student_table, seed_test_student, ensure_student_profile_columns
from models.reset_model import create_reset_table
from models.hostel_model import create_hostel_table, create_room_table, create_bunk_table
from models.room_swap_model import create_room_swap_table
from models.cancellation_model import create_cancellation_table
from models.student_reset_model import create_student_reset_table
from models.booking_model import create_booking_table, ensure_bunk_booking_columns
from models.swap_details_model import create_swap_details_table
from models.rating_model import create_ratings_table




# Blueprints
from routes.auth_routes import auth_bp
from routes.admin_routes import admin_bp
from routes.hostel_routes import hostel_bp
from routes.hostel_api_routes import api as hostel_api_bp
from routes.room_swap_routes import room_swap_bp
from routes.cancellation_routes import cancellation_bp
from routes.dashboard_routes import dashboard_bp
from routes.student.student_routes import student_bp



def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # ---------------- REGISTER BLUEPRINTS ----------------
    # APP_MODE controls which side gets registered in deployment:
    # - admin service:   APP_MODE=admin
    # - student service: APP_MODE=student
    # - local dev:       APP_MODE=all
    mode = os.getenv("APP_MODE", "all")  # "admin", "student", or "all"

    # Shared/common blueprints (keep these if both sides need them)
    # If your auth routes are ADMIN-only, move auth_bp into the admin block.
    app.register_blueprint(hostel_bp)
    app.register_blueprint(hostel_api_bp)

    # Register admin side
    if mode in ("all", "admin"):
        app.register_blueprint(auth_bp)         # admin login currently here
        app.register_blueprint(admin_bp)
        app.register_blueprint(room_swap_bp)
        app.register_blueprint(cancellation_bp)
        app.register_blueprint(dashboard_bp)

    # Register student side
    if mode in ("all", "student"):
        app.register_blueprint(student_bp)

        # routes for deployment
    from routes.host_guard import enforce_subdomain_rules

    @app.before_request
    def _guard_hosts():
        resp = enforce_subdomain_rules()
        if resp:
            return resp


    # ---------------- INITIALIZE DATABASE ----------------
    with app.app_context():
        create_admin_table()
        seed_default_admin()
        create_student_table()
        ensure_student_profile_columns()  
        seed_test_student()
        create_reset_table()
        create_hostel_table()
        create_room_table()
        create_bunk_table()
        create_room_swap_table()
        create_cancellation_table()
        create_student_reset_table()
        create_booking_table()
        ensure_bunk_booking_columns()
        create_swap_details_table()
        create_ratings_table()


        

    # ---------------- CLOSE DATABASE ----------------
    @app.teardown_appcontext
    def shutdown_db(exception=None):
        close_db()

    # ---------------- DEFAULT ROUTE ----------------
    @app.route("/")
    def home():
        # For deployment:
        # - if admin subdomain service, go to admin login
        # - if student subdomain service, go to student login
        if mode == "student":
            return redirect(url_for("student.login_page"))
        return redirect(url_for("auth.login"))

    # Setting Datetime Filter Globally
    @app.template_filter("datetimeformat")
    def datetimeformat(value):
        """
        Converts Unix timestamp (int) OR SQLite datetime string to readable format.
        """
        if value is None or value == "":
            return ""
        try:
            # if unix timestamp
            if isinstance(value, (int, float)) or str(value).isdigit():
                return datetime.fromtimestamp(int(value)).strftime("%d %b %Y, %I:%M %p")
            # if SQLite datetime string
            return datetime.fromisoformat(str(value)).strftime("%d %b %Y, %I:%M %p")
        except Exception:
            return str(value)

    return app


# CREATE APP INSTANCE
app = create_app()

# RUN SERVER
if __name__ == "__main__":
    app.run(debug=True)


# For accessing and updating student profile
def get_student_by_id(student_id):
    db = get_db()
    return db.execute("SELECT * FROM students WHERE id = ?", (student_id,)).fetchone()

def email_in_use_by_other_student(email, current_student_id):
    db = get_db()
    row = db.execute(
        "SELECT id FROM students WHERE email = ? AND id != ?",
        (email.strip().lower(), current_student_id)
    ).fetchone()
    return row is not None

def update_student_profile(student_id, full_name, email, profile_pic_filename=None):
    db = get_db()

    if profile_pic_filename:
        db.execute("""
            UPDATE students
            SET full_name = ?, email = ?, profile_pic = ?
            WHERE id = ?
        """, (full_name, email.strip().lower(), profile_pic_filename, student_id))
    else:
        db.execute("""
            UPDATE students
            SET full_name = ?, email = ?
            WHERE id = ?
        """, (full_name, email.strip().lower(), student_id))

    db.commit()