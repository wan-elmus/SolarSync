# SUMMARY

This folder contains the individual agents that make up the LangGraph workflow for SolarSync. Each agent is a node in the workflow, responsible for a specific task in the process of managing solar grid-tie system jobs. The agents collaborate by updating a shared JobState and interacting with the database, external APIs, and AI models. The supervisor_agent orchestrates the flow between agents.

## 1. AI Prediction Agent (ai_prediction_agent.py)

It uses AI to predict job details such as priority, technician assignment, and diagnostics.

    Inputs
        state["description"]: The job description (e.g., "GRID TIE OFFLINE").
        state["system_type"]: The type of solar system ("pure" or "hybrid").
        state["job_id"]: The unique ID of the job.

    Actions
        Calls predict_job_details from ai_service.py to get AI predictions.
        Updates the JobState with predicted values (priority, technician_id, diagnosis).
        Saves the predictions to the predictions table in the database.
        Updates the jobs table with the predicted priority and technician_id.

    Outputs
        Updated JobState with AI prediction results.
        Database entries in predictions and jobs tables.

    Error Handling
        Skips execution if required fields are missing.
        Handles AI prediction failures and database errors, logging issues and continuing the workflow.

## 2. Job Creator Agent (job_creator.py)

It initializes a new job in the database and sets up the initial JobState.

    Inputs
        state: Contains job details provided by the user (e.g., description, system_type, load_demand_kwh, etc.).
    
    Actions
        Generates a unique job_id using uuid.
        Creates a new Job record in the database with the provided details.
        Sets the initial status to "pending".
        Updates the JobState with the job_id, status, and date_created.

    Outputs
        Updated JobState with the new job_id and status.
        A new record in the jobs table.

    Error Handling
        Validates required fields (description, system_type).
        Handles database errors, rolling back the transaction if the commit fails.

## 3. Notification Agent (notification_agent.py)

It sends an SMS notification to the technician about the job schedule.

    Inputs
        state["technician_id"]: The ID of the assigned technician.
        state["contact_mobile"]: The technician’s mobile number.
        state["job_id"]: The job ID.
        state["scheduled_start"]: The scheduled start date (optional).

    Actions
        Constructs an SMS message with the job ID and scheduled start date.
        Sends the SMS using send_sms from sms_service.py, with retry logic (up to 3 attempts).

    Outputs
        Updated JobState with a message indicating whether the SMS was sent or failed.

    Error Handling
        Skips execution if required fields are missing.
        Retries SMS sending on failure, logging each attempt.

## 4. Sizing Agent (sizing_agent.py)

It calculates sizing metrics for the solar grid-tie system (e.g., panel capacity, costs, ROI).

    Inputs
        state["system_type"]: The type of solar system.
        state["load_demand_kwh"]: The daily energy demand.
        state["position"]: The job location (latitude and longitude).
        state["job_id"]: The job ID.

    Actions
        Calls calculate_sizing from sizing_service.py to compute metrics like panel_capacity_kw, total_cost_ksh, and roi_years.
        Updates the JobState with sizing results.
        Updates the jobs table with the sizing metrics.

    Outputs
        Updated JobState with sizing results.
        Updated record in the jobs table.

    Error Handling
        Validates required fields.
        Handles sizing calculation failures and database errors, logging issues.

## 5. Supervisor Agent (supervisor_agent.py)

It orchestrates the LangGraph workflow by determining the next agent to run.

    Inputs
        state["messages"]: The list of messages from previous agents.
        state["priority"]: The job priority (set by the AI Prediction Agent).

    Actions
        Examines the last message in state["messages"] to determine the current stage of the workflow.
        Routes to the next agent based on the workflow state:
            After job_creator: Routes to sizing_agent.
            After sizing_agent: Routes to ai_prediction_agent.
            After ai_prediction_agent: Routes to technician_assignment_agent.
            After technician_assignment_agent: Routes to notification_agent.
            After notification_agent: Routes to weather_update_agent.
            After weather_update_agent: Routes to sizing_agent if re-sizing is triggered, otherwise ends the workflow.
        Handles special cases, such as high-priority jobs needing immediate notification.

    Outputs
        A string indicating the next agent to run or "END" to terminate the workflow.

    Error Handling
        Handles empty messages list to prevent crashes.
        Logs routing decisions for debugging.

## 6. Technician Assignment Agent (technician_assignment_agent.py)

It assigns a technician to the job based on the AI-predicted technician_id.

    Inputs
        state["technician_id"]: The ID of the technician predicted by the AI.
        state["job_id"]: The job ID.

    Actions
        Queries the technicians table to get the technician’s details.
        Updates the jobs table with the technician’s name and login.
        Updates the JobState with the technician’s details.

    Outputs
        Updated JobState with technician details.
        Updated record in the jobs table.

    Error Handling
        Validates required fields.
        Handles cases where the technician or job is not found.
        Handles database errors.

## 7. Weather Update Agent (weather_update_agent.py)

It monitors weather changes and triggers re-sizing if peak_sun_hours changes significantly.

    Inputs
        state["position"]: The job location (latitude and longitude).
        state["last_peak_sun_hours"]: The last known peak_sun_hours.
        state["last_weather_check"]: The timestamp of the last weather check.
        state["job_id"]: The job ID.

    Actions
        Checks if 30 minutes have passed since the last weather check.
        Fetches the latest peak_sun_hours using get_peak_sun_hours from weather_service.py.
        Compares the new peak_sun_hours with the last known value.
        If the change is greater than 5%, updates the state and triggers re-sizing.

    Outputs
        Updated JobState with the latest peak_sun_hours and weather check timestamp.

    Error Handling
        Validates required fields.
        Handles weather API failures and invalid timestamp formats.
        