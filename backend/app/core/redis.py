import redis
from app.core.config import config
import json
from app.core.state import JobState
import logging
from typing import Optional

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Redis client
try:
    redis_client = redis.Redis.from_url(config.REDIS_URL, decode_responses=True)
    # Test the connection
    redis_client.ping()
    logger.info("Redis client initialized successfully")
except Exception as e:
    logger.critical(f"Failed to initialize Redis client: {str(e)}")
    raise

def save_job_state(job_id: str, state: JobState) -> None:
    """
    Save the JobState to Redis with an expiration time.

    Args:
        job_id (str): The ID of the job.
        state (JobState): The job state to save.

    Raises:
        ValueError: If job_id is empty.
        redis.RedisError: If the Redis operation fails.
    """
    if not job_id:
        logger.error("job_id cannot be empty")
        raise ValueError("job_id cannot be empty")

    try:
        state_json = json.dumps(state, default=str)  # Handle datetime objects
        # Set the key with a 24-hour expiration
        redis_client.setex(f"job_state:{job_id}", 24 * 60 * 60, state_json)
        logger.info(f"Saved state for job {job_id} to Redis with 24-hour expiration")
    except redis.RedisError as e:
        logger.error(f"Error saving state for job {job_id}: {str(e)}")
        raise

def get_job_state(job_id: str) -> Optional[JobState]:
    """
    Retrieve the JobState from Redis.

    Args:
        job_id (str): The ID of the job.

    Returns:
        Optional[JobState]: The job state if found, otherwise None.

    Raises:
        ValueError: If job_id is empty.
        redis.RedisError: If the Redis operation fails.
    """
    if not job_id:
        logger.error("job_id cannot be empty")
        raise ValueError("job_id cannot be empty")

    try:
        state_json = redis_client.get(f"job_state:{job_id}")
        if state_json:
            state = json.loads(state_json)
            logger.debug(f"Retrieved state for job {job_id} from Redis")
            return state
        logger.warning(f"No state found for job {job_id}")
        return None
    except redis.RedisError as e:
        logger.error(f"Error retrieving state for job {job_id}: {str(e)}")
        raise

def delete_job_state(job_id: str) -> None:
    """
    Delete the JobState from Redis.

    Args:
        job_id (str): The ID of the job.

    Raises:
        ValueError: If job_id is empty.
        redis.RedisError: If the Redis operation fails.
    """
    if not job_id:
        logger.error("job_id cannot be empty")
        raise ValueError("job_id cannot be empty")

    try:
        redis_client.delete(f"job_state:{job_id}")
        logger.info(f"Deleted state for job {job_id} from Redis")
    except redis.RedisError as e:
        logger.error(f"Error deleting state for job {job_id}: {str(e)}")
        raise