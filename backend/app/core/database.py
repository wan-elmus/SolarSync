from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.core.config import config
import logging
from typing import Generator

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure the engine with connection pooling
try:
    engine = create_engine(
        config.DATABASE_URL,
        pool_size=5,           # Maximum number of connections to keep in the pool
        max_overflow=10,       # Maximum number of connections to create beyond pool_size
        pool_timeout=30,       # Timeout for getting a connection from the pool
        pool_recycle=1800      # Recycle connections after 30 minutes
    )
    logger.info("Database engine created successfully")
except Exception as e:
    logger.critical(f"Failed to create database engine: {str(e)}")
    raise

# Create a session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
class Base(DeclarativeBase):
    pass

def get_db() -> Generator:
    """
    Provide a database session for dependency injection.

    Yields:
        Session: A SQLAlchemy database session.

    Ensures:
        The session is closed after the request is completed.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        logger.debug("Database session closed")