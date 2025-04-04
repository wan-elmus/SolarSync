from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.core.config import config
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password.

    Args:
        plain_password (str): The plain password to verify.
        hashed_password (str): The hashed password to verify against.

    Returns:
        bool: True if the password matches, False otherwise.
    """
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logger.error(f"Error verifying password: {str(e)}")
        return False

def get_password_hash(password: str) -> str:
    """
    Hash a password for storage.

    Args:
        password (str): The plain password to hash.

    Returns:
        str: The hashed password.
    """
    try:
        hashed_password = pwd_context.hash(password)
        logger.debug("Password hashed successfully")
        return hashed_password
    except Exception as e:
        logger.error(f"Error hashing password: {str(e)}")
        raise

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.

    Args:
        data (Dict[str, Any]): The data to encode in the token (e.g., user ID).
        expires_delta (Optional[timedelta]): The expiration time delta. Defaults to 15 minutes.

    Returns:
        str: The encoded JWT token.

    Raises:
        ValueError: If the token creation fails.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    
    try:
        encoded_jwt = jwt.encode(to_encode, config.SECRET_KEY, algorithm="HS256")
        logger.info(f"Created access token for data: {data}")
        return encoded_jwt
    except Exception as e:
        logger.error(f"Error creating access token: {str(e)}")
        raise ValueError(f"Failed to create access token: {str(e)}")

def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode and verify a JWT access token.

    Args:
        token (str): The JWT token to decode.

    Returns:
        Optional[Dict[str, Any]]: The decoded token data if valid, None otherwise.
    """
    try:
        payload = jwt.decode(token, config.SECRET_KEY, algorithms=["HS256"])
        logger.debug(f"Decoded access token: {payload}")
        return payload
    except JWTError as e:
        logger.error(f"Error decoding access token: {str(e)}")
        return None