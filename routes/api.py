from flask import Blueprint, jsonify, current_app
from decorators import login_required, role_required

# from database.mongodb_connector import get_all_patients, get_analyses # No longer import directly

api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.route("/patients", methods=["GET"])
@login_required
@role_required("medecin")
def get_patients_api():
    users_col = current_app.config["USERS_COLLECTION"]
    from database.mongodb_connector import get_all_patients  # Import here

    patients = get_all_patients(users_col)  # Pass users_col
    # Convert ObjectId to string for JSON serialization
    for patient in patients:
        patient["_id"] = str(patient["_id"])
    return jsonify(patients)


@api_bp.route("/patient/<patient_id>/analyses", methods=["GET"])
@login_required
@role_required("medecin")
def get_patient_analyses_api(patient_id):
    analyses_col = current_app.config["ANALYSES_COLLECTION"]
    patients_col = current_app.config["PATIENTS_COLLECTION"]
    from database.mongodb_connector import get_analyses  # Import here

    analyses = get_analyses(patients_col, analyses_col, patient_id)  # Pass collections
    # Convert ObjectId to string for JSON serialization
    for analysis in analyses:
        analysis["_id"] = str(analysis["_id"])
        # analysis['patient_id'] = str(analysis['patient_id']) # patient_id is already in analysis.result
    return jsonify(analyses)
