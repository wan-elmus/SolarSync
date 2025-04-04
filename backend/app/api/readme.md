# SUMMARY

This folder contains FastAPI endpoints that expose the core functionalities of the SolarSync backend. These endpoints allow users to interact with the system for sizing solar grid-tie systems, triaging jobs (e.g., assigning technicians, sending notifications), and managing related entities (users, technicians, predictions, weather updates). The API is designed to support independent sizing and triaging, making it flexible for different use cases.

## 1. Jobs API (jobs.py)

It manages solar grid-tie system jobs, running the full LangGraph workflow for sizing and triaging.

    How It Achieves This
        POST /api/jobs/create: Creates a new job, initializes a JobState, and runs the LangGraph workflow (Job Creator → Sizing → AI Prediction → Technician Assignment → Notification → Weather Update). The final state is saved to Redis, and the job is stored in the database.
        GET /api/jobs/list: Retrieves a paginated list of jobs, including sizing and triaging details (e.g., panel_capacity_kw, technician_name).
        PUT /api/jobs/{job_id}: Updates a job’s status or actual end date, cleaning up Redis state if the job is no longer active.

    Key Features
        Enforces required fields for job creation (e.g., description, system_type).
        Supports pagination for listing jobs.
        Includes error handling, logging, and detailed response models.

## 2. Predictions API (predictions.py)

It provides access to AI-generated predictions for jobs, supporting the triaging functionality.

    How It Achieves This
        GET /api/predictions/job/{job_id}: Retrieves all predictions for a specific job, showing details like priority, estimated duration, and costs.
        GET /api/predictions/list: Lists all predictions with pagination.

    Key Features
        Returns structured prediction data for triaging purposes.
        Supports pagination for scalability.
        Includes error handling and logging.

## 3. Sizing API (sizing.py)

It provides standalone sizing calculations for solar grid-tie systems, independent of the job workflow.

    How It Achieves This
        POST /api/sizing/calculate: Takes system_type, load_demand_kwh, and position as input, calls calculate_sizing from sizing_service.py, and returns detailed sizing metrics (e.g., panel_capacity_kw, total_cost_ksh).

    Key Features
        Validates inputs (e.g., system_type must be "pure" or "hybrid").
        Operates independently of jobs, making it accessible for users who only need sizing.
        Includes error handling, logging, and a clear response model.

## 4. Technicians API (technicians.py)

It manages technicians, who are assigned to jobs during the triaging process.

    How It Achieves This
        POST /api/technicians/create: Creates a new technician with a unique login.
        GET /api/technicians/list: Lists all technicians with pagination.
        GET /api/technicians/{technician_id}: Retrieves details for a specific technician.
        PUT /api/technicians/{technician_id}: Updates a technician’s details.

    Key Features
        Ensures unique logins for technicians.
        Supports pagination for listing technicians.
        Includes error handling, logging, and detailed response models.

## 4. Users API (users.py)

Manages users (e.g., customers, admins) who interact with the system.

    How It Achieves This
        POST /api/users/create: Creates a new user with a unique email and specified role.
        GET /api/users/list: Lists all users with pagination.
        GET /api/users/{user_id}: Retrieves details for a specific user.
        PUT /api/users/{user_id}: Updates a user’s details.

    Key Features
        Ensures unique emails for users.
        Validates roles ("customer" or "admin").
        Supports pagination for listing users.
        Includes error handling, logging, and detailed response models.

## 5. Weather API (weather.py)

Triggers weather updates for active jobs, supporting dynamic re-sizing based on weather changes.

    How It Achieves This
        POST /api/weather/update-all: Fetches all active jobs (status in ["pending", "in_progress"]), schedules a background task (run_weather_update) for each job to run the Weather Update Agent via the LangGraph workflow, and updates the job state in Redis.

    Key Features
        Uses background tasks to handle weather updates asynchronously.
        Creates a new database session for each background task to avoid session conflicts.
        Includes error handling, logging, and a structured response model.

        