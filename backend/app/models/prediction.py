from sqlalchemy import Column, String, Integer, Float, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base

class Prediction(Base):
    """
    SQLAlchemy model for a prediction in the SolarSync system.

    Represents an AI-generated prediction for a job, used in the triaging process.
    """
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String, ForeignKey("jobs.id"), nullable=False)
    priority = Column(String, nullable=True, default="medium")
    duration_hours = Column(Float, nullable=True)
    labor_ksh = Column(Float, nullable=True)
    transport_ksh = Column(Float, nullable=True)
    diagnosis = Column(String, nullable=True)

    # Relationships
    job = relationship("Job", back_populates="predictions")

    # Table-level constraints
    __table_args__ = (
        CheckConstraint("duration_hours >= 0", name="check_duration_hours_non_negative"),
        CheckConstraint("labor_ksh >= 0", name="check_labor_ksh_non_negative"),
        CheckConstraint("transport_ksh >= 0", name="check_transport_ksh_non_negative"),
    )