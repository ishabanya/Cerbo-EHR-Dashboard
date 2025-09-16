from sqlalchemy import create_engine, MetaData, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
import logging
from typing import Generator

from .config import settings

logger = logging.getLogger(__name__)

# Create SQLAlchemy engine
engine = create_engine(
    settings.database_url,
    echo=settings.database_echo,
    # SQLite specific configuration
    poolclass=StaticPool if settings.database_url.startswith("sqlite") else None,
    connect_args={"check_same_thread": False} if settings.database_url.startswith("sqlite") else {},
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create metadata instance
metadata = MetaData()

def get_db() -> Generator[Session, None, None]:
    """
    Dependency function to get database session.
    This will be used with FastAPI's dependency injection.
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def create_all_tables():
    """Create all database tables"""
    from ..models import Base
    Base.metadata.create_all(bind=engine)
    logger.info("All database tables created successfully")

def drop_all_tables():
    """Drop all database tables (use with caution!)"""
    from ..models import Base
    Base.metadata.drop_all(bind=engine)
    logger.warning("All database tables dropped")

def init_database():
    """Initialize the database with tables and initial data"""
    logger.info("Initializing database...")
    create_all_tables()
    
    # Create initial data if needed
    db = SessionLocal()
    try:
        # Check if we need to create initial data
        from ..models import Provider, Patient
        
        # Create a default provider if none exists
        provider_count = db.query(Provider).count()
        if provider_count == 0:
            logger.info("Creating default provider...")
            default_provider = Provider(
                first_name="John",
                last_name="Doe",
                title="Dr.",
                provider_type="physician",
                email="dr.doe@example.com",
                phone_primary="555-0123",
                specialties=["Family Medicine"],
                npi_number="1234567890"
            )
            db.add(default_provider)
        
        db.commit()
        logger.info("Database initialization completed")
        
    except Exception as e:
        logger.error(f"Error during database initialization: {e}")
        db.rollback()
        raise
    finally:
        db.close()

# Database health check
def check_database_connection() -> bool:
    """Check if database connection is working"""
    try:
        db = SessionLocal()
        # Simple query to test connection
        db.execute(text("SELECT 1"))
        db.close()
        return True
    except Exception as e:
        logger.error(f"Database connection check failed: {e}")
        return False