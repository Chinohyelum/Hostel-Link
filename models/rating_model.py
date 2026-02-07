from extensions import get_db

def create_ratings_table():
    db = get_db()
    db.execute("""
        CREATE TABLE IF NOT EXISTS ratings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            hostel_id INTEGER NOT NULL,
            room_id INTEGER,
            rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
            comment TEXT,
            created_at INTEGER DEFAULT (strftime('%s','now')),
            updated_at INTEGER
        )
    """)
    db.commit()

def get_student_current_allocation_ids(student_id):
    """
    Gets hostel_id and room_id from the student's active booking.
    """
    db = get_db()
    return db.execute("""
        SELECT hostel_id, room_id
        FROM bookings
        WHERE student_id = ? AND status = 'active'
        ORDER BY id DESC LIMIT 1
    """, (student_id,)).fetchone()

def upsert_rating(student_id, hostel_id, room_id, rating, comment):
    """
    One rating per student per hostel + room combination.
    (hostel-only rating uses room_id NULL)
    """
    db = get_db()

    # Normalize comment
    comment = (comment or "").strip()

    existing = db.execute("""
        SELECT id FROM ratings
        WHERE student_id = ?
          AND hostel_id = ?
          AND (
                (room_id IS NULL AND ? IS NULL)
                OR (room_id = ?)
              )
        LIMIT 1
    """, (student_id, hostel_id, room_id, room_id)).fetchone()

    if existing:
        db.execute("""
            UPDATE ratings
            SET rating = ?, comment = ?, updated_at = (strftime('%s','now'))
            WHERE id = ?
        """, (rating, comment, existing["id"]))
        db.commit()
        return True, "Rating updated successfully."
    else:
        db.execute("""
            INSERT INTO ratings (student_id, hostel_id, room_id, rating, comment)
            VALUES (?, ?, ?, ?, ?)
        """, (student_id, hostel_id, room_id, rating, comment))
        db.commit()
        return True, "Rating submitted successfully."

def get_student_ratings(student_id):
    db = get_db()
    return db.execute("""
        SELECT rt.*,
               h.name AS hostel_name,
               r.room_number
        FROM ratings rt
        JOIN hostels h ON h.id = rt.hostel_id
        LEFT JOIN rooms r ON r.id = rt.room_id
        WHERE rt.student_id = ?
        ORDER BY rt.id DESC
    """, (student_id,)).fetchall()

def get_hostel_rating_summary(hostel_id):
    db = get_db()
    return db.execute("""
        SELECT COUNT(*) AS total,
               ROUND(AVG(rating), 2) AS avg_rating
        FROM ratings
        WHERE hostel_id = ?
    """, (hostel_id,)).fetchone()

def get_room_rating_summary(room_id):
    db = get_db()
    return db.execute("""
        SELECT COUNT(*) AS total,
               ROUND(AVG(rating), 2) AS avg_rating
        FROM ratings
        WHERE room_id = ?
    """, (room_id,)).fetchone()
