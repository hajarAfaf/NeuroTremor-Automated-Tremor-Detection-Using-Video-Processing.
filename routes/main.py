from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    current_app,
)
import os

# from database.mongodb_connector import ( # No longer import directly
#     get_all_patients,
#     add_analysis,
#     get_analyses
# )
from decorators import login_required, role_required
from tasks import analyze_video_task  # Import the Celery task

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
@login_required
def home():
    user = session.get("user")
    if user:
        if user["role"] == "medecin":
            return redirect(url_for("main.dashboard"))
        else:
            return redirect(url_for("main.patient_home"))
    return redirect(url_for("auth.login"))


@main_bp.route("/patient", methods=["GET", "POST"])
@login_required
@role_required("patient")
def patient_home():
    user = session.get("user")
    users_col = current_app.config["USERS_COLLECTION"]
    from database.mongodb_connector import get_user_by_id, get_analyses  # Import here

    # Fetch assigned doctor's details
    doctor_name = None
    if user.get("assigned_doctor_id"):
        doctor = get_user_by_id(users_col, user["assigned_doctor_id"])
        if doctor:
            doctor_name = doctor["username"]

    # Get collections from app.config
    analyses_col = current_app.config["ANALYSES_COLLECTION"]
    patients_col = current_app.config["PATIENTS_COLLECTION"]

    if request.method == "POST":
        video = request.files.get("video")
        age = int(request.form.get("age", 60))

        if video:
            video_path = os.path.join(
                current_app.config["UPLOAD_FOLDER"], video.filename
            )
            video.save(video_path)

            # Call the Celery task asynchronously
            # The task will now receive the collection objects
            analyze_video_task.delay(video_path, age, str(user["_id"]))
            flash(
                "Vidéo soumise pour analyse. Les résultats apparaîtront sur cette page une fois prêts.",
                "info",
            )
            return redirect(url_for("main.patient_home"))
        else:
            flash("Aucun fichier vidéo n'a été sélectionné.", "error")
            return redirect(url_for("main.patient_home"))

    # Fetch patient's analyses
    patient_analyses = get_analyses(patients_col, analyses_col, str(user["_id"]))

    return render_template(
        "patient_home.html",
        user=user,
        doctor_name=doctor_name,
        analyses=patient_analyses,
    )


@main_bp.route("/dashboard")
@login_required
@role_required("medecin")
def dashboard():
    user = session.get("user")
    doctor_id = user["_id"]

    # --- Sorting Logic ---
    sort_by = request.args.get("sort_by", "username")
    order = request.args.get("order", "asc")

    # Determine the database sort order
    db_order = 1 if order == "asc" else -1

    # Define valid sort fields for direct DB query
    db_sort_fields = ["username", "age"]

    # --- Data Fetching ---
    users_col = current_app.config["USERS_COLLECTION"]
    analyses_col = current_app.config["ANALYSES_COLLECTION"]
    from database.mongodb_connector import (
        get_patients_for_doctor,
        get_latest_analysis_for_patient,
    )

    # If sorting by a direct DB field, do it here
    db_sort_param = sort_by if sort_by in db_sort_fields else "username"
    patients = get_patients_for_doctor(
        users_col, doctor_id, sort_by=db_sort_param, order=db_order
    )

    # --- Augmenting with Latest Analysis ---
    patients_with_details = []
    severity_map = {"Normal": 0, "Léger": 1, "Modéré": 2, "Sévère": 3}

    for patient in patients:
        latest_analysis = get_latest_analysis_for_patient(analyses_col, patient["_id"])
        severity = "N/A"
        severity_score = -1
        if (
            latest_analysis
            and "result" in latest_analysis
            and "severity" in latest_analysis["result"]
        ):
            severity = latest_analysis["result"]["severity"]
            severity_score = severity_map.get(severity, -1)

        patient_details = {
            **patient,
            "latest_severity": severity,
            "severity_score": severity_score,
        }
        patients_with_details.append(patient_details)

    # --- Post-fetch Sorting for Severity ---
    if sort_by == "severity":
        patients_with_details.sort(
            key=lambda p: p["severity_score"], reverse=(order == "desc")
        )

    # --- Prepare data for template ---
    sort_info = {"by": sort_by, "order": order}

    return render_template(
        "dashboard.html", patients=patients_with_details, user=user, sort_info=sort_info
    )


@main_bp.route("/dashboard/<patient_id>")
@login_required
@role_required("medecin")
def patient_history(patient_id):
    user = session.get("user")
    doctor_id = user["_id"]

    # Get collections from app.config
    users_col = current_app.config["USERS_COLLECTION"]
    analyses_col = current_app.config["ANALYSES_COLLECTION"]
    patients_col = current_app.config["PATIENTS_COLLECTION"]
    from database.mongodb_connector import get_analyses, get_user_by_id  # Import here

    # Security Check: Ensure the requested patient is assigned to the logged-in doctor
    patient = get_user_by_id(users_col, patient_id)
    if not patient or str(patient.get("assigned_doctor_id")) != doctor_id:
        flash("Accès non autorisé à ce patient.", "danger")
        return redirect(url_for("main.dashboard"))

    analyses = get_analyses(patients_col, analyses_col, patient_id)  # Pass collections
    return render_template(
        "history.html",
        sessions=analyses,
        user=user,
        patient_id=patient_id,  # Ensure patient_id is passed to template
        patient_name=patient["username"],  # Pass patient name for display
    )


@main_bp.route("/my_history")
@login_required
@role_required("patient")
def my_history():
    """
    Displays the analysis history for the currently logged-in patient.
    """
    user = session.get("user")
    patient_id = user["_id"]

    analyses_col = current_app.config["ANALYSES_COLLECTION"]
    patients_col = current_app.config["PATIENTS_COLLECTION"]
    from database.mongodb_connector import get_analyses

    analyses = get_analyses(patients_col, analyses_col, patient_id)

    return render_template("my_history.html", sessions=analyses, user=user)


@main_bp.route("/result/<analysis_id>")
@login_required
def result(analysis_id):
    # Get collections from app.config
    analyses_col = current_app.config["ANALYSES_COLLECTION"]
    from database.mongodb_connector import get_analysis_by_id  # Import here

    analysis = get_analysis_by_id(analyses_col, analysis_id)  # Pass analyses_col
    if not analysis:
        flash("Analysis not found.", "error")
        return redirect(url_for("main.home"))  # Or appropriate error page

    # Assuming analysis has a 'result' field with amplitude, frequency, etc.
    # And a 'patient_id' field
    results_data = {
        "amplitude": analysis.get("result", {}).get("amplitude"),
        "frequency": analysis.get("result", {}).get("frequency"),
        "tremor_type": analysis.get("result", {}).get("tremor_type"),
        "severity": analysis.get("result", {}).get("severity"),
        "alert": analysis.get("result", {}).get("alert"),
        "graph": analysis.get("result", {}).get(
            "graph_path"
        ),  # Assuming graph path is stored here
        "patient_id": str(
            analysis.get("patient_id")
        ),  # Pass patient_id for back button
    }
    return render_template("result.html", results=results_data)
