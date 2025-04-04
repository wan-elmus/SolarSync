from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.api.weather import run_weather_update
from app.models.job import Job
import logging
from typing import Optional

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the scheduler with configuration
scheduler = BackgroundScheduler(
    timezone="UTC",
    job_defaults={
        "coalesce": True,  # Run missed jobs once if they pile up
        "max_instances": 1  # Prevent multiple instances of the same job
    }
)

def schedule_weather_updates(app: FastAPI) -> None:
    """
    Schedule periodic weather updates for active jobs.

    Args:
        app (FastAPI): The FastAPI application instance.
    """
    try:
        def run_weather_update_task() -> None:
            """Wrapper to run the weather update task with a new database session."""
            db: Session = SessionLocal()
            try:
                # Fetch all active jobs and run weather updates
                active_jobs = db.query(Job).filter(Job.status.in_(["pending", "in_progress"])).all()
                for job in active_jobs:
                    run_weather_update(job.id)
            except Exception as e:
                logger.error(f"Error in scheduled weather update: {str(e)}")
            finally:
                db.close()

        # Schedule the task to run every 30 minutes
        scheduler.add_job(run_weather_update_task, "interval", minutes=30)
        scheduler.start()
        logger.info("Scheduled weather updates to run every 30 minutes")

    except Exception as e:
        logger.error(f"Error scheduling weather updates: {str(e)}")
        raise

def shutdown_scheduler() -> None:
    """
    Shut down the scheduler on application shutdown.
    """
    try:
        if scheduler.running:
            scheduler.shutdown()
            logger.info("Scheduler shut down successfully")
        else:
            logger.info("Scheduler was not running")
    except Exception as e:
        logger.error(f"Error shutting down scheduler: {str(e)}")
        raise