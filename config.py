import os
from datetime import timedelta  # Import timedelta for session lifetime


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or "super_secret_key_dev"
    UPLOAD_FOLDER = "static/uploads"
    ML_MODEL_PATH = "models/tremblement_model_improved.pkl"
    HAND_LANDMARKER_TASK_PATH = "models/hand_landmarker.task"
    CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
    CELERY_RESULT_BACKEND = os.environ.get(
        "CELERY_RESULT_BACKEND", "redis://localhost:6379/0"
    )

    # Session Configuration for Enhanced Security
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = (
        os.environ.get("FLASK_ENV") == "production"
    )  # Only secure in production
    SESSION_COOKIE_SAMESITE = "Lax"  # Can be 'Lax' or 'Strict'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=1)  # Example: session lasts 1 hour
    SESSION_REFRESH_EACH_REQUEST = True  # Extend session on each request
