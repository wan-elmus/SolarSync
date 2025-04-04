from sqlalchemy.orm import Session
from app.core.state import JobState
from app.services.sizing_service import calculate_sizing
from app.models.job import Job
from app.api.websockets import broadcast_job_update
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def sizing_agent(state: JobState, db: Session) -> JobState:
    """
    Calculate sizing metrics for a solar grid-tie system and update the job.
    
    Args:
        state (JobState): The current state of the job in the LangGraph workflow.
        db (Session): The database session for updating the job.
    
    Returns:
        JobState: The updated state with sizing results.
    """
    # Validate required fields
    if not state.get("system_type") or not state.get("appliances") or not state.get("position") or not state.get("job_id"):
        state["messages"].append({"agent": "sizing_agent", "message": "Skipping sizing: missing required fields (system_type, appliances, position, or job_id)"})
        logger.warning(f"Job {state.get('job_id', 'unknown')} missing required fields for sizing")
        return state

    # Calculate sizing using the appliances list
    try:
        sizing_result = calculate_sizing(
            system_type=state["system_type"],
            appliances=state["appliances"],
            position=state["position"]
        )
    except Exception as e:
        state["messages"].append({"agent": "sizing_agent", "message": f"Sizing calculation failed: {str(e)}"})
        logger.error(f"Sizing calculation failed for job {state['job_id']}: {str(e)}")
        return state

    # Update state with sizing results
    state.update(sizing_result)

    # Update job in database
    try:
        db_job = db.query(Job).filter(Job.id == state["job_id"]).first()
        if not db_job:
            state["messages"].append({"agent": "sizing_agent", "message": f"Job {state['job_id']} not found in database"})
            logger.error(f"Job {state['job_id']} not found in database")
            return state

        # Validate sizing_result keys to ensure they match Job model attributes
        valid_attributes = {col.name for col in Job.__table__.columns}
        for key, value in sizing_result.items():
            if key in valid_attributes:
                setattr(db_job, key, value)
            else:
                logger.warning(f"Ignoring invalid attribute {key} in sizing_result for job {state['job_id']}")

        # Also store the appliances in the Job model
        db_job.appliances = state["appliances"]

        db_job.date_modified = db.func.now()  # Update the modified timestamp
        db.commit()
        db.refresh(db_job)

        # Broadcast the job update via WebSocket
        await broadcast_job_update(state["job_id"], db)
    except Exception as e:
        db.rollback()
        state["messages"].append({"agent": "sizing_agent", "message": f"Database update failed: {str(e)}"})
        logger.error(f"Database update failed for job {state['job_id']}: {str(e)}")
        return state

    state["messages"].append({"agent": "sizing_agent", "message": f"Sizing completed for job {state['job_id']}"})
    logger.info(f"Sizing completed for job {state['job_id']}")
    return state