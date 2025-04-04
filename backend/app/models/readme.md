# SUMMARY

This folder contains SQLAlchemy models that define the database schema for the SolarSync backend. These models represent the core entities of the system: jobs, predictions, technicians, and users. They are designed to support independent sizing and triaging functionalities while ensuring data integrity and consistency.

## 1. Job Model (job.py)

Represents a solar grid-tie system job, storing details for sizing and triaging.

    How It Achieves This
        Defines a Job table with fields for job details (e.g., description, system_type), sizing results (e.g., panel_capacity_kw, total_cost_ksh), and triaging data (e.g., priority, technician_id).
        Establishes relationships with Technician (for assignment) and Prediction (for AI predictions).
        Uses Enum to constrain status and system_type to valid values.

    Key Features
        Enforces required fields (description, system_type, load_demand_kwh, position) to match the LangGraph workflow.
        Includes timestamps (date_created, date_modified) with defaults for tracking.
        Removes redundant fields (technician_name, technician_login) in favor of relationships.

## 2. Prediction Model (prediction.py)

Stores AI-generated predictions for jobs, supporting the triaging process.

    How It Achieves This
        Defines a Prediction table with fields for prediction details (e.g., priority, duration_hours, diagnosis).
        Establishes a relationship with Job via the job_id foreign key.

    Key Features
        Sets a default priority of "medium" for consistency.
        Adds constraints to ensure numeric fields (e.g., duration_hours) are non-negative.
        Includes a docstring for clarity.

## 3. Technician Model (technician.py)

Represents technicians who can be assigned to jobs.

    How It Achieves This
        Defines a Technician table with fields for technician details (e.g., name, login, skills).
        Establishes a relationship with Job for technician assignment.

    Key Features
        Uses a String for id to align with the rest of the system.
        Adds email and phone for notifications.
        Includes a docstring for clarity.

## 4. User Model (user.py)

Represents users (customers or admins) who interact with the system.

    How It Achieves This
        Defines a User table with fields for user details (e.g., email, first_name, role).
        Uses an Enum for the role field to constrain it to "customer" or "admin".

    Key Features
        Uses a String for id to align with the rest of the system.
        Includes timestamps (date_created, date_modified) for tracking.
        Matches the fields used in the users.py API endpoints.
        