from langgraph.graph import StateGraph, END
from app.core.state import JobState
from app.agents.job_creator import job_creator
from app.agents.sizing_agent import sizing_agent
from app.agents.ai_prediction_agent import ai_prediction_agent
from app.agents.technician_assignment_agent import technician_assignment_agent
from app.agents.notification_agent import notification_agent
from app.agents.weather_update_agent import weather_update_agent
from app.agents.supervisor_agent import supervisor_agent
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def build_job_workflow():
    """
    Build a LangGraph workflow for processing a solar system job.

    The workflow handles job creation, sizing, AI predictions, technician assignment,
    notifications, and weather updates. It uses a supervisor agent to decide
    the next step after each node.

    Returns:
        Compiled LangGraph workflow.
    """
    workflow = StateGraph(JobState)

    # Define nodes
    workflow.add_node("job_creator", job_creator)
    workflow.add_node("sizing_agent", sizing_agent)
    workflow.add_node("ai_prediction_agent", ai_prediction_agent)
    workflow.add_node("technician_assignment_agent", technician_assignment_agent)
    workflow.add_node("notification_agent", notification_agent)
    workflow.add_node("weather_update_agent", weather_update_agent)

    # Define edges
    workflow.set_entry_point("job_creator")
    workflow.add_conditional_edges(
        "job_creator",
        supervisor_agent,
        {
            "sizing_agent": "sizing_agent",
            "END": END
        }
    )
    workflow.add_conditional_edges(
        "sizing_agent",
        supervisor_agent,
        {
            "ai_prediction_agent": "ai_prediction_agent",
            "END": END
        }
    )
    workflow.add_conditional_edges(
        "ai_prediction_agent",
        supervisor_agent,
        {
            "technician_assignment_agent": "technician_assignment_agent",
            "END": END
        }
    )
    workflow.add_conditional_edges(
        "technician_assignment_agent",
        supervisor_agent,
        {
            "notification_agent": "notification_agent",
            "END": END
        }
    )
    workflow.add_conditional_edges(
        "notification_agent",
        supervisor_agent,
        {
            "weather_update_agent": "weather_update_agent",
            "sizing_agent": "sizing_agent", 
            "END": END
        }
    )
    workflow.add_conditional_edges(
        "weather_update_agent",
        supervisor_agent,
        {
            "sizing_agent": "sizing_agent", 
            "END": END
        }
    )

    # Compile the workflow with error handling
    compiled_workflow = workflow.compile()
    
    # Log workflow creation
    logger.info("Job workflow compiled successfully")
    return compiled_workflow

# Global instance of the workflow
job_workflow = build_job_workflow()

# Add an async invoke method to handle async agents
async def invoke_workflow(state: JobState, config: dict):
    """
    Asynchronously invoke the job workflow.

    Args:
        state (JobState): The initial state of the job.
        config (dict): Configuration dictionary containing the database session ('db').

    Returns:
        JobState: The final state after the workflow execution.
    """
    try:
        final_state = await job_workflow.ainvoke(state, config)
        logger.info(f"Job workflow completed for job {state.get('job_id', 'unknown')}")
        return final_state
    except Exception as e:
        logger.error(f"Job workflow failed for job {state.get('job_id', 'unknown')}: {str(e)}")
        raise

# Attach the async invoke method to the workflow
job_workflow.invoke = invoke_workflow