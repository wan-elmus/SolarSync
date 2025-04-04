from sqlalchemy.orm import Session
from app.core.state import JobState
from app.models.job import Job
from app.models.technician import Technician
from app.api.websockets import broadcast_job_update  # Added for WebSocket
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def technician_assignment_agent(state: JobState, db: Session) -> JobState:
    """
    Assign a technician to the job based on the AI-predicted technician_id.
    
    Args:
        state (JobState): The current state of the job in the LangGraph workflow.
        db (Session): The database session for querying and updating the job.
    
    Returns:
        JobState: The updated state with technician details.
    """
    # Validate required fields
    if not state.get("technician_id") or not state.get("job_id"):
        state["messages"].append({"agent": "technician_assignment_agent", "message": "Skipping technician assignment: missing technician_id or job_id"})
        logger.warning(f"Job {state.get('job_id', 'unknown')} missing required fields for technician assignment")
        return state

    # Fetch technician details
    technician = db.query(Technician).filter(Technician.id == state["technician_id"]).first()
    if not technician:
        state["messages"].append({"agent": "technician_assignment_agent", "message": f"Technician {state['technician_id']} not found"})
        logger.warning(f"Technician {state['technician_id']} not found for job {state['job_id']}")
        return state

    # Update job with technician details
    try:
        db_job = db.query(Job).filter(Job.id == state["job_id"]).first()
        if not db_job:
            state["messages"].append({"agent": "technician_assignment_agent", "message": f"Job {state['job_id']} not found in database"})
            logger.error(f"Job {state['job_id']} not found in database")
            return state

        # Update job fields (technician_id is already set by AI Prediction Agent)
        db_job.technician_name = f"{technician.first_name} {technician.last_name or ''}".strip()  # Updated to match User model
        db_job.technician_login = technician.email  # Updated to use email instead of login
        db_job.date_modified = db.func.now()  # Update the modified timestamp
        db.commit()
        db.refresh(db_job)

        # Broadcast the job update via WebSocket
        await broadcast_job_update(state["job_id"], db)
    except Exception as e:
        db.rollback()
        state["messages"].append({"agent": "technician_assignment_agent", "message": f"Database update failed: {str(e)}"})
        logger.error(f"Database update failed for job {state['job_id']}: {str(e)}")
        return state

    state["technician_name"] = db_job.technician_name
    state["technician_login"] = db_job.technician_login
    state["messages"].append({"agent": "technician_assignment_agent", "message": f"Technician {db_job.technician_name} assigned to job {state['job_id']}"})
    logger.info(f"Technician {db_job.technician_name} assigned to job {state['job_id']}")
    return state