from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from app.core.database import get_db
from app.models.prediction import Prediction
from app.models.job import Job
from app.core.auth import get_current_active_user
from app.models.user import User, UserRole
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/predictions", tags=["predictions"])

class PredictionResponse(BaseModel):
    id: int
    job_id: str
    priority: Optional[str]
    duration_hours: Optional[float]
    labor_ksh: Optional[float]
    transport_ksh: Optional[float]
    diagnosis: Optional[str]

    class Config:
        orm_mode = True

class PredictionListResponse(BaseModel):
    predictions: List[PredictionResponse]
    total: int
    page: int
    page_size: int

@router.get("/job/{job_id}", response_model=List[PredictionResponse])
async def get_predictions_for_job(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Retrieve all predictions for a specific job.
    Customers can only see predictions for their jobs, technicians for their assigned jobs, admins see all.

    Args:
        job_id (str): The ID of the job.
        db (Session): The database session.
        current_user (User): The authenticated user.

    Returns:
        List[PredictionResponse]: A list of predictions for the job.

    Raises:
        HTTPException: If the job has no predictions or the user is not authorized.
    """
    logger.info(f"Retrieving predictions for job {job_id} by user {current_user.email}")

    # Check if the job exists and the user has access
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            logger.error(f"Job {job_id} not found")
            raise HTTPException(status_code=404, detail="Job not found")

        # Role-based access
        if current_user.role == UserRole.CUSTOMER and job.user_id != current_user.id:
            logger.error(f"Customer {current_user.email} not authorized to view predictions for job {job_id}")
            raise HTTPException(status_code=403, detail="Not authorized to view predictions for this job")
        if current_user.role == UserRole.TECHNICIAN and job.technician_id != current_user.id:
            logger.error(f"Technician {current_user.email} not authorized to view predictions for job {job_id}")
            raise HTTPException(status_code=403, detail="Not authorized to view predictions for this job")
        # Admins can see all predictions

        predictions = db.query(Prediction).filter(Prediction.job_id == job_id).all()
        if not predictions:
            logger.warning(f"No predictions found for job {job_id}")
            raise HTTPException(status_code=404, detail="No predictions found for this job")

        logger.info(f"Retrieved {len(predictions)} predictions for job {job_id} by user {current_user.email}")
        return predictions
    except Exception as e:
        logger.error(f"Database query failed for job {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/list", response_model=PredictionListResponse)
async def list_predictions(
    page: int = 1,
    page_size: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    List all predictions with pagination.
    Customers see predictions for their jobs, technicians for their assigned jobs, admins see all.

    Args:
        page (int): The page number (default: 1).
        page_size (int): The number of predictions per page (default: 10).
        db (Session): The database session.
        current_user (User): The authenticated user.

    Returns:
        PredictionListResponse: A paginated list of predictions.
    """
    logger.info(f"Listing predictions: page={page}, page_size={page_size} by user {current_user.email}")

    try:
        offset = (page - 1) * page_size
        query = db.query(Prediction).join(Job, Prediction.job_id == Job.id)
        if current_user.role == UserRole.CUSTOMER:
            query = query.filter(Job.user_id == current_user.id)
        elif current_user.role == UserRole.TECHNICIAN:
            query = query.filter(Job.technician_id == current_user.id)
        # Admins can see all predictions
        predictions = query.offset(offset).limit(page_size).all()
        total = query.count()

        logger.info(f"Retrieved {len(predictions)} predictions (total: {total}) by user {current_user.email}")
        return {
            "predictions": predictions,
            "total": total,
            "page": page,
            "page_size": page_size
        }
    except Exception as e:
        logger.error(f"Database query failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")