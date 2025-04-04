from sqlalchemy.orm import Session
from app.core.state import JobState
from app.models.job import Job, JobStatus
from app.api.websockets import broadcast_job_update  # Added for WebSocket
import logging
from typing import Dict, Any

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def job_completion_agent(state: JobState, db: Session) -> Dict[str, Any]:
    """
    Agent to handle job completion tasks in the job completion workflow.

    Updates the job status to 'completed', collects feedback from the technician,
    and updates the job's actual end time.

    Args:
        state (JobState): The current state of the job workflow.
        db (Session): The database session.

    Returns:
        Dict[str, Any]: Updated state with feedback and status information.
    """
    try:
        job_id = state.job_id
        logger.info(f"Job completion agent started for job {job_id}")

        # Fetch the job from the database
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            logger.error(f"Job {job_id} not found")
            return {"status": "error", "message": f"Job {job_id} not found"}

        # Update job status to completed
        job.status = JobStatus.COMPLETED
        job.actual_end = db.func.now()  # Set the actual end time to now
        job.date_modified = db.func.now()  # Update the modified timestamp

        # Collect feedback (for now, we'll mock this; in a real system, this could come from the API)
        feedback = state.get("feedback", "Job completed successfully by technician")  # Mock feedback
        job.custom_field_values = job.custom_field_values or {}
        job.custom_field_values["technician_feedback"] = feedback

        # Commit changes to the database
        db.commit()
        db.refresh(job)

        # Broadcast the job update via WebSocket
        await broadcast_job_update(job_id, db)

        logger.info(f"Job {job_id} marked as completed with feedback: {feedback}")

        # Update the state
        state_dict = state.copy()
        state_dict["status"] = "completed"
        state_dict["feedback"] = feedback
        return state_dict

    except Exception as e:
        logger.error(f"Error in job completion agent for job {job_id}: {str(e)}")
        return {"status": "error", "message": str(e)}