from extensions import get_db

def student_has_pending_swap(student_id):
    db = get_db()
    row = db.execute("""
        SELECT id FROM room_swap_requests
        WHERE student_id = ? AND status = 'pending'
        ORDER BY id DESC LIMIT 1
    """, (student_id,)).fetchone()
    return row is not None

def create_room_swap_request(student_id, current_room_id, requested_room_id):
    db = get_db()

    if current_room_id == requested_room_id:
        return False, None, "You cannot request your current room."

    if student_has_pending_swap(student_id):
        return False, None, "You already have a pending swap request."

    db.execute("""
        INSERT INTO room_swap_requests (student_id, current_room_id, requested_room_id, status)
        VALUES (?, ?, ?, 'pending')
    """, (student_id, current_room_id, requested_room_id))
    db.commit()

    swap_id = db.execute("SELECT last_insert_rowid() AS id").fetchone()["id"]
    return True, swap_id, "Swap request submitted."
