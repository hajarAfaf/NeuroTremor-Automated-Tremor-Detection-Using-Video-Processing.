from pymongo import MongoClient
from bson.objectid import ObjectId
import os

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
client = MongoClient(MONGO_URI)
db = client["tremblements_db"]
patients_col = db["patients"]
analyses_col = db["analyses"]
users_col = db["users"]
# Ajouter patient
def add_patient(nom, age, sexe):
    patient = {
        "nom": nom,
        "age": age,
        "sexe": sexe,
        "historique": []
    }
    return patients_col.insert_one(patient).inserted_id

# Ajouter analyse
def add_analysis(patient_id, analysis_data):
    analysis_id = analyses_col.insert_one(analysis_data).inserted_id
    patients_col.update_one(
        {"_id": ObjectId(patient_id)},
        {"$push": {"historique": analysis_id}}
    )
    return analysis_id

# Récupérer analyses par patient
def get_analyses(patient_id):
    patient = patients_col.find_one({"_id": ObjectId(patient_id)})
    if not patient or "historique" not in patient:
        return []
    analyses = analyses_col.find({"_id": {"$in": patient["historique"]}})
    return list(analyses)

# Liste patients
def list_patients():
    return list(patients_col.find())


# Ajouter un utilisateur
def add_user(username, password, role="patient"):
    user = {
        "username": username,
        "password": password,  # plus tard: hashé avec bcrypt
        "role": role  # "patient" ou "medecin"
    }
    return users_col.insert_one(user).inserted_id

# Vérifier login
def check_login(username, password):
    user = users_col.find_one({"username": username, "password": password})
    if user:
        return {"_id": str(user["_id"]), "username": user["username"], "role": user["role"]}
    return None

# Récupérer tous les patients (pour le medecin)
def get_all_patients():
    return list(users_col.find({"role": "patient"}))
