from twilio.rest import Client
from app.core.config import config
import logging
from typing import Optional
import re

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def send_sms(to_phone: str, message: str) -> Optional[str]:
    """
    Send an SMS using the Twilio API.

    Args:
        to_phone (str): The recipient's phone number (e.g., "+254726598127").
        message (str): The message to send.

    Returns:
        Optional[str]: The message SID if successful, None otherwise.

    Raises:
        ValueError: If the phone number format is invalid.
    """
    try:
        # Validate phone number format (e.g., "+254726598127")
        if not re.match(r"^\+\d{10,15}$", to_phone):
            raise ValueError(f"Invalid phone number format: {to_phone}. Must start with '+' followed by 10-15 digits.")

        # Initialize Twilio client
        client = Client(config.TWILIO_ACCOUNT_SID, config.TWILIO_AUTH_TOKEN)

        # Send the SMS
        message_obj = client.messages.create(
            body=message,
            from_=config.TWILIO_PHONE_NUMBER,
            to=to_phone
        )
        logger.info(f"SMS sent to {to_phone}: {message_obj.sid}")
        return message_obj.sid

    except Exception as e:
        logger.error(f"Error sending SMS to {to_phone}: {str(e)}")
        return None