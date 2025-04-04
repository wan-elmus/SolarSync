from app.core.state import JobState
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def supervisor_agent(state: JobState) -> str:
    """
    Determine the next agent to run in the LangGraph workflow based on the current state.
    
    Args:
        state (JobState): The current state of the job in the LangGraph workflow.
    
    Returns:
        str: The name of the next agent to run, or "END" to terminate the workflow.
    """
    job_id = state.get("job_id", "unknown")

    # Check if messages list is empty
    if not state.get("messages"):
        state["messages"].append({"agent": "supervisor_agent", "message": "No messages in state, ending workflow"})
        logger.warning(f"Job {job_id} has no messages, ending workflow")
        return "END"

    # Check if weather update triggered a re-sizing
    if any("triggering re-sizing" in msg["message"] for msg in state["messages"]):
        logger.info(f"Job {job_id} weather update triggered re-sizing")
        return "sizing_agent"

    # Check if job is high priority and needs immediate notification
    if state.get("priority") == "high" and not any("SMS sent" in msg["message"] for msg in state["messages"]):
        logger.info(f"Job {job_id} is high priority, routing to notification_agent")
        return "notification_agent"

    # Default flow based on the last message
    last_message = state["messages"][-1]
    agent = last_message["agent"]
    message = last_message["message"]

    if agent == "job_creator" and "created" in message:
        logger.info(f"Job {job_id} created, routing to sizing_agent")
        return "sizing_agent"
    elif agent == "sizing_agent" and "Sizing completed" in message:
        logger.info(f"Job {job_id} sizing completed, routing to ai_prediction_agent")
        return "ai_prediction_agent"
    elif agent == "ai_prediction_agent" and "AI predictions completed" in message:
        logger.info(f"Job {job_id} AI predictions completed, routing to technician_assignment_agent")
        return "technician_assignment_agent"
    elif agent == "technician_assignment_agent" and "assigned" in message:
        logger.info(f"Job {job_id} technician assigned, routing to notification_agent")
        return "notification_agent"
    elif agent == "notification_agent" and ("SMS sent" in message or "Max retries reached" in message):
        logger.info(f"Job {job_id} notification completed, routing to weather_update_agent")
        return "weather_update_agent"
    elif agent == "weather_update_agent":
        if "triggering re-sizing" in message:
            logger.info(f"Job {job_id} weather update triggered re-sizing")
            return "sizing_agent"
        logger.info(f"Job {job_id} weather update completed, ending workflow")
        return "END"
    else:
        logger.info(f"Job {job_id} no matching condition, ending workflow")
        return "END"