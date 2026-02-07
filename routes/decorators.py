from functools import wraps
from flask import session, redirect, url_for, flash, request

def admin_login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "admin_id" not in session:
            flash("Please log in as admin to access this page.")
            return redirect(url_for("auth.login", next=request.path))
        return f(*args, **kwargs)
    return decorated_function

def student_login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "student_id" not in session:
            flash("Please log in as student to access this page.")
            return redirect(url_for("student.login_page", next=request.path))
        return f(*args, **kwargs)
    return decorated_function
