from langgraph.graph import StateGraph, END
from app.core.state import JobState
from app.agents.job_completion_agent import job_completion_agent
from app.agents.notification_agent import notification_agent
from app.agents.supervisor_agent import supervisor_agent
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def build_job_completion_workflow():
    """
    Build a LangGraph workflow for handling job completion and feedback.

    The workflow marks the job as completed, collects feedback from the technician,
    and notifies the customer of the job status.

    Returns:
        Compiled LangGraph workflow.
    """
    workflow = StateGraph(JobState)

    # Define nodes
    workflow.add_node("job_completion_agent", job_completion_agent)
    workflow.add_node("notification_agent", notification_agent)

    # Define edges
    workflow.set_entry_point("job_completion_agent")
    workflow.add_conditional_edges(
        "job_completion_agent",
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
            "END": END
        }
    )

    # Compile the workflow with error handling
    compiled_workflow = workflow.compile()
    
    # Log workflow creation
    logger.info("Job completion workflow compiled successfully")
    return compiled_workflow

# Global instance of the workflow
job_completion_workflow = build_job_completion_workflow()

# Add an async run method to handle async agents
async def run_workflow(state: JobState):
    """
    Asynchronously run the job completion workflow.

    Args:
        state (JobState): The initial state of the job.

    Returns:
        dict: The result of the workflow execution.
    """
    try:
        config = {"configurable": {"db": state.get("db")}}  # Extract db from state
        result = await job_completion_workflow.ainvoke(state, config)
        logger.info(f"Job completion workflow completed for job {state.get('job_id', 'unknown')}")
        return result
    except Exception as e:
        logger.error(f"Job completion workflow failed for job {state.get('job_id', 'unknown')}: {str(e)}")
        raise

# Attach the async run method to the workflow
job_completion_workflow.run = run_workflow