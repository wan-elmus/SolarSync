# SUMMARY

This folder contains LangGraph workflows that orchestrate the processing of jobs in the SolarSync system. These workflows manage the lifecycle of a job, from creation to completion, by coordinating various agents that perform specific tasks (e.g., sizing, triaging, notifications).

## 1. Job Workflow (job_workflow.py)

Manages the creation, sizing, triaging, technician assignment, and initial notifications for a solar system job.

    How It Achieves This
        Defines a LangGraph workflow with nodes for job creation (job_creator), sizing (sizing_agent), AI predictions (ai_prediction_agent), technician assignment (technician_assignment_agent), notifications (notification_agent), and weather updates (weather_update_agent).
        Uses a supervisor_agent to decide the next step after each node, allowing conditional transitions (e.g., to END if a step fails).

    Key Features
        Supports independent sizing and triaging (e.g., a job can end after sizing if triaging isn’t needed).
        Includes a loop from weather_update_agent to sizing_agent for re-sizing based on weather changes, controlled by the supervisor_agent to prevent infinite loops (assumes a counter in JobState).
        Includes logging for observability.

## 2. Job Completion Workflow (job_completion_workflow.py)

Handles post-assignment tasks, such as marking the job as completed and notifying the customer.

    How It Achieves This
        Defines a LangGraph workflow with nodes for job completion (job_completion_agent) and notifications (notification_agent).
        Uses a supervisor_agent to decide the next step after each node.

    Key Features
        Updates the job status to "completed" and collects feedback (via job_completion_agent).
        Sends a final notification to the customer (via notification_agent).
        Includes logging for observability.

        