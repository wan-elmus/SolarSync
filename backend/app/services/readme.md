# SUMMARY

This folder contains service modules that encapsulate business logic for the SolarSync backend. These services handle tasks such as AI predictions, solar system sizing, weather data fetching, mapping, and SMS notifications. They are designed to support independent sizing and triaging functionalities while ensuring the system is modular, scalable, and maintainable.

## 1. AI Service (ai_service.py)

Provides AI predictions for job details to support the triaging process.

    How It Achieves This
        Implements a predict_job_details function that predicts job priority, duration, costs, technician assignment, and diagnosis based on job description and system type.
        Queries the database to find a suitable technician based on skills.

    Key Features
        Uses a mock AI model (to be replaced with a TensorFlow model) with realistic logic based on job description and system type.
        Includes error handling and logging for robustness.
        Dynamically assigns technicians based on skills, aligning with the database schema.

## 2. Map Service (map_service.py)

Provides mapping functionalities using the Google Maps API.

    How It Achieves This
        Implements geocode_address to convert addresses to coordinates.
        Implements calculate_distance to compute the distance between two coordinates.

    Key Features
        Supports geocoding for jobs where only an address is provided.
        Enables distance-based technician assignment by calculating distances.
        Includes error handling and logging for API interactions.

## 3. Sizing Service (sizing_service.py)

Calculates solar system sizing requirements based on load demand, system type, and location.

    How It Achieves This
        Implements calculate_sizing to compute panel capacity, battery capacity, inverter capacity, costs, and ROI.
        Uses weather_service.py to fetch peak sun hours for accurate sizing.

    Key Features
        Validates inputs (e.g., system_type, position) to ensure data integrity.
        Includes error handling and logging for robustness.
        Provides detailed sizing results for use in job creation and reporting.

## 4. SMS Service (sms_service.py)

Sends SMS notifications using the Twilio API.

    How It Achieves This
        Implements send_sms to send messages to specified phone numbers.

    Key Features
        Enables notifications for technicians (e.g., job assignments) and customers (e.g., job status updates).
        Includes error handling and logging for API interactions.
        Returns the message SID for tracking.

## 5. Weather Service (weather_service.py)

 Fetches weather data from OpenWeatherMap to estimate peak sun hours.

    How It Achieves This
        Implements get_peak_sun_hours to fetch current weather data and estimate peak sun hours based on cloud cover and latitude.

    Key Features
        Dynamically adjusts peak sun hours range based on latitude for more accurate estimates.
        Validates latitude and longitude inputs to prevent invalid requests.
        Includes error handling with a latitude-based fallback value.

        