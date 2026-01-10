from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    session,
    flash,
    current_app,
)

# from database.mongodb_connector import add_user, check_login # No longer import directly
from forms import LoginForm, RegistrationForm
from decorators import login_required

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/signup", methods=["GET", "POST"])
def signup():
    form = RegistrationForm()
    if form.validate_on_submit():
        from database.mongodb_connector import (
            add_user,
        )  # Import here to avoid circular dependency

        users_col = current_app.config["USERS_COLLECTION"]

        # Pass age to add_user function
        add_user(
            users_col,
            form.username.data,
            form.password.data,
            form.role.data,
            form.age.data,
        )

        flash("Compte créé avec succès ! Veuillez vous connecter.", "success")
        return redirect(url_for("auth.login"))
    return render_template("signup.html", form=form)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        from database.mongodb_connector import (
            check_login,
        )  # Import here to avoid circular dependency

        users_col = current_app.config["USERS_COLLECTION"]
        user = check_login(users_col, form.username.data, form.password.data)
        if user:
            session["user"] = user
            session.permanent = True
            flash("Logged in successfully!", "success")
            return redirect(url_for("main.home"))
        flash("Invalid credentials. Please try again.", "error")
    return render_template("login.html", form=form)


@auth_bp.route("/logout")
@login_required
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))
