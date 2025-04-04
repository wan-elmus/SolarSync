from sqlalchemy import Column, String, Float, CheckConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base

class Technician(Base):
    """
    SQLAlchemy model for a technician in the SolarSync system.

    Represents a technician who can be assigned to jobs for installation or maintenance.
    """
    __tablename__ = "technicians"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    login = Column(String, unique=True, nullable=False)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    lat = Column(Float, nullable=True)
    lon = Column(Float, nullable=True)
    skills = Column(String, nullable=True)  # e.g., "hybrid,installation"

    # Relationships
    jobs = relationship("Job", back_populates="technician")

    # Table-level constraints
    __table_args__ = (
        CheckConstraint("lat >= -90 AND lat <= 90", name="check_lat_range"),
        CheckConstraint("lon >= -180 AND lon <= 180", name="check_lon_range"),
    )