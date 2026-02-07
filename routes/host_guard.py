from flask import request, redirect, url_for, session

def enforce_subdomain_rules():
    host = (request.host or "").split(":")[0].lower()

    # allow local dev
    if host in ("127.0.0.1", "localhost"):
        return None

    # You will set these env vars on Render
    admin_host = (request.environ.get("ADMIN_HOST") or "").lower()
    student_host = (request.environ.get("STUDENT_HOST") or "").lower()

    path = request.path or ""

    # Admin pages must be on admin host
    if path.startswith("/admin") or path.startswith("/hostels") or path.startswith("/dashboard") or path.startswith("/api") or path.startswith("/room-swap") or path.startswith("/cancellations"):
        if admin_host and host != admin_host:
            return redirect(f"https://{admin_host}{path}")

    # Student pages must be on student host
    if path.startswith("/student"):
        if student_host and host != student_host:
            return redirect(f"https://{student_host}{path}")

    # Login pages: force correct host based on intent
    # If someone hits "/" on admin host -> admin login
    # If someone hits "/" on student host -> student login
    if path == "/":
        if admin_host and host == admin_host:
            return redirect(url_for("auth.login"))        # admin login endpoint
        if student_host and host == student_host:
            return redirect(url_for("student.login_page")) # student login endpoint

    return None
