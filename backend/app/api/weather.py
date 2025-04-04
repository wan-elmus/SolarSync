from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.core.database import get_db, SessionLocal
from app.models.job import Job
from app.core.state import JobState
from app.core.redis import get_job_state, save_job_state
from app.workflows.job_workflow import job_workflow
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/weather", tags=["weather"])

class WeatherUpdateResponse(BaseModel):
    message: str

def run_weather_update(job_id: str) -> None:
    """
    Run the weather update agent for a specific job in a background task.

    Args:
        job_id (str): The ID of the job to update.
    """
    # Create a new database session for the background task
    db = SessionLocal()
    try:
        logger.info(f"Running weather update for job {job_id}")
        
        # Retrieve the job state from Redis
        try:
            state = get_job_state(job_id)
            if not state:
                logger.warning(f"No state found for job {job_id}, skipping weather update")
                return
        except Exception as e:
            logger.error(f"Failed to retrieve job state from Redis for job {job_id}: {str(e)}")
            return

        # Run the weather update agent through the workflow
        state["messages"] = []  # Reset messages for this run
        final_state = job_workflow.invoke(
            state,
            config={"configurable": {"db": db}},
            starting_node="weather_update_agent"
        )

        # Save the updated state back to Redis
        try:
            save_job_state(job_id, final_state)
            logger.info(f"Weather update completed for job {job_id}")
        except Exception as e:
            logger.error(f"Failed to save job state to Redis for job {job_id}: {str(e)}")

    except Exception as e:
        logger.error(f"Error running weather update for job {job_id}: {str(e)}")
    finally:
        db.close()

@router.post("/update-all", response_model=WeatherUpdateResponse)
async def update_weather_for_all_jobs(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """
    Trigger weather updates for all active jobs.

    Args:
        background_tasks (BackgroundTasks): FastAPI background tasks for scheduling.
        db (Session): The database session.

    Returns:
        WeatherUpdateResponse: A message indicating the result of the operation.

    Raises:
        HTTPException: If the operation fails.
    """
    logger.info("Triggering weather updates for all active jobs")

    try:
        # Fetch all active jobs (pending or in_progress)
        active_jobs = db.query(Job).filter(Job.status.in_(["pending", "in_progress"])).all()
        if not active_jobs:
            logger.info("No active jobs found for weather update")
            return WeatherUpdateResponse(message="No active jobs found")

        # Schedule weather update for each job
        for job in active_jobs:
            background_tasks.add_task(run_weather_update, job.id)

        logger.info(f"Scheduled weather updates for {len(active_jobs)} active jobs")
        return WeatherUpdateResponse(message=f"Scheduled weather updates for {len(active_jobs)} active jobs")

    except Exception as e:
        logger.error(f"Error scheduling weather updates: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error scheduling weather updates: {str(e)}")