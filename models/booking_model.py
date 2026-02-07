from extensions import get_db

def create_booking_table():
    db = get_db()
    db.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            hostel_id INTEGER NOT NULL,
            room_id INTEGER NOT NULL,
            bunk_id INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'active',   -- active | cancelled | completed
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    db.commit()


def ensure_bunk_booking_columns():
    """
    Your bunks table already has: occupied (0/1), bunk_label
    We'll optionally add occupied_by so you know who is in a bunk.
    This does NOT touch hostel_model.py. It only alters DB schema safely.
    """
    db = get_db()
    cols = db.execute("PRAGMA table_info(bunks)").fetchall()
    existing = {c["name"] for c in cols}

    if "occupied_by" not in existing:
        db.execute("ALTER TABLE bunks ADD COLUMN occupied_by INTEGER")
        db.commit()


# ---------- DATA FOR DROPDOWNS ----------
def get_all_hostels():
    db = get_db()
    return db.execute("SELECT id, name FROM hostels ORDER BY name").fetchall()

def get_rooms_by_hostel(hostel_id):
    db = get_db()
    return db.execute(
        "SELECT id, room_number FROM rooms WHERE hostel_id = ? ORDER BY room_number",
        (hostel_id,)
    ).fetchall()

def get_available_bunks_by_room(room_id):
    db = get_db()
    return db.execute("""
        SELECT id, bunk_label
        FROM bunks
        WHERE room_id = ?
          AND (occupied IS NULL OR occupied = 0)
        ORDER BY bunk_label
    """, (room_id,)).fetchall()


# ---------- RULE: ONE ACTIVE BOOKING PER STUDENT ----------
def student_has_active_booking(student_id):
    db = get_db()
    row = db.execute("""
        SELECT id FROM bookings
        WHERE student_id = ? AND status = 'active'
        ORDER BY id DESC LIMIT 1
    """, (student_id,)).fetchone()
    return row is not None


# ---------- BOOKING ----------
def create_booking(student_id, hostel_id, room_id, bunk_id):
    db = get_db()

    if student_has_active_booking(student_id):
        return False, "You already have an active booking."

    # confirm bunk belongs to room and is available
    bunk = db.execute("""
        SELECT id, occupied
        FROM bunks
        WHERE id = ? AND room_id = ?
    """, (bunk_id, room_id)).fetchone()

    if not bunk:
        return False, "Invalid bunk selection."

    if bunk["occupied"] == 1:
        return False, "That bunk is already taken. Please choose another."

    try:
        db.execute("BEGIN")

        # re-check inside transaction
        still_free = db.execute(
            "SELECT occupied FROM bunks WHERE id = ?",
            (bunk_id,)
        ).fetchone()

        if not still_free or still_free["occupied"] == 1:
            db.execute("ROLLBACK")
            return False, "That bunk was just taken. Please choose another."

        # create booking row
        db.execute("""
            INSERT INTO bookings (student_id, hostel_id, room_id, bunk_id, status)
            VALUES (?, ?, ?, ?, 'active')
        """, (student_id, hostel_id, room_id, bunk_id))

        # mark bunk occupied
        db.execute("""
            UPDATE bunks
            SET occupied = 1, occupied_by = ?
            WHERE id = ?
        """, (student_id, bunk_id))

        db.commit()
        return True, "Booking successful!"
    except Exception as e:
        db.execute("ROLLBACK")
        return False, f"Booking failed: {str(e)}"


def get_student_bookings(student_id):
    db = get_db()
    return db.execute("""
        SELECT b.id, b.status, b.created_at,
               h.name AS hostel_name,
               r.room_number,
               k.bunk_label
        FROM bookings b
        JOIN hostels h ON h.id = b.hostel_id
        JOIN rooms r   ON r.id = b.room_id
        JOIN bunks k   ON k.id = b.bunk_id
        WHERE b.student_id = ?
        ORDER BY b.id DESC
    """, (student_id,)).fetchall()


# To know student's current bunk, we can add a helper:
from extensions import get_db

def get_student_active_room_id(student_id):
    db = get_db()
    row = db.execute("""
        SELECT room_id
        FROM bookings
        WHERE student_id = ? AND status = 'active'
        ORDER BY id DESC LIMIT 1
    """, (student_id,)).fetchone()
    return row["room_id"] if row else None


# store current allocation
from extensions import get_db

def get_student_current_allocation(student_id):
    """
    Returns the student's active allocation:
    hostel_name, room_number, bunk_label, and IDs needed.
    Uses bookings table primarily, fallback to bunks.occupied_by if needed.
    """
    db = get_db()

    # 1) Prefer bookings table (your flow)
    row = db.execute("""
        SELECT b.id AS booking_id,
               h.name AS hostel_name,
               r.id AS room_id,
               r.room_number,
               k.id AS bunk_id,
               k.bunk_label
        FROM bookings b
        JOIN hostels h ON h.id = b.hostel_id
        JOIN rooms r   ON r.id = b.room_id
        JOIN bunks k   ON k.id = b.bunk_id
        WHERE b.student_id = ? AND b.status = 'active'
        ORDER BY b.id DESC
        LIMIT 1
    """, (student_id,)).fetchone()

    if row:
        return row

    # 2) Fallback: find bunk by occupied_by (if booking record missing)
    row = db.execute("""
        SELECT NULL AS booking_id,
               h.name AS hostel_name,
               r.id AS room_id,
               r.room_number,
               k.id AS bunk_id,
               k.bunk_label
        FROM bunks k
        JOIN rooms r ON r.id = k.room_id
        JOIN hostels h ON h.id = r.hostel_id
        WHERE k.occupied = 1 AND k.occupied_by = ?
        LIMIT 1
    """, (student_id,)).fetchone()

    return row
