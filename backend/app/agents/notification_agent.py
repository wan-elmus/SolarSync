from sqlalchemy.orm import Session
from app.core.state import JobState
from app.services.sms_service import send_sms
from app.models.job import Job
from app.models.user import User
from app.api.websockets import broadcast_job_update  # Added for WebSocket
import time
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def notification_agent(state: JobState, db: Session) -> JobState:
    """
    Send an SMS notification to the technician about the job schedule.
    
    Args:
        state (JobState): The current state of the job in the LangGraph workflow.
        db (Session): The database session for querying the job.
    
    Returns:
        JobState: The updated state with notification status messages.
    """
    # Validate required fields
    if not state.get("technician_id") or not state.get("job_id"):
        state["messages"].append({"agent": "notification_agent", "message": "Skipping notification: missing technician_id or job_id"})
        logger.warning(f"Job {state.get('job_id', 'unknown')} missing required fields for notification")
        return state

    # Fetch the job to get the technician's contact details
    job = db.query(Job).filter(Job.id == state["job_id"]).first()
    if not job:
        state["messages"].append({"agent": "notification_agent", "message": f"Job {state['job_id']} not found in database"})
        logger.error(f"Job {state['job_id']} not found in database")
        return state

    # Use the technician's phone number (stored in the User model)
    technician = db.query(User).filter(User.id == state["technician_id"]).first()
    if not technician or not technician.phone:
        state["messages"].append({"agent": "notification_agent", "message": f"Technician {state['technician_id']} has no phone number"})
        logger.warning(f"Technician {state['technician_id']} has no phone number for job {state['job_id']}")
        return state

    # Use scheduled_start if available, otherwise default to a placeholder
    scheduled_date = state.get("scheduled_start", "April 10")
    message = f"Job {state['job_id']} scheduled for {scheduled_date}"
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            send_sms(to=technician.phone, message=message)
            state["messages"].append({"agent": "notification_agent", "message": f"SMS sent for job {state['job_id']}"})
            logger.info(f"SMS sent for job {state['job_id']}")
            break
        except Exception as e:
            state["messages"].append({"agent": "notification_agent", "message": f"SMS attempt {attempt + 1} failed: {str(e)}"})
            logger.warning(f"SMS attempt {attempt + 1} failed for job {state['job_id']}: {str(e)}")
            if attempt == max_retries - 1:
                state["messages"].append({"agent": "notification_agent", "message": "Max retries reached, SMS failed"})
                logger.error(f"Max retries reached for SMS for job {state['job_id']}")
            time.sleep(2)  # Wait before retrying

    # Broadcast the job update via WebSocket
    await broadcast_job_update(state["job_id"], db)

    return state