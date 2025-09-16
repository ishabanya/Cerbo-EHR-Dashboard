from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from ..utils.database import get_db
from ..services.clinical_record_service import ClinicalRecordService
from ..schemas.clinical_record import (
    ClinicalRecordCreate, ClinicalRecordUpdate, ClinicalRecordResponse,
    ClinicalRecordSearch, ClinicalRecordSummary, VitalSignsCreate,
    DiagnosisCreate, PrescriptionCreate, RecordTypeEnum, StatusEnum
)
from ..schemas.common import PaginatedResponse, SuccessResponse

logger = logging.getLogger(__name__)

router = APIRouter()

def get_clinical_record_service(db: Session = Depends(get_db)) -> ClinicalRecordService:
    """Dependency to get clinical record service"""
    return ClinicalRecordService(db)

@router.get("/", response_model=PaginatedResponse[ClinicalRecordResponse])
async def get_clinical_records(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    patient_id: Optional[int] = Query(None),
    provider_id: Optional[int] = Query(None),
    record_type: Optional[RecordTypeEnum] = Query(None),
    status: Optional[StatusEnum] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    clinical_record_service: ClinicalRecordService = Depends(get_clinical_record_service)
):
    """Get clinical records with pagination and filtering"""
    try:
        skip = (page - 1) * per_page
        
        # Build filters
        filters = {}
        if patient_id:
            filters['patient_id'] = patient_id
        if provider_id:
            filters['provider_id'] = provider_id
        if record_type:
            filters['record_type'] = record_type
        if status:
            filters['status'] = status
        if start_date:
            filters['record_date'] = {'gte': start_date}
        if end_date:
            if 'record_date' in filters:
                filters['record_date']['lte'] = end_date
            else:
                filters['record_date'] = {'lte': end_date}
        
        records = clinical_record_service.search_records(
            filters=filters,
            skip=skip,
            limit=per_page
        )
        
        total = clinical_record_service.count(filters)
        pages = (total + per_page - 1) // per_page
        
        return PaginatedResponse(
            items=[ClinicalRecordResponse.from_orm(record) for record in records],
            total=total,
            page=page,
            pages=pages,
            per_page=per_page,
            has_next=page < pages,
            has_prev=page > 1
        )
    except Exception as e:
        logger.error(f"Error getting clinical records: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve clinical records")

@router.post("/", response_model=ClinicalRecordResponse, status_code=201)
async def create_clinical_record(
    record_data: ClinicalRecordCreate,
    clinical_record_service: ClinicalRecordService = Depends(get_clinical_record_service)
):
    """Create a new clinical record"""
    try:
        record = clinical_record_service.create(record_data.dict())
        return ClinicalRecordResponse.from_orm(record)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating clinical record: {e}")
        raise HTTPException(status_code=500, detail="Failed to create clinical record")

@router.get("/search", response_model=List[ClinicalRecordResponse])
async def search_clinical_records(
    search_params: ClinicalRecordSearch = Depends(),
    clinical_record_service: ClinicalRecordService = Depends(get_clinical_record_service)
):
    """Advanced clinical record search"""
    try:
        skip = (search_params.page - 1) * search_params.per_page
        
        records = clinical_record_service.advanced_search(
            search_params=search_params,
            skip=skip,
            limit=search_params.per_page
        )
        
        return [ClinicalRecordResponse.from_orm(record) for record in records]
    except Exception as e:
        logger.error(f"Error searching clinical records: {e}")
        raise HTTPException(status_code=500, detail="Failed to search clinical records")

@router.get("/{record_id}", response_model=ClinicalRecordResponse)
async def get_clinical_record(
    record_id: int,
    clinical_record_service: ClinicalRecordService = Depends(get_clinical_record_service)
):
    """Get a specific clinical record by ID"""
    try:
        record = clinical_record_service.get_by_id(record_id)
        if not record:
            raise HTTPException(status_code=404, detail="Clinical record not found")
        return ClinicalRecordResponse.from_orm(record)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting clinical record {record_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve clinical record")

@router.put("/{record_id}", response_model=ClinicalRecordResponse)
async def update_clinical_record(
    record_id: int,
    record_data: ClinicalRecordUpdate,
    clinical_record_service: ClinicalRecordService = Depends(get_clinical_record_service)
):
    """Update a clinical record"""
    try:
        update_data = {k: v for k, v in record_data.dict().items() if v is not None}
        record = clinical_record_service.update(record_id, update_data)
        
        if not record:
            raise HTTPException(status_code=404, detail="Clinical record not found")
        
        return ClinicalRecordResponse.from_orm(record)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating clinical record {record_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update clinical record")

@router.delete("/{record_id}", response_model=SuccessResponse)
async def delete_clinical_record(
    record_id: int,
    clinical_record_service: ClinicalRecordService = Depends(get_clinical_record_service)
):
    """Delete (deactivate) a clinical record"""
    try:
        success = clinical_record_service.delete(record_id)
        if not success:
            raise HTTPException(status_code=404, detail="Clinical record not found")
        
        return SuccessResponse(message="Clinical record successfully deleted")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting clinical record {record_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete clinical record")

@router.get("/patient/{patient_id}/history", response_model=List[ClinicalRecordSummary])
async def get_patient_clinical_history(
    patient_id: int,
    record_type: Optional[RecordTypeEnum] = Query(None),
    limit: int = Query(100, le=500),
    clinical_record_service: ClinicalRecordService = Depends(get_clinical_record_service)
):
    """Get clinical history for a specific patient"""
    try:
        records = clinical_record_service.get_patient_history(
            patient_id=patient_id,
            record_type=record_type,
            limit=limit
        )
        
        return [ClinicalRecordSummary.from_orm(record) for record in records]
    except Exception as e:
        logger.error(f"Error getting patient clinical history {patient_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve patient clinical history")

@router.get("/patient/{patient_id}/timeline")
async def get_patient_timeline(
    patient_id: int,
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    clinical_record_service: ClinicalRecordService = Depends(get_clinical_record_service)
):
    """Get chronological timeline of patient's clinical records"""
    try:
        timeline = clinical_record_service.get_patient_timeline(
            patient_id=patient_id,
            start_date=start_date,
            end_date=end_date
        )
        
        return {"timeline": timeline}
    except Exception as e:
        logger.error(f"Error getting patient timeline {patient_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve patient timeline")

@router.get("/type/{record_type}", response_model=List[ClinicalRecordResponse])
async def get_records_by_type(
    record_type: RecordTypeEnum,
    patient_id: Optional[int] = Query(None),
    provider_id: Optional[int] = Query(None),
    limit: int = Query(50, le=200),
    clinical_record_service: ClinicalRecordService = Depends(get_clinical_record_service)
):
    """Get records filtered by type"""
    try:
        filters = {"record_type": record_type}
        if patient_id:
            filters["patient_id"] = patient_id
        if provider_id:
            filters["provider_id"] = provider_id
        
        records = clinical_record_service.get_by_fields(filters, limit=limit)
        
        return [ClinicalRecordResponse.from_orm(record) for record in records]
    except Exception as e:
        logger.error(f"Error getting records by type {record_type}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve records by type")

@router.post("/vital-signs", response_model=ClinicalRecordResponse, status_code=201)
async def create_vital_signs(
    vital_signs_data: VitalSignsCreate,
    clinical_record_service: ClinicalRecordService = Depends(get_clinical_record_service)
):
    """Create a vital signs record"""
    try:
        record = clinical_record_service.create_vital_signs(vital_signs_data.dict())
        return ClinicalRecordResponse.from_orm(record)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating vital signs: {e}")
        raise HTTPException(status_code=500, detail="Failed to create vital signs record")

@router.post("/diagnosis", response_model=ClinicalRecordResponse, status_code=201)
async def create_diagnosis(
    diagnosis_data: DiagnosisCreate,
    clinical_record_service: ClinicalRecordService = Depends(get_clinical_record_service)
):
    """Create a diagnosis record"""
    try:
        record = clinical_record_service.create_diagnosis(diagnosis_data.dict())
        return ClinicalRecordResponse.from_orm(record)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating diagnosis: {e}")
        raise HTTPException(status_code=500, detail="Failed to create diagnosis record")

@router.post("/prescription", response_model=ClinicalRecordResponse, status_code=201)
async def create_prescription(
    prescription_data: PrescriptionCreate,
    clinical_record_service: ClinicalRecordService = Depends(get_clinical_record_service)
):
    """Create a prescription record"""
    try:
        record = clinical_record_service.create_prescription(prescription_data.dict())
        return ClinicalRecordResponse.from_orm(record)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating prescription: {e}")
        raise HTTPException(status_code=500, detail="Failed to create prescription record")

@router.get("/patient/{patient_id}/allergies", response_model=List[ClinicalRecordResponse])
async def get_patient_allergies(
    patient_id: int,
    active_only: bool = Query(True),
    clinical_record_service: ClinicalRecordService = Depends(get_clinical_record_service)
):
    """Get all allergies for a patient"""
    try:
        allergies = clinical_record_service.get_patient_allergies(
            patient_id=patient_id,
            active_only=active_only
        )
        
        return [ClinicalRecordResponse.from_orm(allergy) for allergy in allergies]
    except Exception as e:
        logger.error(f"Error getting patient allergies {patient_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve patient allergies")

@router.get("/patient/{patient_id}/medications", response_model=List[ClinicalRecordResponse])
async def get_patient_medications(
    patient_id: int,
    active_only: bool = Query(True),
    clinical_record_service: ClinicalRecordService = Depends(get_clinical_record_service)
):
    """Get all medications/prescriptions for a patient"""
    try:
        medications = clinical_record_service.get_patient_medications(
            patient_id=patient_id,
            active_only=active_only
        )
        
        return [ClinicalRecordResponse.from_orm(med) for med in medications]
    except Exception as e:
        logger.error(f"Error getting patient medications {patient_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve patient medications")

@router.get("/patient/{patient_id}/diagnoses", response_model=List[ClinicalRecordResponse])
async def get_patient_diagnoses(
    patient_id: int,
    active_only: bool = Query(True),
    clinical_record_service: ClinicalRecordService = Depends(get_clinical_record_service)
):
    """Get all diagnoses for a patient"""
    try:
        diagnoses = clinical_record_service.get_patient_diagnoses(
            patient_id=patient_id,
            active_only=active_only
        )
        
        return [ClinicalRecordResponse.from_orm(diagnosis) for diagnosis in diagnoses]
    except Exception as e:
        logger.error(f"Error getting patient diagnoses {patient_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve patient diagnoses")

@router.get("/patient/{patient_id}/vital-signs/latest")
async def get_latest_vital_signs(
    patient_id: int,
    clinical_record_service: ClinicalRecordService = Depends(get_clinical_record_service)
):
    """Get the most recent vital signs for a patient"""
    try:
        vital_signs = clinical_record_service.get_latest_vital_signs(patient_id)
        
        if not vital_signs:
            return {"message": "No vital signs found for this patient"}
        
        return ClinicalRecordResponse.from_orm(vital_signs)
    except Exception as e:
        logger.error(f"Error getting latest vital signs {patient_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve latest vital signs")

@router.post("/{record_id}/review", response_model=ClinicalRecordResponse)
async def review_clinical_record(
    record_id: int,
    reviewed_by: str = Query(...),
    notes: Optional[str] = Query(None),
    clinical_record_service: ClinicalRecordService = Depends(get_clinical_record_service)
):
    """Mark a clinical record as reviewed"""
    try:
        record = clinical_record_service.mark_as_reviewed(
            record_id=record_id,
            reviewed_by=reviewed_by,
            notes=notes
        )
        
        if not record:
            raise HTTPException(status_code=404, detail="Clinical record not found")
        
        return ClinicalRecordResponse.from_orm(record)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reviewing clinical record {record_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to review clinical record")

@router.get("/stats/summary")
async def get_clinical_records_summary(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    clinical_record_service: ClinicalRecordService = Depends(get_clinical_record_service)
):
    """Get summary statistics for clinical records"""
    try:
        summary = clinical_record_service.get_records_summary(
            start_date=start_date,
            end_date=end_date
        )
        
        return summary
    except Exception as e:
        logger.error(f"Error getting clinical records summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve clinical records summary")