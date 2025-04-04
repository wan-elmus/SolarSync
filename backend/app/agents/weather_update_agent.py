from sqlalchemy.orm import Session
from app.core.state import JobState
from app.services.weather_service import get_peak_sun_hours
from datetime import datetime, timedelta
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def weather_update_agent(state: JobState, db: Session) -> JobState:
    """
    Check for weather updates and trigger re-sizing if peak_sun_hours changes significantly.
    
    Args:
        state (JobState): The current state of the job in the LangGraph workflow.
        db (Session): The database session (not used directly but passed for consistency).
    
    Returns:
        JobState: The updated state with weather check results.
    """
    # Validate required fields
    if not state.get("position") or "lat" not in state["position"] or "lon" not in state["position"] or not state.get("job_id"):
        state["messages"].append({"agent": "weather_update_agent", "message": "Skipping weather update: missing position or job_id"})
        logger.warning(f"Job {state.get('job_id', 'unknown')} missing position or job_id for weather update")
        return state

    last_check = state.get("last_weather_check")
    if last_check:
        try:
            last_check_time = datetime.fromisoformat(last_check)
            if (datetime.utcnow() - last_check_time) < timedelta(minutes=30):
                state["messages"].append({"agent": "weather_update_agent", "message": "Skipping weather update: too soon"})
                logger.info(f"Job {state['job_id']} weather update skipped: too soon")
                return state
        except ValueError as e:
            state["messages"].append({"agent": "weather_update_agent", "message": f"Invalid last_weather_check format: {str(e)}"})
            logger.error(f"Job {state['job_id']} has invalid last_weather_check format: {str(e)}")

    # Fetch the latest peak_sun_hours
    try:
        lat = state["position"]["lat"]
        lon = state["position"]["lon"]
        current_peak_sun_hours = get_peak_sun_hours(lat, lon)
    except Exception as e:
        state["messages"].append({"agent": "weather_update_agent", "message": f"Failed to fetch weather data: {str(e)}"})
        logger.error(f"Job {state['job_id']} failed to fetch weather data: {str(e)}")
        return state

    # Update the last weather check timestamp
    state["last_weather_check"] = datetime.utcnow().isoformat()

    # Compare with the last known peak_sun_hours
    last_peak_sun_hours = state.get("last_peak_sun_hours")
    if last_peak_sun_hours is None:
        # First weather check, set the baseline
        state["last_peak_sun_hours"] = current_peak_sun_hours
        state["messages"].append({"agent": "weather_update_agent", "message": f"Initial weather check: peak_sun_hours = {current_peak_sun_hours}"})
        logger.info(f"Job {state['job_id']} initial weather check: peak_sun_hours = {current_peak_sun_hours}")
        return state

    # Check if peak_sun_hours has changed significantly (e.g., by more than 5%)
    change_percentage = abs(current_peak_sun_hours - last_peak_sun_hours) / last_peak_sun_hours * 100 if last_peak_sun_hours != 0 else 100
    if change_percentage > 5:
        state["peak_sun_hours"] = current_peak_sun_hours
        state["last_peak_sun_hours"] = current_peak_sun_hours
        state["messages"].append({"agent": "weather_update_agent", "message": f"peak_sun_hours changed by {change_percentage:.2f}% to {current_peak_sun_hours}, triggering re-sizing"})
        logger.info(f"Job {state['job_id']} peak_sun_hours changed by {change_percentage:.2f}% to {current_peak_sun_hours}, triggering re-sizing")
    else:
        state["messages"].append({"agent": "weather_update_agent", "message": f"peak_sun_hours unchanged: {current_peak_sun_hours}"})
        logger.info(f"Job {state['job_id']} peak_sun_hours unchanged: {current_peak_sun_hours}")
        return state

    return state