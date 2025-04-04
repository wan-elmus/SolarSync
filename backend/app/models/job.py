from sqlalchemy import Column, Index, String, Float, Boolean, DateTime, JSON, ForeignKey, Enum, CheckConstraint, Integer
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime
import enum



class JobStatus(enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"

class SystemType(enum.Enum):
    PURE = "pure"
    HYBRID = "hybrid"

class Job(Base):
    """
    SQLAlchemy model for a job in the SolarSync system.

    Represents a solar grid-tie system job, including details for sizing and triaging.
    """
    __tablename__ = "jobs"

    id = Column(String, primary_key=True, index=True)
    description = Column(String, nullable=False)  # Required for workflow
    priority = Column(String, nullable=True)
    customer = Column(JSON, nullable=True)
    system_type = Column(Enum(SystemType), nullable=False)  # Required for workflow
    load_demand_kwh = Column(Float, nullable=False)  # Required for workflow
    appliances = Column(JSON, nullable=True)  # Added: List of appliances with power ratings, quantities, and runtimes
    peak_sun_hours = Column(Float, nullable=True)
    panel_capacity_kw = Column(Float, nullable=True)
    battery_capacity_kwh = Column(Float, nullable=True)
    inverter_capacity_kw = Column(Float, nullable=True)
    daily_output_kwh = Column(Float, nullable=True)
    excess_kwh = Column(Float, nullable=True)
    panel_cost_ksh = Column(Float, nullable=True)
    battery_cost_ksh = Column(Float, nullable=True)
    inverter_cost_ksh = Column(Float, nullable=True)
    installation_cost_ksh = Column(Float, nullable=True)
    total_cost_ksh = Column(Float, nullable=True)
    roi_years = Column(Float, nullable=True)
    system_efficiency = Column(Float, nullable=True)
    site = Column(String, nullable=True)
    equipment = Column(JSON, nullable=True)
    project = Column(JSON, nullable=True)
    type = Column(String, nullable=True)
    report_template = Column(String, nullable=True)
    created_by = Column(JSON, nullable=True)
    address_street = Column(String, nullable=True)
    address_province = Column(String, nullable=True)
    address_city = Column(String, nullable=True)
    address_zip = Column(String, nullable=True)
    address_country = Column(String, nullable=True)
    address = Column(String, nullable=True)
    address_complement = Column(String, nullable=True)
    contact_first_name = Column(String, nullable=True)
    contact_last_name = Column(String, nullable=True)
    contact_mobile = Column(String, nullable=True)
    contact_phone = Column(String, nullable=True)
    contact_email = Column(String, nullable=True)
    status = Column(Enum(JobStatus), nullable=True, default=JobStatus.PENDING)
    public_link = Column(String, nullable=True)
    technician_id = Column(String, ForeignKey("users.id"), nullable=True)  # Updated to reference users table
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    scheduled_start = Column(DateTime, nullable=True)
    scheduled_end = Column(DateTime, nullable=True)
    actual_start = Column(DateTime, nullable=True)
    actual_end = Column(DateTime, nullable=True)
    created_by_customer = Column(Boolean, nullable=True)
    position = Column(JSON, nullable=False)  # Required for workflow
    custom_field_values = Column(JSON, nullable=True)
    date_created = Column(DateTime, nullable=False, default=datetime.utcnow)
    date_modified = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    preferences = Column(JSON, nullable=True)
    job_type = Column(String, nullable=True)
    # Added fields for detailed sizing results
    panels_required = Column(Integer, nullable=True)  # Number of panels required
    lead_acid_batteries_required = Column(Integer, nullable=True)  # Number of Lead Acid batteries required
    lithium_ion_batteries_required = Column(Integer, nullable=True)  # Number of Lithium-Ion batteries required
    inverters_required = Column(Integer, nullable=True)  # Number of inverters required
    lead_acid_batteries_series = Column(Integer, nullable=True)  # Number of Lead Acid batteries in series
    lead_acid_batteries_parallel = Column(Integer, nullable=True)  # Number of Lead Acid batteries in parallel
    lithium_ion_batteries_series = Column(Integer, nullable=True)  # Number of Lithium-Ion batteries in series
    lithium_ion_batteries_parallel = Column(Integer, nullable=True)  # Number of Lithium-Ion batteries in parallel

    # Relationships
    technician = relationship("User", foreign_keys=[technician_id], back_populates="assigned_jobs")
    user = relationship("User", foreign_keys=[user_id], back_populates="jobs")
    predictions = relationship("Prediction", back_populates="job")

    # Table-level constraints
    __table_args__ = (
        CheckConstraint("load_demand_kwh >= 0", name="check_load_demand_kwh_non_negative"),
        CheckConstraint("peak_sun_hours >= 0", name="check_peak_sun_hours_non_negative"),
        CheckConstraint("panel_capacity_kw >= 0", name="check_panel_capacity_kw_non_negative"),
        CheckConstraint("battery_capacity_kwh >= 0", name="check_battery_capacity_kwh_non_negative"),
        CheckConstraint("inverter_capacity_kw >= 0", name="check_inverter_capacity_kw_non_negative"),
        CheckConstraint("daily_output_kwh >= 0", name="check_daily_output_kwh_non_negative"),
        CheckConstraint("excess_kwh >= 0", name="check_excess_kwh_non_negative"),
        CheckConstraint("panel_cost_ksh >= 0", name="check_panel_cost_ksh_non_negative"),
        CheckConstraint("battery_cost_ksh >= 0", name="check_battery_cost_ksh_non_negative"),
        CheckConstraint("inverter_cost_ksh >= 0", name="check_inverter_cost_ksh_non_negative"),
        CheckConstraint("installation_cost_ksh >= 0", name="check_installation_cost_ksh_non_negative"),
        CheckConstraint("total_cost_ksh >= 0", name="check_total_cost_ksh_non_negative"),
        CheckConstraint("roi_years >= 0", name="check_roi_years_non_negative"),
        CheckConstraint("system_efficiency >= 0", name="check_system_efficiency_non_negative"),
        CheckConstraint("panels_required >= 0", name="check_panels_required_non_negative"),
        CheckConstraint("lead_acid_batteries_required >= 0", name="check_lead_acid_batteries_required_non_negative"),
        CheckConstraint("lithium_ion_batteries_required >= 0", name="check_lithium_ion_batteries_required_non_negative"),
        CheckConstraint("inverters_required >= 0", name="check_inverters_required_non_negative"),
        CheckConstraint("lead_acid_batteries_series >= 0", name="check_lead_acid_batteries_series_non_negative"),
        CheckConstraint("lead_acid_batteries_parallel >= 0", name="check_lead_acid_batteries_parallel_non_negative"),
        CheckConstraint("lithium_ion_batteries_series >= 0", name="check_lithium_ion_batteries_series_non_negative"),
        CheckConstraint("lithium_ion_batteries_parallel >= 0", name="check_lithium_ion_batteries_parallel_non_negative"),
        (Index('ix_jobs_user_id', 'user_id'),),
        (Index('ix_jobs_technician_id', 'technician_id'),),
        (Index('ix_jobs_status', 'status'),),
    )