from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from app.core.database import get_db
from app.services.sizing_service import calculate_sizing
from app.core.auth import get_current_active_user, get_current_customer
from app.models.user import User, UserRole
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/sizing", tags=["sizing"])

class SizingRequest(BaseModel):
    system_type: str = Field(..., description="Type of solar system ('pure' or 'hybrid')")
    load_demand_kwh: float = Field(..., gt=0, description="Daily energy demand in kWh")
    position: dict = Field(..., description="Location coordinates (e.g., {'lat': -1.2699, 'lon': 36.8408})")

class SizingResponse(BaseModel):
    panel_capacity_kw: float
    battery_capacity_kwh: float
    inverter_capacity_kw: float
    daily_output_kwh: float
    excess_kwh: float
    panel_cost_ksh: float
    battery_cost_ksh: float
    inverter_cost_ksh: float
    installation_cost_ksh: float
    total_cost_ksh: float
    roi_years: float
    system_efficiency: float
    peak_sun_hours: float  # Added to match expected fields

@router.post("/calculate", response_model=SizingResponse)
async def calculate_sizing_endpoint(
    request: SizingRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Calculate sizing metrics for a solar grid-tie system independently of a job.
    Only customers and admins can calculate sizing.

    Args:
        request (SizingRequest): The sizing parameters.
        db (Session): The database session (used by calculate_sizing for weather data).
        current_user (User): The authenticated user.

    Returns:
        SizingResponse: The calculated sizing metrics.

    Raises:
        HTTPException: If the input is invalid, the user is not authorized, or the calculation fails.
    """
    logger.info(f"Calculating sizing: system_type={request.system_type}, load_demand_kwh={request.load_demand_kwh} by user {current_user.email}")

    # Role-based access
    if current_user.role not in [UserRole.CUSTOMER, UserRole.ADMIN]:
        logger.error(f"User {current_user.email} not authorized to calculate sizing")
        raise HTTPException(status_code=403, detail="Not authorized to calculate sizing")

    # Validate system_type
    if request.system_type not in ["pure", "hybrid"]:
        logger.error(f"Invalid system_type: {request.system_type}")
        raise HTTPException(status_code=400, detail="system_type must be 'pure' or 'hybrid'")

    # Validate position
    if not all(key in request.position for key in ["lat", "lon"]):
        logger.error("Invalid position format in sizing request")
        raise HTTPException(status_code=400, detail="Position must contain 'lat' and 'lon' keys")

    # Calculate sizing
    try:
        result = calculate_sizing(
            system_type=request.system_type,
            load_demand_kwh=request.load_demand_kwh,
            position=request.position,
            db=db
        )
    except Exception as e:
        logger.error(f"Sizing calculation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Sizing calculation failed: {str(e)}")

    logger.info(f"Sizing calculation completed: total_cost_ksh={result['total_cost_ksh']}, roi_years={result['roi_years']} by user {current_user.email}")
    return result