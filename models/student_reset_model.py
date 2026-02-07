from extensions import get_db
from datetime import datetime, timedelta

def create_student_reset_table():
    db = get_db()
    db.execute("""
        CREATE TABLE IF NOT EXISTS student_password_resets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            token TEXT UNIQUE NOT NULL,
            expires_at TEXT NOT NULL,
            used INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    db.commit()

def create_reset_token(student_id, token, minutes_valid=30):
    db = get_db()
    expires_at = (datetime.now() + timedelta(minutes=minutes_valid)).isoformat()
    db.execute("""
        INSERT INTO student_password_resets (student_id, token, expires_at, used)
        VALUES (?, ?, ?, 0)
    """, (student_id, token, expires_at))
    db.commit()

def get_reset_by_token(token):
    db = get_db()
    return db.execute("""
        SELECT * FROM student_password_resets WHERE token = ?
    """, (token,)).fetchone()

def mark_token_used(reset_id):
    db = get_db()
    db.execute("UPDATE student_password_resets SET used = 1 WHERE id = ?", (reset_id,))
    db.commit()
