from extensions import get_db
from werkzeug.security import generate_password_hash
# from routes.admin_routes import admin_bp
import sqlite3


def create_admin_table():
    db = get_db()
    # Create table if it doesn't exist
    db.execute("""
    CREATE TABLE IF NOT EXISTS admins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name TEXT NOT NULL,
        last_name TEXT NOT NULL,
        nickname TEXT,
        email TEXT UNIQUE NOT NULL,
        role TEXT DEFAULT 'admin',
        password TEXT NOT NULL,
        profile_picture TEXT,
        created_at INTEGER DEFAULT (strftime('%s','now'))
    )
    """)
    db.commit()



def seed_default_admin():
    db = get_db()

    admin = db.execute("SELECT * FROM admins LIMIT 1").fetchone()

    if not admin:
        db.execute("""
        INSERT INTO admins (first_name, last_name, nickname, email, password)
        VALUES (?, ?, ?, ?, ?)
        """, (
            "Chinonye",
            "Obieze",
            "Hostel Officer",
            "chinonyeobieze3@gmail.com",
            generate_password_hash("admin123")
        ))
        db.commit()
        print("Default Admin Created")
    else:
        print("Admin already exists")