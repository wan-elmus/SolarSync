from sqlalchemy import Column, String, DateTime, Enum, Boolean
from app.core.database import Base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

class UserRole(enum.Enum):
    CUSTOMER = "customer"
    ADMIN = "admin"
    ADMIN = "admin"

class User(Base):
    """
    SQLAlchemy model for a user in the SolarSync system.

    Represents a user (customer or admin) who interacts with the system.
    """
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    role = Column(Enum(UserRole), default=UserRole.CUSTOMER, nullable=False)
    date_created = Column(DateTime, nullable=False, default=datetime.utcnow)
    date_modified = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    jobs = relationship("Job", back_populates="user")
    