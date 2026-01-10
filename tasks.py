from celery_app import celery
from analysis.video_analysis import analyze_video

# from database.mongodb_connector import add_analysis, get_analysis_by_id # No longer import directly
from flask import current_app
import logging

# Setup logging for tasks
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


@celery.task(bind=True, max_retries=3, default_retry_delay=60)
def analyze_video_task(self, video_path, patient_age, user_id):
    self.update_state(
        state="PROGRESS",
        meta={"current": 0, "total": 100, "status": "Starting video analysis..."},
    )
    logger.info(
        f"Task {self.request.id}: Starting video analysis for patient {user_id} on {video_path}"
    )

    try:
        # Get collections from app.config
        analyses_col = current_app.config["ANALYSES_COLLECTION"]
        patients_col = current_app.config["PATIENTS_COLLECTION"]
        from database.mongodb_connector import add_analysis  # Import here

        # Step 1: Analyze Video
        self.update_state(
            state="PROGRESS",
            meta={"current": 25, "total": 100, "status": "Analyzing video frames..."},
        )
        with current_app.app_context():
            analysis_result = analyze_video(video_path, patient_age=patient_age)

        if not analysis_result:
            raise ValueError("Video analysis returned no results.")

        # Step 2: Add Analysis to Database
        self.update_state(
            state="PROGRESS",
            meta={"current": 75, "total": 100, "status": "Saving analysis results..."},
        )
        with current_app.app_context():
            # Ensure patient_id is passed as string if add_analysis expects it
            analysis_id = add_analysis(
                analyses_col,
                patients_col,
                user_id,
                {"patient_id": user_id, "result": analysis_result},
            )

        if not analysis_id:
            raise ValueError("Failed to save analysis results to database.")

        self.update_state(
            state="SUCCESS",
            meta={
                "current": 100,
                "total": 100,
                "status": "Video analysis complete!",
                "analysis_id": str(analysis_id),
            },
        )
        logger.info(
            f"Task {self.request.id}: Video analysis completed successfully for patient {user_id}. Analysis ID: {analysis_id}"
        )
        return {"status": "SUCCESS", "analysis_id": str(analysis_id)}

    except Exception as exc:
        logger.error(
            f"Task {self.request.id}: Video analysis failed for patient {user_id} on {video_path}. Error: {exc}",
            exc_info=True,
        )

        # Update task state to FAILURE
        self.update_state(state="FAILURE", meta={"status": f"Analysis failed: {exc}"})

        # Retry the task on certain exceptions
        try:
            self.retry(exc=exc, countdown=self.default_retry_delay)
        except self.MaxRetriesExceededError:
            logger.error(
                f"Task {self.request.id}: Max retries exceeded for patient {user_id}."
            )
            return {"status": "FAILURE", "error": str(exc)}
