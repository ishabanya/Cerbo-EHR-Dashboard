from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import logging

from ..utils.database import get_db, check_database_connection
from ..utils.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint"""
    try:
        # Check database connection
        db_healthy = check_database_connection()
        
        # Check CERBO API (basic connectivity)
        cerbo_healthy = True  # We'll implement this when we test the API
        
        status = "healthy" if db_healthy and cerbo_healthy else "unhealthy"
        
        return {
            "status": status,
            "version": settings.app_version,
            "database": "connected" if db_healthy else "disconnected",
            "cerbo_api": "available" if cerbo_healthy else "unavailable",
            "environment": "development" if settings.debug else "production"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }

@router.get("/info")
async def app_info():
    """Application information endpoint"""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "description": "EHR CRUD Dashboard with CERBO SANDBOX API integration",
        "endpoints": {
            "patients": "/api/v1/patients",
            "appointments": "/api/v1/appointments", 
            "providers": "/api/v1/providers",
            "clinical_records": "/api/v1/clinical-records",
            "insurance": "/api/v1/insurance",
            "billing": "/api/v1/billing"
        }
    }