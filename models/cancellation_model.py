from extensions import get_db

def create_cancellation_table():
    db = get_db()
    db.execute("""
        CREATE TABLE IF NOT EXISTS cancellation_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            room_id INTEGER NOT NULL,
            status TEXT DEFAULT 'pending',      -- pending|approved|rejected
            created_at INTEGER DEFAULT (strftime('%s','now')),
            decided_at INTEGER
        )
    """)
    db.commit()
