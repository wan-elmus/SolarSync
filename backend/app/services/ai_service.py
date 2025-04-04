from sqlalchemy.orm import Session
from app.models.technician import Technician
from sqlalchemy import func
import logging
from typing import Dict, Any

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def predict_job_details(
    job_id: str,
    description: str,
    system_type: str,
    battery_type: str = None,
    battery_cost_ksh: float = 0.0,
    panel_cost_ksh: float = 0.0,
    inverter_cost_ksh: float = 0.0,
    db: Session = None
) -> Dict[str, Any]:
    """
    Predict job details using a mock AI model (to be replaced with a TensorFlow model).

    Args:
        job_id (str): The ID of the job.
        description (str): The job description (e.g., "GRID TIE OFFLINE").
        system_type (str): The system type ("pure" or "hybrid").
        battery_type (str, optional): The selected battery type ("lead_acid" or "lithium_ion").
        battery_cost_ksh (float, optional): The cost of batteries in KSh.
        panel_cost_ksh (float, optional): The cost of panels in KSh.
        inverter_cost_ksh (float, optional): The cost of inverters in KSh.
        db (Session): The database session.

    Returns:
        Dict[str, Any]: A dictionary containing predicted job details:
            - priority (str): The predicted priority ("high", "medium", "low").
            - duration_hours (float): Estimated duration in hours.
            - labor_ksh (float): Estimated labor cost in KSh.
            - transport_ksh (float): Estimated transport cost in KSh.
            - technician_id (str): The ID of the recommended technician.
            - diagnosis (str): The predicted diagnosis.
    """
    try:
        # Mock AI prediction logic
        is_offline = "offline" in description.lower()
        priority = "high" if is_offline else "medium" if "maintenance" in description.lower() else "low"
        
        # Adjust duration based on system type, battery type, and description
        duration_hours = 6.0 if system_type == "hybrid" else 4.0
        if is_offline:
            duration_hours += 2.0  # Extra time for offline issues
        
        # Adjust duration based on battery type (Lithium-Ion may require less maintenance time)
        if battery_type == "lithium_ion":
            duration_hours *= 0.9  # 10% less time due to simpler maintenance
        elif battery_type == "lead_acid":
            duration_hours *= 1.1  # 10% more time due to more complex maintenance

        # Calculate total equipment cost
        total_equipment_cost_ksh = battery_cost_ksh + panel_cost_ksh + inverter_cost_ksh

        # Adjust labor cost based on duration and equipment cost
        base_labor_rate = 1000.0  # 1000 KSh per hour
        labor_cost_factor = 1.0 + (total_equipment_cost_ksh / 100000.0)  # Increase labor cost for expensive systems
        labor_ksh = duration_hours * base_labor_rate * min(labor_cost_factor, 2.0)  # Cap the factor at 2.0

        # Adjust transport cost based on priority and equipment cost
        base_transport_ksh = 1200.0 if is_offline else 800.0
        transport_cost_factor = 1.0 + (total_equipment_cost_ksh / 200000.0)  # Increase transport cost for expensive systems
        transport_ksh = base_transport_ksh * min(transport_cost_factor, 1.5)  # Cap the factor at 1.5

        # Find a suitable technician based on skills and location
        required_skill = system_type  # e.g., "hybrid" or "pure"
        if battery_type:
            required_skill += f" {battery_type}"  # e.g., "hybrid lithium_ion"
        technician = (
            db.query(Technician)
            .filter(Technician.skills.ilike(f"%{required_skill}%"))
            .order_by(func.random())  # Random selection for now; can be improved with location-based logic
            .first()
        )
        technician_id = technician.id if technician else None
        if not technician:
            logger.warning(f"No technician found with skill '{required_skill}' for job {job_id}")

        # Diagnosis based on description and battery type
        diagnosis = "Check inverter wiring" if is_offline else "Routine maintenance check" if "maintenance" in description.lower() else "System inspection"
        if battery_type == "lead_acid":
            diagnosis += "; inspect Lead Acid battery connections"
        elif battery_type == "lithium_ion":
            diagnosis += "; verify Lithium-Ion battery management system"

        prediction = {
            "priority": priority,
            "duration_hours": duration_hours,
            "labor_ksh": labor_ksh,
            "transport_ksh": transport_ksh,
            "technician_id": technician_id,
            "diagnosis": diagnosis
        }
        logger.info(f"AI prediction for job {job_id}: {prediction}")
        return prediction

    except Exception as e:
        logger.error(f"Error predicting job details for job {job_id}: {str(e)}")
        # Fallback prediction
        return {
            "priority": "medium",
            "duration_hours": 4.0,
            "labor_ksh": 4000.0,
            "transport_ksh": 800.0,
            "technician_id": None,
            "diagnosis": "System inspection"
        }