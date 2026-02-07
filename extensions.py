import sqlite3
from flask import g, current_app
import time
import os
from werkzeug.utils import secure_filename
from config import Config

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(Config.DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db

    # The next line is only for debugging - it will print the path to the database file being used.
    print("DB PATH:", os.path.abspath(DATABASE))


def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


        # -------------------  CREATING FOR FILE SAVING ----------------------------


# Allowed image formats
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def save_file(file, folder="profile_pics"):
    """
    Saves uploaded file into /static/uploads/<folder>/
    Returns relative path to store in database
    """

    if file is None or file.filename == "":
        return None

    if not allowed_file(file.filename):
        return None

    # Create uploads directory if it doesn't exist
    upload_path = os.path.join(current_app.root_path, "static", "uploads", folder)
    os.makedirs(upload_path, exist_ok=True)

    # Unique filename (prevents overwrite)
    filename = secure_filename(file.filename)
    ext = filename.rsplit(".", 1)[1].lower()
    unique_name = f"{int(time.time())}.{ext}"

    full_path = os.path.join(upload_path, unique_name)
    file.save(full_path)

    # Path stored in DB (relative to static)
    return f"uploads/{folder}/{unique_name}"