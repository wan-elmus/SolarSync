from sqlalchemy.orm import Session
from app.models.job import Job, JobStatus
from app.core.state import JobState
from datetime import datetime
import uuid
import logging
from app.api.websockets import broadcast_job_update  # Added for WebSocket

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def job_creator(state: JobState, db: Session) -> JobState:
    """
    Create a new job in the database and initialize the job state.
    
    Args:
        state (JobState): The initial state of the job in the LangGraph workflow.
        db (Session): The database session for creating the job.
    
    Returns:
        JobState: The updated state with the new job ID and status.
    """
    # Validate required fields
    if not state.get("description") or not state.get("system_type"):
        state["messages"].append({"agent": "job_creator", "message": "Skipping job creation: missing required fields (description or system_type)"})
        logger.warning("Missing required fields for job creation")
        return state

    job_id = str(uuid.uuid4())
    try:
        db_job = Job(
            id=job_id,
            description=state.get("description"),
            system_type=state.get("system_type"),
            load_demand_kwh=state.get("load_demand_kwh"),
            position=state.get("position"),
            contact_first_name=state.get("contact_first_name"),
            contact_email=state.get("contact_email"),
            contact_last_name=state.get("contact_last_name"),
            contact_mobile=state.get("contact_mobile"),
            contact_phone=state.get("contact_phone"),
            customer=state.get("customer"),
            site=state.get("site"),
            equipment=state.get("equipment"),
            project=state.get("project"),
            type=state.get("type"),
            report_template=state.get("report_template"),
            created_by=state.get("created_by"),
            address_street=state.get("address_street"),
            address_province=state.get("address_province"),
            address_city=state.get("address_city"),
            address_zip=state.get("address_zip"),
            address_country=state.get("address_country"),
            address=state.get("address"),
            address_complement=state.get("address_complement"),
            created_by_customer=state.get("created_by_customer"),
            custom_field_values=state.get("custom_field_values"),
            preferences=state.get("preferences"),
            job_type=state.get("job_type"),
            user_id=state.get("user_id"),  # Added to associate the job with the customer
            date_created=datetime.utcnow(),
            date_modified=datetime.utcnow(),
            status=JobStatus.PENDING  # Updated to use JobStatus enum
        )
        db.add(db_job)
        db.commit()
        db.refresh(db_job)

        # Broadcast the job creation via WebSocket
        await broadcast_job_update(job_id, db)
    except Exception as e:
        db.rollback()
        state["messages"].append({"agent": "job_creator", "message": f"Failed to create job: {str(e)}"})
        logger.error(f"Failed to create job: {str(e)}")
        return state

    state["job_id"] = job_id
    state["status"] = "pending"
    state["date_created"] = db_job.date_created.isoformat()
    state["messages"].append({"agent": "job_creator", "message": f"Job {job_id} created"})
    logger.info(f"Job {job_id} created successfully")
    return state