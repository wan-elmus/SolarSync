from sqlalchemy import Column, String, Integer, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String, ForeignKey("jobs.id"), nullable=False)
    priority = Column(String, nullable=True)
    duration_hours = Column(Float, nullable=True)
    labor_ksh = Column(Float, nullable=True)
    transport_ksh = Column(Float, nullable=True)
    diagnosis = Column(String, nullable=True)

    # Relationships
    job = relationship("Job", back_populates="predictions")