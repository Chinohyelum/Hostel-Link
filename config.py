import os

# import app

class Config:
    SECRET_KEY = "super-secret-key-change-this"
    DATABASE = os.path.join(os.path.abspath(os.path.dirname(__file__)), "database.db")
    SECRET_KEY = "hostel_link-secret-key"

# app.secret_key = "dev-secret"  # replace with config value


