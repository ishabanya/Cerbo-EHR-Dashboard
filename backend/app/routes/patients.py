from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from ..utils.database import get_db
from ..services.patient_service import PatientService
from ..schemas.patient import (
    PatientCreate, PatientUpdate, PatientResponse, 
    PatientSearch, PatientSummary
)
from ..schemas.common import PaginatedResponse, SuccessResponse

logger = logging.getLogger(__name__)

router = APIRouter()

def get_patient_service(db: Session = Depends(get_db)) -> PatientService:
    """Dependency to get patient service"""
    return PatientService(db)

@router.get("/", response_model=PaginatedResponse[PatientResponse])
async def get_patients(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    search: Optional[str] = Query(None),
    search_type: str = Query("all"),
    is_active: Optional[bool] = Query(True),
    patient_service: PatientService = Depends(get_patient_service)
):
    """Get all patients with pagination and search"""
    try:
        skip = (page - 1) * per_page
        
        if search:
            patients = patient_service.search_patients(
                search_term=search,
                search_type=search_type,
                skip=skip,
                limit=per_page
            )
        else:
            filters = {"is_active": is_active} if is_active is not None else {}
            patients = patient_service.get_by_fields(filters) if filters else patient_service.get_all(skip=skip, limit=per_page)
        
        # Get total count
        total = patient_service.count({"is_active": is_active} if is_active is not None else {})
        
        # Calculate pagination info
        pages = (total + per_page - 1) // per_page
        has_next = page < pages
        has_prev = page > 1
        
        return PaginatedResponse(
            items=[PatientResponse.from_orm(patient) for patient in patients],
            total=total,
            page=page,
            pages=pages,
            per_page=per_page,
            has_next=has_next,
            has_prev=has_prev
        )
    except Exception as e:
        logger.error(f"Error getting patients: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve patients")

@router.post("/", response_model=PatientResponse, status_code=201)
async def create_patient(
    patient_data: PatientCreate,
    patient_service: PatientService = Depends(get_patient_service)
):
    """Create a new patient"""
    try:
        patient = patient_service.create(patient_data.dict())
        return PatientResponse.from_orm(patient)
    except Exception as e:
        logger.error(f"Error creating patient: {e}")
        raise HTTPException(status_code=500, detail="Failed to create patient")

@router.get("/search", response_model=List[PatientResponse])
async def search_patients(
    search_params: PatientSearch = Depends(),
    patient_service: PatientService = Depends(get_patient_service)
):
    """Advanced patient search"""
    try:
        skip = (search_params.page - 1) * search_params.per_page
        
        patients = patient_service.search_patients(
            search_term=search_params.search_term,
            search_type=search_params.search_type,
            skip=skip,
            limit=search_params.per_page
        )
        
        return [PatientResponse.from_orm(patient) for patient in patients]
    except Exception as e:
        logger.error(f"Error searching patients: {e}")
        raise HTTPException(status_code=500, detail="Failed to search patients")

@router.get("/{patient_id}", response_model=PatientResponse)
async def get_patient(
    patient_id: int,
    patient_service: PatientService = Depends(get_patient_service)
):
    """Get a specific patient by ID"""
    try:
        patient = patient_service.get_by_id(patient_id)
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        return PatientResponse.from_orm(patient)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting patient {patient_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve patient")

@router.put("/{patient_id}", response_model=PatientResponse)
async def update_patient(
    patient_id: int,
    patient_data: PatientUpdate,
    patient_service: PatientService = Depends(get_patient_service)
):
    """Update a patient"""
    try:
        # Only include non-None values
        update_data = {k: v for k, v in patient_data.dict().items() if v is not None}
        
        patient = patient_service.update(patient_id, update_data)
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        return PatientResponse.from_orm(patient)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating patient {patient_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update patient")

@router.delete("/{patient_id}", response_model=SuccessResponse)
async def delete_patient(
    patient_id: int,
    patient_service: PatientService = Depends(get_patient_service)
):
    """Delete (deactivate) a patient"""
    try:
        success = patient_service.deactivate_patient(patient_id, "Deleted via API")
        if not success:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        return SuccessResponse(message="Patient successfully deactivated")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting patient {patient_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete patient")

@router.post("/{patient_id}/reactivate", response_model=PatientResponse)
async def reactivate_patient(
    patient_id: int,
    patient_service: PatientService = Depends(get_patient_service)
):
    """Reactivate a deactivated patient"""
    try:
        patient = patient_service.reactivate_patient(patient_id)
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        return PatientResponse.from_orm(patient)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reactivating patient {patient_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to reactivate patient")

@router.get("/{patient_id}/summary")
async def get_patient_summary(
    patient_id: int,
    patient_service: PatientService = Depends(get_patient_service)
):
    """Get comprehensive patient summary"""
    try:
        summary = patient_service.get_patient_summary(patient_id)
        if not summary:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        return summary
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting patient summary {patient_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve patient summary")

@router.get("/mrn/{mrn}", response_model=PatientResponse)
async def get_patient_by_mrn(
    mrn: str,
    patient_service: PatientService = Depends(get_patient_service)
):
    """Get patient by medical record number"""
    try:
        patient = patient_service.get_by_medical_record_number(mrn)
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        return PatientResponse.from_orm(patient)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting patient by MRN {mrn}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve patient")