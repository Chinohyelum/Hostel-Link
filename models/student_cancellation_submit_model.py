from extensions import get_db

def get_student_active_room_id(student_id):
    """
    Uses bunks.occupied_by to find student's current room.
    Works even if bookings table changes.
    """
    db = get_db()
    row = db.execute("""
        SELECT room_id
        FROM bunks
        WHERE occupied = 1 AND occupied_by = ?
        LIMIT 1
    """, (student_id,)).fetchone()
    return row["room_id"] if row else None


def student_has_pending_cancellation(student_id):
    db = get_db()
    row = db.execute("""
        SELECT id FROM cancellation_requests
        WHERE student_id = ? AND status = 'pending'
        ORDER BY id DESC LIMIT 1
    """, (student_id,)).fetchone()
    return row is not None


def create_cancellation_request(student_id, room_id):
    db = get_db()

    if student_has_pending_cancellation(student_id):
        return False, "You already have a pending cancellation request."

    db.execute("""
        INSERT INTO cancellation_requests (student_id, room_id, status)
        VALUES (?, ?, 'pending')
    """, (student_id, room_id))
    db.commit()
    return True, "Cancellation request submitted to admin."


def get_student_cancellation_requests(student_id):
    db = get_db()
    return db.execute("""
        SELECT cr.*, r.room_number, h.name AS hostel_name
        FROM cancellation_requests cr
        JOIN rooms r ON r.id = cr.room_id
        JOIN hostels h ON h.id = r.hostel_id
        WHERE cr.student_id = ?
        ORDER BY cr.id DESC
    """, (student_id,)).fetchall()
