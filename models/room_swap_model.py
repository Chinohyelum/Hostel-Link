from extensions import get_db
import time

def create_room_swap_table():
    db = get_db()
    db.execute("""
        CREATE TABLE IF NOT EXISTS room_swap_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            current_room_id INTEGER NOT NULL,
            requested_room_id INTEGER NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at INTEGER DEFAULT (strftime('%s','now')),
            decided_at INTEGER
        )
    """)
    db.commit()
