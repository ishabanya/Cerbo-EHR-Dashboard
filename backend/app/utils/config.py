import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings and configuration"""
    
    # API Configuration
    cerbo_base_url: str = Field(
        default="https://sandbox.md-hq.com/api/v1",
        env="CERBO_BASE_URL",
        description="CERBO SANDBOX API base URL"
    )
    cerbo_username: str = Field(
        default="pk_scribe_health_ai",
        env="CERBO_USERNAME",
        description="CERBO API username"
    )
    cerbo_secret_key: str = Field(
        default="sk_FghBAQHKXZzO4Mt4oWAC5s8sGEbVH",
        env="CERBO_SECRET_KEY",
        description="CERBO API secret key"
    )
    
    # Database Configuration
    database_url: str = Field(
        default="sqlite:///./ehr_dashboard.db",
        env="DATABASE_URL",
        description="Database connection URL"
    )
    database_echo: bool = Field(
        default=False,
        env="DATABASE_ECHO",
        description="Enable SQLAlchemy query logging"
    )
    
    # Application Configuration
    app_name: str = Field(
        default="EHR CRUD Dashboard",
        env="APP_NAME",
        description="Application name"
    )
    app_version: str = Field(
        default="1.0.0",
        env="APP_VERSION",
        description="Application version"
    )
    debug: bool = Field(
        default=False,
        env="DEBUG",
        description="Enable debug mode"
    )
    environment: str = Field(
        default="development",
        env="ENVIRONMENT",
        description="Application environment (development/production/testing)"
    )
    
    # Security Configuration
    secret_key: str = Field(
        default="your-secret-key-change-in-production",
        env="SECRET_KEY",
        description="Application secret key for security"
    )
    access_token_expire_minutes: int = Field(
        default=30,
        env="ACCESS_TOKEN_EXPIRE_MINUTES",
        description="JWT token expiration time in minutes"
    )
    
    # CORS Configuration
    allowed_origins: list = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        env="ALLOWED_ORIGINS",
        description="Allowed CORS origins"
    )
    
    # Logging Configuration
    log_level: str = Field(
        default="INFO",
        env="LOG_LEVEL",
        description="Logging level"
    )
    
    # Rate Limiting
    rate_limit_requests: int = Field(
        default=60,
        env="RATE_LIMIT_REQUESTS",
        description="Max requests per rate limit window"
    )
    rate_limit_window: int = Field(
        default=60,
        env="RATE_LIMIT_WINDOW",
        description="Rate limit window in seconds"
    )
    
    # File Upload Configuration
    max_upload_size: int = Field(
        default=10 * 1024 * 1024,  # 10MB
        env="MAX_UPLOAD_SIZE",
        description="Maximum file upload size in bytes"
    )
    upload_directory: str = Field(
        default="./uploads",
        env="UPLOAD_DIRECTORY",
        description="Directory for file uploads"
    )
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
        "extra": "ignore"
    }

# Create global settings instance
settings = Settings()

# Environment detection
def is_development() -> bool:
    """Check if running in development environment"""
    return settings.debug or os.getenv("ENVIRONMENT", "development") == "development"

def is_production() -> bool:
    """Check if running in production environment"""
    return os.getenv("ENVIRONMENT") == "production"

def is_testing() -> bool:
    """Check if running in testing environment"""
    return os.getenv("ENVIRONMENT") == "testing"