from sqlalchemy.orm import Session
from app.core.state import JobState
from app.services.ai_service import predict_job_details
from app.models.prediction import Prediction
from app.models.job import Job
from app.api.websockets import broadcast_job_update
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def ai_prediction_agent(state: JobState, db: Session) -> JobState:
    """
    Run AI predictions for a job, updating the state and database with the results.
    
    Args:
        state (JobState): The current state of the job in the LangGraph workflow.
        db (Session): The database session for querying and updating the database.
    
    Returns:
        JobState: The updated state with AI prediction results.
    """
    # Validate required fields
    if not state.get("description") or not state.get("system_type") or not state.get("job_id"):
        state["messages"].append({"agent": "ai_prediction_agent", "message": "Skipping AI predictions: missing required fields (description, system_type, or job_id)"})
        logger.warning(f"Job {state.get('job_id', 'unknown')} missing required fields for AI predictions")
        return state

    # Run AI predictions
    try:
        prediction = predict_job_details(
            job_id=state["job_id"],
            description=state["description"],
            system_type=state["system_type"],
            battery_type=state.get("battery_type"),  # Added
            battery_cost_ksh=state.get("battery_cost_ksh", 0),  # Added
            panel_cost_ksh=state.get("panel_cost_ksh", 0),  # Added
            inverter_cost_ksh=state.get("inverter_cost_ksh", 0),  # Added
            db=db
        )
    except Exception as e:
        state["messages"].append({"agent": "ai_prediction_agent", "message": f"AI prediction failed: {str(e)}"})
        logger.error(f"AI prediction failed for job {state['job_id']}: {str(e)}")
        return state

    # Validate prediction results
    required_keys = ["priority", "technician_id", "diagnosis", "duration_hours", "labor_ksh", "transport_ksh"]
    missing_keys = [key for key in required_keys if key not in prediction]
    if missing_keys:
        state["messages"].append({"agent": "ai_prediction_agent", "message": f"AI prediction missing required keys: {missing_keys}"})
        logger.warning(f"AI prediction for job {state['job_id']} missing keys: {missing_keys}")
        return state

    # Update state with prediction results
    state["priority"] = prediction["priority"]
    state["technician_id"] = prediction["technician_id"]
    state["diagnosis"] = prediction["diagnosis"]

    # Save prediction to database
    try:
        db_prediction = Prediction(
            job_id=state["job_id"],
            priority=prediction["priority"],
            duration_hours=prediction["duration_hours"],
            labor_ksh=prediction["labor_ksh"],
            transport_ksh=prediction["transport_ksh"],
            diagnosis=prediction["diagnosis"]
        )
        db.add(db_prediction)

        # Update job with predicted fields
        db_job = db.query(Job).filter(Job.id == state["job_id"]).first()
        if not db_job:
            state["messages"].append({"agent": "ai_prediction_agent", "message": f"Job {state['job_id']} not found in database"})
            logger.error(f"Job {state['job_id']} not found in database")
            return state

        db_job.priority = prediction["priority"]
        db_job.technician_id = prediction["technician_id"]
        db_job.date_modified = db.func.now()
        db.commit()
        db.refresh(db_job)

        # Broadcast the job update via WebSocket
        await broadcast_job_update(state["job_id"], db)
    except Exception as e:
        db.rollback()
        state["messages"].append({"agent": "ai_prediction_agent", "message": f"Database update failed: {str(e)}"})
        logger.error(f"Database update failed for job {state['job_id']}: {str(e)}")
        return state

    state["messages"].append({"agent": "ai_prediction_agent", "message": f"AI predictions completed for job {state['job_id']}"})
    logger.info(f"AI predictions completed for job {state['job_id']}")
    return state