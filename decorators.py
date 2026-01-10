from functools import wraps
from flask import session, redirect, url_for, flash


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            flash("You need to be logged in to access this page.", "warning")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)

    return decorated_function


def role_required(role):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if "user" not in session or session["user"]["role"] != role:
                flash(
                    f"You do not have the necessary permissions to access this page. Role '{role}' required.",
                    "danger",
                )
                return redirect(url_for("main.home"))  # Redirect to home or login
            return f(*args, **kwargs)

        return decorated_function

    return decorator


def admin_login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session or session["user"].get("role") != "admin":
            flash(
                "Vous devez être connecté en tant qu'administrateur pour accéder à cette page.",
                "warning",
            )
            return redirect(url_for("admin.login"))
        return f(*args, **kwargs)

    return decorated_function
