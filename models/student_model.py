from extensions import get_db
from werkzeug.security import generate_password_hash, check_password_hash

def create_student_table():
    db = get_db()
    db.execute("""
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        matric_no TEXT UNIQUE NOT NULL,
        full_name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    db.commit()


def create_student(matric_no, full_name, email, password):
    db = get_db()
    db.execute("""
    INSERT INTO students (matric_no, full_name, email, password)
    VALUES (?, ?, ?, ?)
    """, (
        matric_no,
        full_name,
        email,
        generate_password_hash(password)
    ))
    db.commit()

# Adding profile pic and department fields
def ensure_student_profile_columns():
    """
    Safely adds profile_pic and department columns if missing.
    This will NOT delete data or break existing table.
    """
    db = get_db()
    cols = db.execute("PRAGMA table_info(students)").fetchall()
    existing = {c["name"] for c in cols}

    if "profile_pic" not in existing:
        db.execute("ALTER TABLE students ADD COLUMN profile_pic TEXT")

    if "department" not in existing:
        db.execute("ALTER TABLE students ADD COLUMN department TEXT")

    db.commit()

    # Default student account for testing
from werkzeug.security import generate_password_hash
from extensions import get_db

def seed_test_student():
    """
    Inserts one test student if it doesn't already exist.
    Matric: u22csc823
    Password: student123
    """
    db = get_db()

    # check if student exists
    existing = db.execute(
        "SELECT id FROM students WHERE matric_no = ?",
        ("u22csc823",)
    ).fetchone()

    if existing:
        return  # already seeded

    db.execute("""
        INSERT INTO students (matric_no, full_name, email, password)
        VALUES (?, ?, ?, ?)
    """, (
        "u22csc823",
        "Test Student",
        "u22csc823@student.test",
        generate_password_hash("student123")
    ))
    db.commit()


# ------------------ AUTH HELPERS ------------------

def get_student_by_matric(matric_no):
    db = get_db()
    student = db.execute(
        "SELECT * FROM students WHERE matric_no = ?",
        (matric_no,)
    ).fetchone()
    return student

def verify_student_password(student_row, plain_password):
    # student_row["password"] is your hashed password
    return check_password_hash(student_row["password"], plain_password)

# Forgot Password Helpers

def get_student_by_email(email):
    db = get_db()
    return db.execute("SELECT * FROM students WHERE email = ?", (email.strip().lower(),)).fetchone()

def update_student_password(student_id, new_password):
    db = get_db()
    db.execute("""
        UPDATE students SET password = ? WHERE id = ?
    """, (generate_password_hash(new_password), student_id))
    db.commit()


# making email the primary key

def get_student_by_id(student_id):
    db = get_db()
    return db.execute(
        "SELECT * FROM students WHERE id = ?",
        (student_id,)
    ).fetchone()

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
        """, (full_name.strip(), email.strip().lower(), profile_pic_filename, student_id))
    else:
        db.execute("""
            UPDATE students
            SET full_name = ?, email = ?
            WHERE id = ?
        """, (full_name.strip(), email.strip().lower(), student_id))

    db.commit()

def ensure_student_profile_columns():
    """
    Adds profile_pic + department columns if missing.
    Works safely with existing SQLite table.
    """
    db = get_db()
    cols = db.execute("PRAGMA table_info(students)").fetchall()
    existing = {c["name"] for c in cols}

    if "profile_pic" not in existing:
        db.execute("ALTER TABLE students ADD COLUMN profile_pic TEXT")

    if "department" not in existing:
        db.execute("ALTER TABLE students ADD COLUMN department TEXT")

    db.commit()
