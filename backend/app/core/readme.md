# SUMMARY

This folder contains the core utilities and configurations for the SolarSync backend. These utilities provide the foundational functionality needed for the API endpoints, including configuration management, database access, Redis state management, scheduling, security, and workflow state definition. The core components are designed to support independent sizing and triaging while ensuring the system is secure, scalable, and maintainable.

## 1. Configuration (config.py)

Manages environment-specific configuration settings for the application.

    How It Achieves This
        Loads environment variables using dotenv and stores them in a Config class.
        Validates required variables (DATABASE_URL, REDIS_URL, SECRET_KEY) and warns about missing optional variables (e.g., OPENWEATHERMAP_API_KEY).
        Supports different environments (development, testing, production) via the ENVIRONMENT variable.

    Key Features
        Ensures the SECRET_KEY is secure (minimum 32 characters).
        Provides type hints for all configuration variables.
        Includes logging for validation errors and warnings.

## 2. Database (database.py)

Sets up the SQLAlchemy database connection and provides a dependency for database sessions.

    How It Achieves This
        Creates a SQLAlchemy engine with connection pooling (pool_size, max_overflow, etc.) using the DATABASE_URL from config.py.
        Defines a SessionLocal factory for creating database sessions.
        Provides a Base class (DeclarativeBase) for defining database models.
        Implements a get_db dependency that yields a database session and ensures it’s closed after use.

    Key Features
        Uses modern SQLAlchemy practices (e.g., DeclarativeBase instead of deprecated declarative_base).
        Configures connection pooling for production performance.
        Includes error handling and logging for engine creation and session closure.

## 3. Redis (redis.py)

Manages job state storage in Redis for the LangGraph workflow.

    How It Achieves This
        Initializes a Redis client using the REDIS_URL from config.py.
        Provides functions to save (save_job_state), retrieve (get_job_state), and delete (delete_job_state) job states in Redis.
        Serializes JobState objects to JSON for storage and deserializes them on retrieval.

    Key Features
        Sets a 24-hour expiration for job states to prevent stale data.
        Validates job_id to ensure valid Redis keys.
        Includes error handling and logging for Redis operations.

## 4. Scheduler (scheduler.py)

Schedules periodic tasks, such as weather updates for active jobs.

    How It Achieves This
        Initializes a BackgroundScheduler with configuration (e.g., timezone, coalesce, max_instances).
        Defines schedule_weather_updates to schedule a task that runs every 30 minutes, fetching active jobs and running weather updates via run_weather_update (from weather.py).
        Provides shutdown_scheduler to cleanly shut down the scheduler on application shutdown.

    Key Features
        Uses a new database session for each scheduled task to avoid session conflicts.
        Includes error handling and logging for scheduling and shutdown operations.
        Configures the scheduler to prevent multiple instances of the same task.

## 5. Security (security.py)

Provides utilities for password hashing and JWT token management for user authentication.

    How It Achieves This
        Uses passlib to hash and verify passwords (get_password_hash, verify_password).
        Uses jose to create and decode JWT access tokens (create_access_token, decode_access_token).

    Key Features
        Supports secure password hashing with bcrypt.
        Creates JWT tokens with configurable expiration (default: 15 minutes).
        Decodes and verifies JWT tokens for authentication.
        Includes error handling and logging for all operations.

## 6. State (state.py)

Defines the JobState structure for the LangGraph workflow.

    How It Achieves This
        Uses a TypedDict to define the JobState with all fields needed for the workflow (e.g., job details, sizing results, triaging data, messages).
        Integrates with LangGraph via the messages field, annotated with add_messages.

    Key Features
        Provides a comprehensive set of fields for job management, sizing, and triaging.
        Aligns field types with the database schema (e.g., technician_id as str).
        Includes a detailed docstring describing each field.
        Sets a default empty list for messages to ensure initialization.
        