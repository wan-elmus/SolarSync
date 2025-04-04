from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from app.core.database import get_db
from app.models.job import Job, JobStatus
from app.workflows.job_workflow import job_workflow
from app.workflows.job_completion_workflow import job_completion_workflow
from app.core.state import JobState
from app.core.redis import save_job_state, delete_job_state
from app.core.auth import get_current_active_user, get_current_customer, get_current_technician, get_current_admin
from app.models.user import User, UserRole
import logging
from app.api.websockets import broadcast_job_update

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/jobs", tags=["jobs"])

class Appliance(BaseModel):
    name: str = Field(..., description="Name of the appliance (e.g., 'lights')")
    power_w: Optional[float] = Field(None, description="Power rating in watts (optional, will use default if not provided)")
    quantity: int = Field(..., gt=0, description="Number of units")
    runtime_hrs: float = Field(..., gt=0, description="Daily runtime in hours")

class JobCreate(BaseModel):
    description: str = Field(..., description="Description of the job (e.g., 'GRID TIE OFFLINE')")
    system_type: str = Field(..., description="Type of solar system ('pure' or 'hybrid')")
    appliances: List[Appliance] = Field(..., description="List of appliances with their details")
    position: dict = Field(..., description="Location coordinates (e.g., {'lat': -1.2699, 'lon': 36.8408})")
    battery_type: str = Field(..., description="Preferred battery type ('lead_acid' or 'lithium_ion')")
    contact_first_name: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    contact_last_name: Optional[str] = None
    contact_mobile: Optional[str] = None
    contact_phone: Optional[str] = None
    customer: Optional[dict] = None
    site: Optional[str] = None
    equipment: Optional[dict] = None
    project: Optional[dict] = None
    type: Optional[str] = None
    report_template: Optional[str] = None
    created_by: Optional[dict] = None
    address_street: Optional[str] = None
    address_province: Optional[str] = None
    address_city: Optional[str] = None
    address_zip: Optional[str] = None
    address_country: Optional[str] = None
    address: Optional[str] = None
    address_complement: Optional[str] = None
    created_by_customer: Optional[bool] = None
    custom_field_values: Optional[dict] = None
    preferences: Optional[dict] = None
    job_type: Optional[str] = None

class JobUpdate(BaseModel):
    status: Optional[str] = Field(None, description="Job status ('pending', 'in_progress', 'completed')")
    actual_end: Optional[str] = None

class JobResponse(BaseModel):
    id: str
    description: Optional[str]
    priority: Optional[str]
    system_type: Optional[str]
    appliances: Optional[List[dict]]
    load_demand_kwh: Optional[float]
    position: Optional[dict]
    panel_capacity_kw: Optional[float]
    battery_capacity_kwh: Optional[float]
    inverter_capacity_kw: Optional[float]
    total_cost_ksh: Optional[float]
    roi_years: Optional[float]
    contact_first_name: Optional[str]
    contact_email: Optional[str]
    contact_mobile: Optional[str]
    technician_name: Optional[str]
    status: Optional[str]
    date_created: Optional[datetime]
    date_modified: Optional[datetime]
    user_id: Optional[str]
    technician_id: Optional[str]
    panels_required: Optional[int]
    lead_acid_batteries_required: Optional[int]
    lithium_ion_batteries_required: Optional[int]
    inverters_required: Optional[int]
    lead_acid_batteries_series: Optional[int]
    lead_acid_batteries_parallel: Optional[int]
    lithium_ion_batteries_series: Optional[int]
    lithium_ion_batteries_parallel: Optional[int]

    class Config:
        orm_mode = True

class JobListResponse(BaseModel):
    jobs: List[JobResponse]
    total: int
    page: int
    page_size: int

@router.post("/create", response_model=JobResponse)
async def create_job(
    job: JobCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new job and run the LangGraph workflow for sizing and triaging.
    Only customers and admins can create jobs.

    Args:
        job (JobCreate): The job details provided by the user.
        db (Session): The database session.
        current_user (User): The authenticated user.

    Returns:
        JobResponse: The created job with sizing and triaging results.

    Raises:
        HTTPException: If the job creation fails or the user is not authorized.
    """
    logger.info(f"Creating new job with description: {job.description} by user {current_user.email}")

    # Role-based access
    if current_user.role not in [UserRole.CUSTOMER, UserRole.ADMIN]:
        logger.error(f"User {current_user.email} not authorized to create jobs")
        raise HTTPException(status_code=403, detail="Not authorized to create jobs")

    # Validate position format
    if not all(key in job.position for key in ["lat", "lon"]):
        logger.error("Invalid position format in job creation request")
        raise HTTPException(status_code=400, detail="Position must contain 'lat' and 'lon' keys")
    
    # Validate battery_type
    valid_battery_types = ["lead_acid", "lithium_ion"]
    if job.battery_type not in valid_battery_types:
        logger.error(f"Invalid battery_type: {job.battery_type}")
        raise HTTPException(status_code=400, detail=f"battery_type must be one of {valid_battery_types}")

    # Initialize state with user input
    initial_state = JobState(
        description=job.description,
        system_type=job.system_type,
        appliances=[appliance.dict() for appliance in job.appliances],  
        position=job.position,
        battery_type=job.battery_type,
        contact_first_name=job.contact_first_name,
        contact_email=job.contact_email,
        contact_last_name=job.contact_last_name,
        contact_mobile=job.contact_mobile,
        contact_phone=job.contact_phone,
        customer=job.customer,
        site=job.site,
        equipment=job.equipment,
        project=job.project,
        type=job.type,
        report_template=job.report_template,
        created_by=job.created_by,
        address_street=job.address_street,
        address_province=job.address_province,
        address_city=job.address_city,
        address_zip=job.address_zip,
        address_country=job.address_country,
        address=job.address,
        address_complement=job.address_complement,
        created_by_customer=job.created_by_customer,
        custom_field_values=job.custom_field_values,
        preferences=job.preferences,
        job_type=job.job_type,
        messages=[],
        user_id=current_user.id if current_user.role == UserRole.CUSTOMER else None
    )

    # Run the LangGraph workflow
    try:
        final_state = await job_workflow.invoke(initial_state, config={"configurable": {"db": db}})
    except Exception as e:
        logger.error(f"LangGraph workflow failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Workflow failed: {str(e)}")

    # Validate job_id
    if not final_state.get("job_id"):
        logger.error("LangGraph workflow did not return a job_id")
        raise HTTPException(status_code=500, detail="Job creation failed: no job_id returned")

    # Save the final state to Redis
    try:
        save_job_state(final_state["job_id"], final_state)
    except Exception as e:
        logger.error(f"Failed to save job state to Redis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to save job state: {str(e)}")

    # Fetch the updated job from the database
    try:
        db_job = db.query(Job).filter(Job.id == final_state["job_id"]).first()
        if not db_job:
            logger.error(f"Job {final_state['job_id']} not found in database after creation")
            raise HTTPException(status_code=404, detail="Job not created")
    except Exception as e:
        logger.error(f"Database query failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    logger.info(f"Job {db_job.id} created successfully by user {current_user.email}")
    return db_job

@router.get("/list", response_model=JobListResponse)
async def list_jobs(
    page: int = 1,
    page_size: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    List all jobs with pagination.
    Customers see their own jobs, technicians see their assigned jobs, admins see all.

    Args:
        page (int): The page number (default: 1).
        page_size (int): The number of jobs per page (default: 10).
        db (Session): The database session.
        current_user (User): The authenticated user.

    Returns:
        JobListResponse: A paginated list of jobs.
    """
    logger.info(f"Listing jobs: page={page}, page_size={page_size} by user {current_user.email}")

    try:
        # Calculate offset
        offset = (page - 1) * page_size
        # Query jobs based on user role
        query = db.query(
            Job.id,
            Job.description,
            Job.priority,
            Job.system_type,
            Job.appliances,
            Job.load_demand_kwh,
            Job.position,
            Job.panel_capacity_kw,
            Job.battery_capacity_kwh,
            Job.inverter_capacity_kw,
            Job.total_cost_ksh,
            Job.roi_years,
            Job.contact_first_name,
            Job.contact_email,
            Job.contact_mobile,
            Job.technician_id,
            Job.status,
            Job.date_created,
            Job.date_modified,
            Job.user_id,
            Job.panels_required,
            Job.lead_acid_batteries_required,
            Job.lithium_ion_batteries_required,
            Job.inverters_required,
            Job.lead_acid_batteries_series,
            Job.lead_acid_batteries_parallel,
            Job.lithium_ion_batteries_series,
            Job.lithium_ion_batteries_parallel
        )
        if current_user.role == UserRole.CUSTOMER:
            query = query.filter(Job.user_id == current_user.id)
        elif current_user.role == UserRole.TECHNICIAN:
            query = query.filter(Job.technician_id == current_user.id)
        # Admins can see all jobs
        jobs = query.offset(offset).limit(page_size).all()
        # Get the total count (optimized by using a separate count query)
        total_query = db.query(Job.id)
        if current_user.role == UserRole.CUSTOMER:
            total_query = total_query.filter(Job.user_id == current_user.id)
        elif current_user.role == UserRole.TECHNICIAN:
            total_query = total_query.filter(Job.technician_id == current_user.id)
        total = total_query.count()
    except Exception as e:
        logger.error(f"Database query failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    logger.info(f"Retrieved {len(jobs)} jobs (total: {total}) by user {current_user.email}")
    return {
        "jobs": jobs,
        "total": total,
        "page": page,
        "page_size": page_size
    }

@router.put("/{job_id}", response_model=JobResponse)
async def update_job(
    job_id: str,
    job_update: JobUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Update a job's status or actual end date.
    Only admins can update jobs.

    Args:
        job_id (str): The ID of the job to update.
        job_update (JobUpdate): The updated job details.
        db (Session): The database session.
        current_user (User): The authenticated user (must be admin).

    Returns:
        JobResponse: The updated job.

    Raises:
        HTTPException: If the job is not found, the user is not authorized, or the update fails.
    """
    logger.info(f"Updating job {job_id} by user {current_user.email}")

    try:
        db_job = db.query(Job).filter(Job.id == job_id).first()
        if not db_job:
            logger.error(f"Job {job_id} not found")
            raise HTTPException(status_code=404, detail="Job not found")

        # Validate status if provided
        if job_update.status:
            valid_statuses = ["pending", "in_progress", "completed"]
            if job_update.status not in valid_statuses:
                logger.error(f"Invalid status {job_update.status} for job {job_id}")
                raise HTTPException(status_code=400, detail=f"Status must be one of {valid_statuses}")
            db_job.status = JobStatus(job_update.status)

        if job_update.actual_end:
            try:
                db_job.actual_end = datetime.fromisoformat(job_update.actual_end)
            except ValueError as e:
                logger.error(f"Invalid actual_end format for job {job_id}: {str(e)}")
                raise HTTPException(status_code=400, detail="actual_end must be in ISO format")

        db_job.date_modified = datetime.utcnow()
        db.commit()
        db.refresh(db_job)
        
        # Broadcast the job update via WebSocket
        await broadcast_job_update(job_id, db)

        # If the job is no longer active, delete its state from Redis
        if db_job.status not in [JobStatus.PENDING, JobStatus.IN_PROGRESS]:
            try:
                delete_job_state(job_id)
                logger.info(f"Deleted Redis state for job {job_id}")
            except Exception as e:
                logger.warning(f"Failed to delete Redis state for job {job_id}: {str(e)}")

        logger.info(f"Job {job_id} updated successfully by user {current_user.email}")
        return db_job

    except Exception as e:
        db.rollback()
        logger.error(f"Database update failed for job {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.post("/complete/{job_id}")
async def complete_job(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_technician)
):
    """
    Mark a job as completed and run the job completion workflow.
    Only technicians can complete jobs, and only their assigned jobs.

    Args:
        job_id (str): The ID of the job to complete.
        db (Session): The database session.
        current_user (User): The authenticated user (must be a technician).

    Returns:
        dict: A response containing the job details and workflow result.

    Raises:
        HTTPException: If the job is not found, the user is not authorized, or the workflow fails.
    """
    logger.info(f"Completing job {job_id} by technician {current_user.email}")

    # Fetch the job from the database
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        logger.error(f"Job {job_id} not found")
        raise HTTPException(status_code=404, detail="Job not found")

    # Ensure the technician is assigned to this job
    if job.technician_id != current_user.id:
        logger.error(f"Technician {current_user.email} not authorized to complete job {job_id}")
        raise HTTPException(status_code=403, detail="Not authorized to complete this job")

    # Run the job completion workflow
    state = JobState(job_id=job_id, db=db)
    try:
        result = await job_completion_workflow.run(state)
    except Exception as e:
        logger.error(f"Job completion workflow failed for job {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Workflow failed: {str(e)}")

    # Check the workflow result
    if result.get("status") == "error":
        logger.error(f"Job completion workflow failed for job {job_id}: {result.get('message')}")
        raise HTTPException(status_code=500, detail=result.get("message", "Job completion workflow failed"))

    # Refresh the job from the database
    db.refresh(job)

    # If the job is no longer active, delete its state from Redis
    if job.status not in [JobStatus.PENDING, JobStatus.IN_PROGRESS]:
        try:
            delete_job_state(job_id)
            logger.info(f"Deleted Redis state for job {job_id}")
        except Exception as e:
            logger.warning(f"Failed to delete Redis state for job {job_id}: {str(e)}")

    # Include feedback from the workflow result in the response
    response = {
        "message": "Job completed successfully",
        "job": {
            "id": job.id,
            "status": job.status.value,
            "actual_end": job.actual_end,
            "technician_feedback": job.custom_field_values.get("technician_feedback") if job.custom_field_values else None
        },
        "workflow_result": {
            "status": result.get("status"),
            "feedback": result.get("feedback")
        }
    }
    logger.info(f"Job {job_id} completed successfully by technician {current_user.email}")
    return response