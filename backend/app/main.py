from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import logging
import uvicorn
from contextlib import asynccontextmanager

from .utils.config import settings
from .utils.database import init_database, check_database_connection
from .routes import patients, appointments, providers, clinical_records, insurance, billing, health

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting EHR Dashboard application...")
    
    try:
        init_database()
        if check_database_connection():
            logger.info("Database connection verified")
        else:
            logger.error("Database connection failed")
            raise Exception("Database initialization failed")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise
    
    logger.info("Application startup complete")
    yield
    
    logger.info("Shutting down EHR Dashboard application...")

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Comprehensive EHR CRUD Dashboard with CERBO SANDBOX API integration",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if not settings.debug:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["localhost", "127.0.0.1", "*.example.com"]
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    logger.error(f"HTTP {exc.status_code}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "path": str(request.url.path)
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "status_code": 500,
            "path": str(request.url.path)
        }
    )

app.include_router(health.router, prefix="/api/v1", tags=["Health"])
app.include_router(patients.router, prefix="/api/v1/patients", tags=["Patients"])
app.include_router(appointments.router, prefix="/api/v1/appointments", tags=["Appointments"])
app.include_router(providers.router, prefix="/api/v1/providers", tags=["Providers"])
app.include_router(clinical_records.router, prefix="/api/v1/clinical-records", tags=["Clinical Records"])
app.include_router(insurance.router, prefix="/api/v1/insurance", tags=["Insurance"])
app.include_router(billing.router, prefix="/api/v1/billing", tags=["Billing"])

@app.get("/")
async def root():
    return {
        "message": "EHR CRUD Dashboard API",
        "version": settings.app_version,
        "docs": "/docs" if settings.debug else "Documentation disabled in production"
    }

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )