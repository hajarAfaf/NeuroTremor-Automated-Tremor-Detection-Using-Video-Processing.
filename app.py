from flask import Flask, render_template, request, redirect, url_for, session
import os

from analysis.video_analysis import analyze_video
from database.mongodb_connector import (
    add_user,
    check_login,
    get_all_patients,
    add_analysis,
    list_patients,
    get_analyses
)

# =====================
# CONFIG
# =====================
app = Flask(__name__)
app.secret_key = "secret123"

UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


# =====================
# ROUTE RACINE
# =====================
@app.route("/")
def home():
    user = session.get("user")
    if user:
        if user["role"] == "medecin":
            return redirect(url_for("dashboard"))
        else:
            return redirect(url_for("patient_home"))
    return redirect(url_for("login"))


# =====================
# INSCRIPTION
# =====================
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        add_user(
            request.form["username"],
            request.form["password"],
            request.form["role"]
        )
        return redirect(url_for("login"))
    return render_template("signup.html")


# =====================
# LOGIN
# =====================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = check_login(
            request.form["username"],
            request.form["password"]
        )
        if user:
            session["user"] = user
            return redirect(url_for("home"))
        return render_template("login.html", error="Identifiants incorrects")
    return render_template("login.html")


# =====================
# LOGOUT
# =====================
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# =====================
# ESPACE PATIENT
# =====================
@app.route("/patient", methods=["GET", "POST"])
def patient_home():
    user = session.get("user")

    if not user or user["role"] != "patient":
        return redirect(url_for("login"))

    if request.method == "POST":
        video = request.files.get("video")
        age = int(request.form.get("age", 60))

        if video:
            video_path = os.path.join(app.config["UPLOAD_FOLDER"], video.filename)
            video.save(video_path)

            result = analyze_video(video_path, patient_age=age)
            add_analysis(user["_id"], result)

            return render_template(
                "result.html",
                results=result,
                user=user
            )

    return render_template("patient_home.html", user=user)


# =====================
# DASHBOARD MEDECIN
# =====================
@app.route("/dashboard")
def dashboard():
    user = session.get("user")

    if not user or user["role"] != "medecin":
        return redirect(url_for("login"))

    patients = get_all_patients()
    return render_template(
        "dashboard.html",
        patients=patients,
        user=user
    )


# =====================
# HISTORIQUE PATIENT (MEDECIN)
# =====================
@app.route("/dashboard/<patient_id>")
def patient_history(patient_id):
    user = session.get("user")

    if not user or user["role"] != "medecin":
        return redirect(url_for("login"))

    analyses = get_analyses(patient_id)
    return render_template(
        "history.html",
        sessions=analyses,
        user=user
    )


# =====================
# RUN
# =====================
if __name__ == "__main__":
    app.run(debug=True)
