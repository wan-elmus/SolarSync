from dotenv import load_dotenv
import os
from typing import Optional
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class Config:
    """
    Configuration class for SolarSync, loading settings from environment variables.

    Attributes:
        ENVIRONMENT (str): The environment the app is running in ('development', 'testing', 'production').
        DATABASE_URL (str): The URL for the database connection.
        OPENWEATHERMAP_API_KEY (str): API key for OpenWeatherMap.
        GOOGLE_MAPS_API_KEY (str): API key for Google Maps.
        TWILIO_ACCOUNT_SID (str): Twilio account SID for SMS.
        TWILIO_AUTH_TOKEN (str): Twilio auth token for SMS.
        TWILIO_PHONE_NUMBER (str): Twilio phone number for sending SMS.
        REDIS_URL (str): The URL for the Redis connection.
        SECRET_KEY (str): Secret key for JWT and other security features.
    """
    def __init__(self) -> None:
        self.ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
        self.DATABASE_URL: str = os.getenv("DATABASE_URL")
        self.OPENWEATHERMAP_API_KEY: Optional[str] = os.getenv("OPENWEATHERMAP_API_KEY")
        self.GOOGLE_MAPS_API_KEY: Optional[str] = os.getenv("GOOGLE_MAPS_API_KEY")
        self.TWILIO_ACCOUNT_SID: Optional[str] = os.getenv("TWILIO_ACCOUNT_SID")
        self.TWILIO_AUTH_TOKEN: Optional[str] = os.getenv("TWILIO_AUTH_TOKEN")
        self.TWILIO_PHONE_NUMBER: Optional[str] = os.getenv("TWILIO_PHONE_NUMBER")
        self.REDIS_URL: str = os.getenv("REDIS_URL")
        self.SECRET_KEY: str = os.getenv("SECRET_KEY")

        # Validate required environment variables
        self._validate()

    def _validate(self) -> None:
        """
        Validate that required environment variables are set and meet minimum requirements.
        
        Raises:
            ValueError: If a required environment variable is missing or invalid.
        """
        required_vars = {
            "DATABASE_URL": self.DATABASE_URL,
            "REDIS_URL": self.REDIS_URL,
            "SECRET_KEY": self.SECRET_KEY,
        }
        for var_name, var_value in required_vars.items():
            if not var_value:
                logger.error(f"Missing required environment variable: {var_name}")
                raise ValueError(f"Missing required environment variable: {var_name}")

        # Validate SECRET_KEY length
        if len(self.SECRET_KEY) < 32:
            logger.error("SECRET_KEY must be at least 32 characters long")
            raise ValueError("SECRET_KEY must be at least 32 characters long")

        # Validate ENVIRONMENT
        valid_environments = ["development", "testing", "production"]
        if self.ENVIRONMENT not in valid_environments:
            logger.error(f"Invalid ENVIRONMENT: {self.ENVIRONMENT}. Must be one of {valid_environments}")
            raise ValueError(f"Invalid ENVIRONMENT: {self.ENVIRONMENT}. Must be one of {valid_environments}")

        # Warn if optional variables are missing
        optional_vars = {
            "OPENWEATHERMAP_API_KEY": self.OPENWEATHERMAP_API_KEY,
            "GOOGLE_MAPS_API_KEY": self.GOOGLE_MAPS_API_KEY,
            "TWILIO_ACCOUNT_SID": self.TWILIO_ACCOUNT_SID,
            "TWILIO_AUTH_TOKEN": self.TWILIO_AUTH_TOKEN,
            "TWILIO_PHONE_NUMBER": self.TWILIO_PHONE_NUMBER,
        }
        for var_name, var_value in optional_vars.items():
            if not var_value:
                logger.warning(f"Optional environment variable {var_name} is not set. Some features may not work.")

# Instantiate the config
try:
    config = Config()
except Exception as e:
    logger.critical(f"Failed to initialize configuration: {str(e)}")
    raise