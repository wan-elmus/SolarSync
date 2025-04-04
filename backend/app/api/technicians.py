from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field
from app.core.database import get_db
from app.models.technician import Technician
from app.core.auth import get_current_active_user, get_current_admin, get_current_technician
from datetime import datetime
from app.models.user import User, UserRole
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/technicians", tags=["technicians"])

class TechnicianCreate(BaseModel):
    name: str = Field(..., description="Full name of the technician")
    login: str = Field(..., description="Unique login identifier for the technician")
    email: Optional[str] = None
    phone: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    skills: Optional[str] = None

class TechnicianUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    skills: Optional[str] = None

class TechnicianResponse(BaseModel):
    id: str
    name: str
    login: str
    email: Optional[str]
    phone: Optional[str]
    lat: Optional[float]
    lon: Optional[float]
    skills: Optional[str]

    class Config:
        orm_mode = True

class TechnicianListResponse(BaseModel):
    technicians: List[TechnicianResponse]
    total: int
    page: int
    page_size: int

@router.post("/create", response_model=TechnicianResponse)
async def create_technician(
    technician: TechnicianCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Create a new technician.
    Only admins can create technicians.

    Args:
        technician (TechnicianCreate): The technician details.
        db (Session): The database session.
        current_user (User): The authenticated user (must be admin).

    Returns:
        TechnicianResponse: The created technician.

    Raises:
        HTTPException: If the technician creation fails.
    """
    logger.info(f"Creating technician with login: {technician.login} by user {current_user.email}")

    # Check if login already exists
    try:
        existing_technician = db.query(Technician).filter(Technician.login == technician.login).first()
        if existing_technician:
            logger.error(f"Technician with login {technician.login} already exists")
            raise HTTPException(status_code=400, detail="Technician with this login already exists")
    except Exception as e:
        logger.error(f"Database query failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    # Create new technician
    try:
        db_technician = Technician(
            id=f"tech-{technician.login}-{int(datetime.utcnow().timestamp())}",  # Generate a unique ID
            name=technician.name,
            login=technician.login,
            email=technician.email,
            phone=technician.phone,
            lat=technician.lat,
            lon=technician.lon,
            skills=technician.skills
        )
        db.add(db_technician)
        db.commit()
        db.refresh(db_technician)
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create technician: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    logger.info(f"Technician {db_technician.id} created successfully by user {current_user.email}")
    return db_technician

@router.get("/list", response_model=TechnicianListResponse)
async def list_technicians(
    page: int = 1,
    page_size: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    List all technicians with pagination.
    Only admins can list technicians.

    Args:
        page (int): The page number (default: 1).
        page_size (int): The number of technicians per page (default: 10).
        db (Session): The database session.
        current_user (User): The authenticated user (must be admin).

    Returns:
        TechnicianListResponse: A paginated list of technicians.
    """
    logger.info(f"Listing technicians: page={page}, page_size={page_size} by user {current_user.email}")

    try:
        offset = (page - 1) * page_size
        technicians = db.query(Technician).offset(offset).limit(page_size).all()
        total = db.query(Technician).count()
    except Exception as e:
        logger.error(f"Database query failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    logger.info(f"Retrieved {len(technicians)} technicians (total: {total}) by user {current_user.email}")
    return {
        "technicians": technicians,
        "total": total,
        "page": page,
        "page_size": page_size
    }

@router.get("/{technician_id}", response_model=TechnicianResponse)
async def get_technician(
    technician_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Retrieve details for a specific technician.
    Technicians can only see their own profile, admins can see all.

    Args:
        technician_id (str): The ID of the technician.
        db (Session): The database session.
        current_user (User): The authenticated user.

    Returns:
        TechnicianResponse: The technician details.

    Raises:
        HTTPException: If the technician is not found or the user is not authorized.
    """
    logger.info(f"Retrieving technician {technician_id} by user {current_user.email}")

    try:
        technician = db.query(Technician).filter(Technician.id == technician_id).first()
        if not technician:
            logger.error(f"Technician {technician_id} not found")
            raise HTTPException(status_code=404, detail="Technician not found")
    except Exception as e:
        logger.error(f"Database query failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    # Role-based access
    if current_user.role == UserRole.TECHNICIAN and technician.id != current_user.id:
        logger.error(f"Technician {current_user.email} not authorized to view technician {technician_id}")
        raise HTTPException(status_code=403, detail="Not authorized to view this technician")
    if current_user.role == UserRole.CUSTOMER:
        logger.error(f"Customer {current_user.email} not authorized to view technicians")
        raise HTTPException(status_code=403, detail="Not authorized to view technicians")

    logger.info(f"Technician {technician_id} retrieved successfully by user {current_user.email}")
    return technician

@router.put("/{technician_id}", response_model=TechnicianResponse)
async def update_technician(
    technician_id: str,
    technician_update: TechnicianUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Update a technician's details.
    Technicians can update their own profile, admins can update any.

    Args:
        technician_id (str): The ID of the technician to update.
        technician_update (TechnicianUpdate): The updated technician details.
        db (Session): The database session.
        current_user (User): The authenticated user.

    Returns:
        TechnicianResponse: The updated technician.

    Raises:
        HTTPException: If the technician is not found, the user is not authorized, or the update fails.
    """
    logger.info(f"Updating technician {technician_id} by user {current_user.email}")

    try:
        db_technician = db.query(Technician).filter(Technician.id == technician_id).first()
        if not db_technician:
            logger.error(f"Technician {technician_id} not found")
            raise HTTPException(status_code=404, detail="Technician not found")

        # Role-based access
        if current_user.role == UserRole.TECHNICIAN and db_technician.id != current_user.id:
            logger.error(f"Technician {current_user.email} not authorized to update technician {technician_id}")
            raise HTTPException(status_code=403, detail="Not authorized to update this technician")
        if current_user.role == UserRole.CUSTOMER:
            logger.error(f"Customer {current_user.email} not authorized to update technicians")
            raise HTTPException(status_code=403, detail="Not authorized to update technicians")

        if technician_update.name:
            db_technician.name = technician_update.name
        if technician_update.email is not None:
            db_technician.email = technician_update.email
        if technician_update.phone is not None:
            db_technician.phone = technician_update.phone
        if technician_update.lat is not None:
            db_technician.lat = technician_update.lat
        if technician_update.lon is not None:
            db_technician.lon = technician_update.lon
        if technician_update.skills is not None:
            db_technician.skills = technician_update.skills

        db.commit()
        db.refresh(db_technician)
    except Exception as e:
        db.rollback()
        logger.error(f"Database update failed for technician {technician_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    logger.info(f"Technician {technician_id} updated successfully by user {current_user.email}")
    return db_technician