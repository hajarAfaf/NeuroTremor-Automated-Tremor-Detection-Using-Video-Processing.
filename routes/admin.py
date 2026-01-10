from flask import (
    Blueprint,
    render_template,
    flash,
    redirect,
    url_for,
    current_app,
    session,
)
from decorators import admin_login_required
from forms import AddDoctorForm, AdminLoginForm, AdminRegistrationForm, AssignDoctorForm
from database.mongodb_connector import (
    add_user,
    get_all_doctors,
    get_all_patients,
    get_user_by_id,
    get_analyses,
    check_login,
    check_admin_exists,
    assign_doctor_to_patient,
)

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/register", methods=["GET", "POST"])
def register():
    """
    Handles the registration of the first admin user.
    This page is only accessible if no admin user exists.
    """
    users_col = current_app.config["USERS_COLLECTION"]
    if check_admin_exists(users_col):
        flash(
            "Un compte administrateur existe déjà. L'inscription est désactivée.",
            "warning",
        )
        return redirect(url_for("admin.login"))

    form = AdminRegistrationForm()
    if form.validate_on_submit():
        user_id = add_user(
            users_col, form.username.data, form.password.data, role="admin"
        )
        if user_id:
            flash(
                "Compte administrateur créé avec succès. Veuillez vous connecter.",
                "success",
            )
            return redirect(url_for("admin.login"))
        else:
            flash("Une erreur est survenue lors de la création du compte.", "danger")

    return render_template("admin/register.html", form=form)


@admin_bp.route("/login", methods=["GET", "POST"])
def login():
    """
    Handles the login for admin users.
    """
    form = AdminLoginForm()
    if form.validate_on_submit():
        users_col = current_app.config["USERS_COLLECTION"]
        user = check_login(users_col, form.username.data, form.password.data)

        if user and user.get("role") == "admin":
            session["user"] = user
            session.permanent = True
            flash("Connecté en tant qu'administrateur.", "success")
            return redirect(url_for("admin.dashboard"))
        else:
            flash("Accès non autorisé ou identifiants invalides.", "danger")

    return render_template("admin/login.html", form=form)


@admin_bp.route("/dashboard")
@admin_login_required
def dashboard():
    """
    Displays the main admin dashboard.
    Accessible only by users with the 'admin' role.
    """
    return render_template("admin/dashboard.html")


@admin_bp.route("/add_doctor", methods=["GET", "POST"])
@admin_login_required
def add_doctor():
    """
    Provides a form for admins to add a new doctor (user with 'medecin' role).
    """
    form = AddDoctorForm()
    if form.validate_on_submit():
        users_col = current_app.config["USERS_COLLECTION"]
        user_id = add_user(
            users_col, form.username.data, form.password.data, role="medecin"
        )
        if user_id:
            flash(
                f"Le médecin '{form.username.data}' a été ajouté avec succès.",
                "success",
            )
            return redirect(url_for("admin.doctors_list"))
        else:
            flash("Une erreur est survenue lors de l'ajout du médecin.", "danger")

    return render_template("admin/add_doctor.html", form=form)


@admin_bp.route("/doctors")
@admin_login_required
def doctors_list():
    """
    Displays a list of all doctors.
    """
    users_col = current_app.config["USERS_COLLECTION"]
    doctors = get_all_doctors(users_col)
    return render_template("admin/doctors_list.html", doctors=doctors)


@admin_bp.route("/patients")
@admin_login_required
def patients_list():
    """
    Displays a list of all patients.
    """
    users_col = current_app.config["USERS_COLLECTION"]
    patients = get_all_patients(users_col)
    # For each patient, we want to fetch their assigned doctor's name
    patients_with_doctors = []
    for patient in patients:
        doctor_name = "Non assigné"
        if patient.get("assigned_doctor_id"):
            doctor = get_user_by_id(users_col, patient["assigned_doctor_id"])
            if doctor:
                doctor_name = doctor["username"]
        patients_with_doctors.append({**patient, "doctor_name": doctor_name})

    return render_template("admin/patients_list.html", patients=patients_with_doctors)


@admin_bp.route("/patient/<user_id>")
@admin_login_required
def patient_details(user_id):
    """
    Displays the details and analysis history for a specific patient.
    """
    users_col = current_app.config["USERS_COLLECTION"]
    patients_col = current_app.config["PATIENTS_COLLECTION"]
    analyses_col = current_app.config["ANALYSES_COLLECTION"]

    patient = get_user_by_id(users_col, user_id)
    if not patient or patient.get("role") != "patient":
        flash("Patient non trouvé.", "danger")
        return redirect(url_for("admin.patients_list"))

    # Here, we use the user_id as the patient_id, following the app's logic
    analyses = get_analyses(patients_col, analyses_col, user_id)

    return render_template(
        "admin/patient_details.html", patient=patient, analyses=analyses
    )


@admin_bp.route("/assign_doctor/<patient_id>", methods=["GET", "POST"])
@admin_login_required
def assign_doctor(patient_id):
    """
    Handles assigning a doctor to a patient.
    """
    users_col = current_app.config["USERS_COLLECTION"]
    patient = get_user_by_id(users_col, patient_id)

    if not patient or patient.get("role") != "patient":
        flash("Patient non trouvé.", "danger")
        return redirect(url_for("admin.patients_list"))

    form = AssignDoctorForm()
    doctors = get_all_doctors(users_col)
    # Populate choices for the select field
    form.doctor.choices = [(str(d["_id"]), d["username"]) for d in doctors]
    # Add an option for 'unassign'
    form.doctor.choices.insert(0, ("", "Non assigné"))

    if form.validate_on_submit():
        doctor_id = form.doctor.data or None  # Set to None if empty string
        if assign_doctor_to_patient(users_col, patient_id, doctor_id):
            doctor_name = "personne"
            if doctor_id:
                # Find the doctor's name for the flash message
                selected_doctor = next(
                    (d for d in doctors if str(d["_id"]) == doctor_id), None
                )
                if selected_doctor:
                    doctor_name = selected_doctor["username"]

            flash(
                f"Le patient '{patient['username']}' a été assigné à '{doctor_name}'.",
                "success",
            )
        else:
            flash("Erreur lors de l'assignation du médecin.", "danger")

        return redirect(url_for("admin.patients_list"))

    # Pre-select the currently assigned doctor in the form
    if patient.get("assigned_doctor_id"):
        form.doctor.data = str(patient["assigned_doctor_id"])

    return render_template("admin/assign_doctor.html", form=form, patient=patient)
