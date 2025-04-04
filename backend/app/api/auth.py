from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel, EmailStr
from app.core.database import get_db
from datetime import datetime, timedelta
from app.core.auth import (
    authenticate_user, create_access_token, get_current_active_user,
    get_password_hash, ACCESS_TOKEN_EXPIRE_MINUTES
)
from app.models.user import User, UserRole
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["auth"])  # Updated prefix and tags

# Pydantic models
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: Optional[str] = None  # Made optional to match User model
    phone: Optional[str] = None
    role: UserRole = UserRole.CUSTOMER

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

class Token(BaseModel):
    access_token: str
    token_type: str

@router.post("/signup", response_model=UserResponse, status_code=201)
async def signup(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user (customer, technician, or admin).

    Args:
        user_data (UserCreate): The user details.
        db (Session): The database session.

    Returns:
        UserResponse: The created user.

    Raises:
        HTTPException: If the email is already registered.
    """
    logger.info(f"Signing up user with email: {user_data.email}")

    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        logger.error(f"User with email {user_data.email} already exists")
        raise HTTPException(status_code=400, detail="Email already registered")

    # Create new user
    hashed_password = get_password_hash(user_data.password)
    user = User(
        id=f"user-{user_data.email.split('@')[0]}-{int(datetime.utcnow().timestamp())}",  # Generate a unique ID
        email=user_data.email,
        hashed_password=hashed_password,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        phone=user_data.phone,
        role=user_data.role,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    logger.info(f"User {user.email} signed up with role {user.role}")
    return user

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Authenticate a user and return a JWT token.

    Args:
        form_data (OAuth2PasswordRequestForm): The login form data (username and password).
        db (Session): The database session.

    Returns:
        Token: The JWT access token.

    Raises:
        HTTPException: If authentication fails.
    """
    logger.info(f"Login attempt for email: {form_data.username}")
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        logger.error(f"Login failed for email: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    logger.info(f"User {user.email} logged in successfully")
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """
    Retrieve the authenticated user's details.

    Args:
        current_user (User): The authenticated user.

    Returns:
        UserResponse: The user's details.
    """
    logger.info(f"User {current_user.email} accessed their profile")
    return current_user