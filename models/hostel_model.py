# models/hostel_model.py
import sqlite3
from extensions import get_db

# ---------------- CREATE HOSTEL TABLE ----------------

def create_hostel_table():
    db = get_db()
    db.execute("""
    CREATE TABLE IF NOT EXISTS hostels (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        gender TEXT,
        faculty TEXT,
        created_at INTEGER,
        image TEXT
    )
    """)
    db.commit()

    # ---------------- CREATE ROOMS TABLE ----------------

def create_room_table():
    db = get_db()
    db.execute("""
    CREATE TABLE IF NOT EXISTS rooms (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        hostel_id INTEGER NOT NULL,
        room_number TEXT NOT NULL,
        type TEXT,
        capacity INTEGER DEFAULT 1,
        FOREIGN KEY(hostel_id) REFERENCES hostels(id)
    )
    """)
    db.commit()

    # ---------------- CREATE BUNKS TABLE ----------------

def create_bunk_table():
    db = get_db()
    db.execute("""
    CREATE TABLE IF NOT EXISTS bunks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        room_id INTEGER NOT NULL,
        bunk_label TEXT NOT NULL,
        occupied INTEGER DEFAULT 0,
        FOREIGN KEY(room_id) REFERENCES rooms(id)
    )
    """)
    db.commit()
