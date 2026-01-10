from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, DuplicateKeyError, OperationFailure
from bson.objectid import ObjectId
import os
import bcrypt
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
client = None
db = None

patients_col = None
analyses_col = None
users_col = None


def connect_to_mongodb():
    """Establishes connection to MongoDB and returns the collections."""
    try:
        client = MongoClient(MONGO_URI)
        db = client["tremblements_db"]

        users_col = db["users"]
        patients_col = db["patients"]
        analyses_col = db["analyses"]

        users_col.create_index("username", unique=True)
        analyses_col.create_index("patient_id")

        logger.info(
            "Successfully connected to MongoDB and initialized collections/indexes."
        )
        return users_col, patients_col, analyses_col  # Return the collections
    except ConnectionFailure as e:
        logger.error(f"Could not connect to MongoDB: {e}")
        return None, None, None
    except Exception as e:
        logger.error(
            f"An unexpected error occurred during MongoDB connection setup: {e}"
        )
        return None, None, None


# The automatic call to connect_to_mongodb() on import is removed here.


# Ajouter patient
def add_patient(patients_col, nom, age, sexe):
    try:
        patient = {"nom": nom, "age": age, "sexe": sexe, "historique": []}
        result = patients_col.insert_one(patient)
        logger.info(f"Patient '{nom}' added with ID: {result.inserted_id}")
        return result.inserted_id
    except OperationFailure as e:
        logger.error(f"MongoDB operation failed while adding patient: {e}")
        return None
    except Exception as e:
        logger.error(f"An unexpected error occurred while adding patient: {e}")
        return None


# Ajouter analyse
def add_analysis(analyses_col, patients_col, patient_id, analysis_data):
    try:
        if not isinstance(patient_id, ObjectId):
            patient_id = ObjectId(patient_id)

        result_analysis = analyses_col.insert_one(analysis_data)
        analysis_id = result_analysis.inserted_id

        patients_col.update_one(
            {"_id": patient_id}, {"$push": {"historique": analysis_id}}
        )
        logger.info(f"Analysis {analysis_id} added for patient {patient_id}")
        return analysis_id
    except OperationFailure as e:
        logger.error(f"MongoDB operation failed while adding analysis: {e}")
        return None
    except Exception as e:
        logger.error(f"An unexpected error occurred while adding analysis: {e}")
        return None


# Récupérer analyses par patient
def get_analyses(patients_col, analyses_col, patient_id):
    try:
        if not isinstance(patient_id, ObjectId):
            patient_id = ObjectId(patient_id)

        patient = patients_col.find_one({"_id": patient_id})
        if not patient or "historique" not in patient:
            return []

        analyses = analyses_col.find({"_id": {"$in": patient["historique"]}}).sort(
            "result.date", -1
        )
        return list(analyses)
    except OperationFailure as e:
        logger.error(
            f"MongoDB operation failed while getting analyses for patient {patient_id}: {e}"
        )
        return []
    except Exception as e:
        logger.error(
            f"An unexpected error occurred while getting analyses for patient {patient_id}: {e}"
        )
        return []


# Liste patients (this is actually list_all_patients, not just patients with role 'patient')
def list_patients(patients_col):
    try:
        return list(patients_col.find())
    except OperationFailure as e:
        logger.error(f"MongoDB operation failed while listing patients: {e}")
        return []
    except Exception as e:
        logger.error(f"An unexpected error occurred while listing patients: {e}")
        return []


# Ajouter un utilisateur
def add_user(users_col, username, password, role="patient", age=None):
    try:
        hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
        user = {
            "username": username,
            "password": hashed_password,
            "role": role,
            "age": age,
        }
        result = users_col.insert_one(user)
        logger.info(f"User '{username}' added with ID: {result.inserted_id}")
        return result.inserted_id
    except DuplicateKeyError:
        logger.warning(f"Attempted to add duplicate username: {username}")
        return None  # Indicate that user already exists
    except OperationFailure as e:
        logger.error(f"MongoDB operation failed while adding user: {e}")
        return None
    except Exception as e:
        logger.error(f"An unexpected error occurred while adding user: {e}")
        return None


# Vérifier login
def check_login(users_col, username, password):
    try:
        user = users_col.find_one({"username": username})
        if user and bcrypt.checkpw(password.encode("utf-8"), user["password"]):
            logger.info(f"User '{username}' logged in successfully.")
            return {
                "_id": str(user["_id"]),
                "username": user["username"],
                "role": user["role"],
            }
        logger.warning(f"Failed login attempt for username: {username}")
        return None
    except OperationFailure as e:
        logger.error(
            f"MongoDB operation failed during login check for '{username}': {e}"
        )
        return None
    except Exception as e:
        logger.error(
            f"An unexpected error occurred during login check for '{username}': {e}"
        )
        return None


# Vérifier si le nom d'utilisateur existe déjà
def check_username_exists(users_col, username):
    try:
        return users_col.find_one({"username": username}) is not None
    except OperationFailure as e:
        logger.error(
            f"MongoDB operation failed while checking username existence for '{username}': {e}"
        )
        return False  # Assume it doesn't exist or handle as an error
    except Exception as e:
        logger.error(
            f"An unexpected error occurred while checking username existence for '{username}': {e}"
        )
        return False


# Récupérer tous les patients (pour le medecin)
def get_all_patients(users_col):
    try:
        return list(users_col.find({"role": "patient"}))
    except OperationFailure as e:
        logger.error(f"MongoDB operation failed while getting all patients: {e}")
        return []
    except Exception as e:
        logger.error(f"An unexpected error occurred while getting all patients: {e}")
        return []


def get_all_doctors(users_col):
    """Fetches all users with the 'medecin' role."""
    try:
        return list(users_col.find({"role": "medecin"}))
    except OperationFailure as e:
        logger.error(f"MongoDB operation failed while getting all doctors: {e}")
        return []
    except Exception as e:
        logger.error(f"An unexpected error occurred while getting all doctors: {e}")
        return []


def get_patients_for_doctor(users_col, doctor_id, sort_by="username", order=1):
    """Fetches all patients assigned to a specific doctor, with sorting."""
    try:
        if not isinstance(doctor_id, ObjectId):
            doctor_id = ObjectId(doctor_id)

        cursor = users_col.find(
            {"role": "patient", "assigned_doctor_id": doctor_id}
        ).sort(sort_by, order)

        return list(cursor)
    except OperationFailure as e:
        logger.error(
            f"MongoDB operation failed while getting patients for doctor {doctor_id}: {e}"
        )
        return []
    except Exception as e:
        logger.error(
            f"An unexpected error occurred while getting patients for doctor {doctor_id}: {e}"
        )
        return []


def check_admin_exists(users_col):
    """Checks if any user with the 'admin' role exists."""
    try:
        return users_col.find_one({"role": "admin"}) is not None
    except OperationFailure as e:
        logger.error(f"MongoDB operation failed while checking for admin: {e}")
        return False  # Assume no admin on error to be safe
    except Exception as e:
        logger.error(f"An unexpected error occurred while checking for admin: {e}")
        return False


def assign_doctor_to_patient(users_col, patient_id, doctor_id):
    """Assigns a doctor to a patient by storing the doctor's ID in the patient's user document."""
    try:
        if not isinstance(patient_id, ObjectId):
            patient_id = ObjectId(patient_id)

        # Ensure doctor_id is also an ObjectId if it's not null
        if doctor_id and not isinstance(doctor_id, ObjectId):
            doctor_id = ObjectId(doctor_id)

        result = users_col.update_one(
            {"_id": patient_id, "role": "patient"},
            {"$set": {"assigned_doctor_id": doctor_id}},
        )
        if result.modified_count > 0:
            logger.info(
                f"Successfully assigned doctor {doctor_id} to patient {patient_id}"
            )
            return True
        # If modified_count is 0, it could be that the value was the same, or patient not found.
        # We can consider this not an error.
        logger.warning(
            f"Doctor assignment for patient {patient_id} resulted in no changes. (Already assigned?)"
        )
        return True

    except OperationFailure as e:
        logger.error(f"MongoDB operation failed while assigning doctor: {e}")
        return False
    except Exception as e:
        logger.error(f"An unexpected error occurred while assigning doctor: {e}")
        return False


# Récupérer une analyse spécifique par ID
def get_analysis_by_id(analyses_col, analysis_id):
    try:
        if not isinstance(analysis_id, ObjectId):
            analysis_id = ObjectId(analysis_id)
        return analyses_col.find_one({"_id": analysis_id})
    except OperationFailure as e:
        logger.error(
            f"MongoDB operation failed while getting analysis by ID {analysis_id}: {e}"
        )
        return None
    except Exception as e:
        logger.error(
            f"An unexpected error occurred while getting analysis by ID {analysis_id}: {e}"
        )
        return None


def get_latest_analysis_for_patient(analyses_col, patient_id):
    """Fetches the most recent analysis for a single patient."""
    try:
        if not isinstance(patient_id, ObjectId):
            patient_id = ObjectId(patient_id)
        # Assuming 'result.date' is a field that can be sorted.
        # The date format must be consistent (e.g., ISO 8601) for correct sorting.
        latest = analyses_col.find_one(
            {
                "patient_id": str(patient_id)
            },  # In tasks.py, patient_id is stored as string
            sort=[("result.date", -1)],
        )
        return latest
    except OperationFailure as e:
        logger.error(
            f"MongoDB operation failed while getting latest analysis for patient {patient_id}: {e}"
        )
        return None
    except Exception as e:
        logger.error(
            f"An unexpected error occurred while getting latest analysis for patient {patient_id}: {e}"
        )
        return None


# --- New Admin-related functions ---


def get_user_by_id(users_col, user_id):
    try:
        if not isinstance(user_id, ObjectId):
            user_id = ObjectId(user_id)
        return users_col.find_one({"_id": user_id})
    except OperationFailure as e:
        logger.error(
            f"MongoDB operation failed while getting user by ID {user_id}: {e}"
        )
        return None
    except Exception as e:
        logger.error(
            f"An unexpected error occurred while getting user by ID {user_id}: {e}"
        )
        return None


def update_user_role(users_col, user_id, new_role):
    try:
        if not isinstance(user_id, ObjectId):
            user_id = ObjectId(user_id)
        result = users_col.update_one({"_id": user_id}, {"$set": {"role": new_role}})
        if result.modified_count > 0:
            logger.info(f"User {user_id} role updated to {new_role}.")
            return True
        return False
    except OperationFailure as e:
        logger.error(
            f"MongoDB operation failed while updating user {user_id} role: {e}"
        )
        return False
    except Exception as e:
        logger.error(
            f"An unexpected error occurred while updating user {user_id} role: {e}"
        )
        return False


def delete_user(users_col, user_id):
    try:
        if not isinstance(user_id, ObjectId):
            user_id = ObjectId(user_id)
        result = users_col.delete_one({"_id": user_id})
        if result.deleted_count > 0:
            logger.info(f"User {user_id} deleted.")
            return True
        return False
    except OperationFailure as e:
        logger.error(f"MongoDB operation failed while deleting user {user_id}: {e}")
        return False
    except Exception as e:
        logger.error(f"An unexpected error occurred while deleting user {user_id}: {e}")
        return False


def get_all_users(users_col):
    try:
        return list(users_col.find({}))
    except OperationFailure as e:
        logger.error(f"MongoDB operation failed while getting all users: {e}")
        return []
    except Exception as e:
        logger.error(f"An unexpected error occurred while getting all users: {e}")
        return []


def get_all_analyses(analyses_col):
    try:
        return list(analyses_col.find({}).sort("result.date", -1))
    except OperationFailure as e:
        logger.error(f"MongoDB operation failed while getting all analyses: {e}")
        return []
    except Exception as e:
        logger.error(f"An unexpected error occurred while getting all analyses: {e}")
        return []
