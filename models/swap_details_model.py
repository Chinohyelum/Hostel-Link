from extensions import get_db

def create_swap_details_table():
    db = get_db()
    db.execute("""
        CREATE TABLE IF NOT EXISTS room_swap_details (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            swap_request_id INTEGER NOT NULL UNIQUE,
            requested_bunk_id INTEGER NOT NULL,
            reason TEXT,
            created_at INTEGER DEFAULT (strftime('%s','now')),
            FOREIGN KEY(swap_request_id) REFERENCES room_swap_requests(id)
        )
    """)
    db.commit()

def save_swap_details(swap_request_id, requested_bunk_id, reason=""):
    db = get_db()
    db.execute("""
        INSERT OR REPLACE INTO room_swap_details (swap_request_id, requested_bunk_id, reason)
        VALUES (?, ?, ?)
    """, (swap_request_id, requested_bunk_id, reason.strip()))
    db.commit()

def get_swap_details_by_request_id(swap_request_id):
    db = get_db()
    return db.execute("""
        SELECT d.*, b.bunk_label, r.room_number, h.name AS hostel_name
        FROM room_swap_details d
        JOIN bunks b ON b.id = d.requested_bunk_id
        JOIN rooms r ON r.id = b.room_id
        JOIN hostels h ON h.id = r.hostel_id
        WHERE d.swap_request_id = ?
    """, (swap_request_id,)).fetchone()
