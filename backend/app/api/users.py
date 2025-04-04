from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field, EmailStr
from app.core.database import get_db
from app.models.user import User, UserRole
from app.core.auth import get_current_active_user, get_current_admin
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/users", tags=["users"])

class UserCreate(BaseModel):
    email: EmailStr = Field(..., description="User's email address (must be unique)")
    first_name: str = Field(..., description="User's first name")
    last_name: Optional[str] = None
    phone: Optional[str] = None

class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = None  # Only admins can update this

class UserResponse(BaseModel):
    id: str
    email: str
    first_name: str
    last_name: Optional[str]
    phone: Optional[str]
    role: str
    is_active: bool

    class Config:
        orm_mode = True

class UserListResponse(BaseModel):
    users: List[UserResponse]
    total: int
    page: int
    page_size: int

@router.post("/create", response_model=UserResponse)
async def create_user(
    user: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Create a new user.
    Only admins can create users.

    Args:
        user (UserCreate): The user details.
        db (Session): The database session.
        current_user (User): The authenticated user (must be admin).

    Returns:
        UserResponse: The created user.

    Raises:
        HTTPException: If the user creation fails.
    """
    logger.info(f"Creating user with email: {user.email} by user {current_user.email}")

    # Check if email already exists
    try:
        existing_user = db.query(User).filter(User.email == user.email).first()
        if existing_user:
            logger.error(f"User with email {user.email} already exists")
            raise HTTPException(status_code=400, detail="User with this email already exists")
    except Exception as e:
        logger.error(f"Database query failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    # Create new user
    try:
        # Since /auth/signup handles password and role, this endpoint assumes a default role
        # We'll set a dummy password since it should be set via /auth/signup
        from app.core.auth import get_password_hash
        db_user = User(
            id=f"user-{user.email.split('@')[0]}-{int(datetime.utcnow().timestamp())}",
            email=user.email,
            hashed_password=get_password_hash("temporarypassword"),  # Should be set via /auth/signup
            first_name=user.first_name,
            last_name=user.last_name,
            phone=user.phone,
            role=UserRole.CUSTOMER,  # Default role, should be set via /auth/signup
            is_active=True
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create user: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    logger.info(f"User {db_user.id} created successfully by user {current_user.email}")
    return db_user

@router.get("/list", response_model=UserListResponse)
async def list_users(
    page: int = 1,
    page_size: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    List all users with pagination.
    Only admins can list users.

    Args:
        page (int): The page number (default: 1).
        page_size (int): The number of users per page (default: 10).
        db (Session): The database session.
        current_user (User): The authenticated user (must be admin).

    Returns:
        UserListResponse: A paginated list of users.
    """
    logger.info(f"Listing users: page={page}, page_size={page_size} by user {current_user.email}")

    try:
        offset = (page - 1) * page_size
        users = db.query(User).offset(offset).limit(page_size).all()
        total = db.query(User).count()
    except Exception as e:
        logger.error(f"Database query failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    logger.info(f"Retrieved {len(users)} users (total: {total}) by user {current_user.email}")
    return {
        "users": users,
        "total": total,
        "page": page,
        "page_size": page_size
    }

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Retrieve details for a specific user.
    Users can only see their own profile, admins can see all.

    Args:
        user_id (str): The ID of the user.
        db (Session): The database session.
        current_user (User): The authenticated user.

    Returns:
        UserResponse: The user details.

    Raises:
        HTTPException: If the user is not found or the current user is not authorized.
    """
    logger.info(f"Retrieving user {user_id} by user {current_user.email}")

    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.error(f"User {user_id} not found")
            raise HTTPException(status_code=404, detail="User not found")
    except Exception as e:
        logger.error(f"Database query failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    # Role-based access
    if current_user.role != UserRole.ADMIN and user.id != current_user.id:
        logger.error(f"User {current_user.email} not authorized to view user {user_id}")
        raise HTTPException(status_code=403, detail="Not authorized to view this user")

    logger.info(f"User {user_id} retrieved successfully by user {current_user.email}")
    return user

@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Update a user's details.
    Users can update their own profile, admins can update any (including is_active).

    Args:
        user_id (str): The ID of the user to update.
        user_update (UserUpdate): The updated user details.
        db (Session): The database session.
        current_user (User): The authenticated user.

    Returns:
        UserResponse: The updated user.

    Raises:
        HTTPException: If the user is not found, the current user is not authorized, or the update fails.
    """
    logger.info(f"Updating user {user_id} by user {current_user.email}")

    try:
        db_user = db.query(User).filter(User.id == user_id).first()
        if not db_user:
            logger.error(f"User {user_id} not found")
            raise HTTPException(status_code=404, detail="User not found")

        # Role-based access
        if current_user.role != UserRole.ADMIN and db_user.id != current_user.id:
            logger.error(f"User {current_user.email} not authorized to update user {user_id}")
            raise HTTPException(status_code=403, detail="Not authorized to update this user")

        if user_update.first_name:
            db_user.first_name = user_update.first_name
        if user_update.last_name is not None:
            db_user.last_name = user_update.last_name
        if user_update.phone is not None:
            db_user.phone = user_update.phone
        if user_update.is_active is not None:
            if current_user.role != UserRole.ADMIN:
                logger.error(f"User {current_user.email} not authorized to update is_active")
                raise HTTPException(status_code=403, detail="Not authorized to update is_active")
            db_user.is_active = user_update.is_active

        db.commit()
        db.refresh(db_user)
    except Exception as e:
        db.rollback()
        logger.error(f"Database update failed for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    logger.info(f"User {user_id} updated successfully by user {current_user.email}")
    return db_user