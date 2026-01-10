from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    session, # Added session import
)
import os
from dotenv import load_dotenv
from config import Config
from routes.auth import auth_bp
from routes.main import main_bp
from routes.api import api_bp
from routes.admin import admin_bp
from celery_app import make_celery
from datetime import datetime
import logging
from logging.handlers import RotatingFileHandler
from database.mongodb_connector import connect_to_mongodb  # Import connect_to_mongodb

load_dotenv()

# =====================
# CONFIG
# =====================
app = Flask(__name__)
app.config.from_object(Config)

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# =====================
# DATABASE CONNECTION
# =====================
users_col, patients_col, analyses_col = connect_to_mongodb()
if users_col is None:
    app.logger.error("Failed to connect to MongoDB on startup. Exiting.")
    # In a real application, you might want to raise an exception or handle this more gracefully
    # For now, we'll just log and let the app potentially fail later if db ops are attempted.
    # Or, you could exit: sys.exit(1)
app.config["USERS_COLLECTION"] = users_col
app.config["PATIENTS_COLLECTION"] = patients_col
app.config["ANALYSES_COLLECTION"] = analyses_col


# =====================
# LOGGING
# =====================
if not app.debug:
    if not os.path.exists("logs"):
        os.mkdir("logs")
    file_handler = RotatingFileHandler(
        "logs/parkinson_detection.log", maxBytes=10240, backupCount=10
    )
    file_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]"
        )
    )
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)

    app.logger.setLevel(logging.INFO)
    app.logger.info("Parkinson Detection startup")

# =====================
# CELERY
# =====================
celery = make_celery(app)

# =====================
# BLUEPRINTS
# =====================
app.register_blueprint(auth_bp, url_prefix="/auth")
app.register_blueprint(main_bp)
app.register_blueprint(api_bp)
app.register_blueprint(admin_bp)


# =====================
# CONTEXT PROCESSORS
# =====================
@app.context_processor
def inject_current_year():
    return {"current_year": datetime.now().year}

@app.context_processor
def inject_current_user():
    user = session.get("user")
    if user:
        # Convert ObjectId to string for JSON serialization if needed later,
        # and to avoid issues with Jinja2's strictness.
        # Also, add an is_authenticated property for template checks.
        user_obj = {
            **user,
            "_id": str(user["_id"]),
            "is_authenticated": True,
            "is_active": True, # Assuming active if logged in
            "is_anonymous": False,
            "get_id": lambda: str(user["_id"]) # For Flask-Login compatibility if ever introduced
        }
        return {"current_user": user_obj}
    return {"current_user": {"is_authenticated": False, "is_anonymous": True}}


# =====================
# ERROR HANDLERS
# =====================
def handle_error(e):
    code = getattr(e, "code", 500)
    message = getattr(e, "description", "Internal Server Error")

    app.logger.error(f"Error {code}: {message}", exc_info=True)

    if (
        request.accept_mimetypes.accept_json
        and not request.accept_mimetypes.accept_html
    ):
        response = jsonify(code=code, message=message)
        response.status_code = code
        return response
    return render_template(f"{code}.html", error=message), code


app.errorhandler(400)(handle_error)
app.errorhandler(401)(handle_error)
app.errorhandler(403)(handle_error)
app.errorhandler(404)(handle_error)
app.errorhandler(405)(handle_error)
app.errorhandler(500)(handle_error)

# =====================
# RUN
# =====================
if __name__ == "__main__":
    app.run(debug=True)
