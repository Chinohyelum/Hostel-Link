from extensions import get_db

def get_student_notifications(student_id):
    """
    Returns a combined list of swap + cancellation status updates.
    """
    db = get_db()

    cancellations = db.execute("""
        SELECT
            'cancellation' AS type,
            cr.id AS request_id,
            cr.status AS status,
            cr.created_at AS created_at,
            cr.decided_at AS decided_at,
            h.name AS hostel_name,
            r.room_number AS room_number,
            NULL AS requested_hostel_name,
            NULL AS requested_room_number,
            NULL AS requested_bunk_label
        FROM cancellation_requests cr
        JOIN rooms r ON r.id = cr.room_id
        JOIN hostels h ON h.id = r.hostel_id
        WHERE cr.student_id = ?
    """, (student_id,)).fetchall()

    # Swap requests: room A -> room B
    # If you created room_swap_details, we LEFT JOIN it for requested bunk label
    swaps = db.execute("""
        SELECT
            'swap' AS type,
            rs.id AS request_id,
            rs.status AS status,
            rs.created_at AS created_at,
            rs.decided_at AS decided_at,
            h1.name AS hostel_name,
            r1.room_number AS room_number,
            h2.name AS requested_hostel_name,
            r2.room_number AS requested_room_number,
            b.bunk_label AS requested_bunk_label
        FROM room_swap_requests rs
        JOIN rooms r1 ON r1.id = rs.current_room_id
        JOIN hostels h1 ON h1.id = r1.hostel_id
        JOIN rooms r2 ON r2.id = rs.requested_room_id
        JOIN hostels h2 ON h2.id = r2.hostel_id
        LEFT JOIN room_swap_details d ON d.swap_request_id = rs.id
        LEFT JOIN bunks b ON b.id = d.requested_bunk_id
        WHERE rs.student_id = ?
    """, (student_id,)).fetchall()

    # Combine + sort by most recent event time
    all_items = list(cancellations) + list(swaps)

    def sort_key(x):
        # show decided notifications first (latest decided), else created
        return (x["decided_at"] or x["created_at"] or 0)

    all_items.sort(key=sort_key, reverse=True)
    return all_items
