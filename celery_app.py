from celery import Celery

celery = Celery(__name__)  # Initialize Celery here


def make_celery(app):
    celery.conf.update(
        broker_url=app.config["CELERY_BROKER_URL"],
        result_backend=app.config["CELERY_RESULT_BACKEND"],
        # Recommended Celery Configuration for Robustness
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
        timezone="Europe/Paris",  # Or your application's timezone
        enable_utc=True,
        task_acks_late=True,  # Acknowledge task only after it's done
        worker_prefetch_multiplier=1,  # Process one task at a time
        task_track_started=True,  # Track task started state
        task_time_limit=300,  # Tasks will be killed after 5 minutes
        task_soft_time_limit=240,  # Tasks will raise SoftTimeLimitExceeded after 4 minutes
        broker_connection_retry_on_startup=True,  # Retry connecting to broker on startup
    )

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery
