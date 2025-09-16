from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from ..utils.database import get_db
from ..services.insurance_service import InsuranceService
from ..schemas.insurance import (
    InsuranceCreate, InsuranceUpdate, InsuranceResponse,
    InsuranceSearch, InsuranceSummary, EligibilityVerificationRequest,
    EligibilityVerificationResponse, CoverageCalculationRequest,
    CoverageCalculationResponse, PriorAuthorizationRequest,
    PriorAuthorizationResponse, InsuranceTypeEnum, CoverageStatusEnum,
    EligibilityStatusEnum
)
from ..schemas.common import PaginatedResponse, SuccessResponse

logger = logging.getLogger(__name__)

router = APIRouter()

def get_insurance_service(db: Session = Depends(get_db)) -> InsuranceService:
    """Dependency to get insurance service"""
    return InsuranceService(db)

@router.get("/", response_model=PaginatedResponse[InsuranceResponse])
async def get_insurance_records(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    patient_id: Optional[int] = Query(None),
    insurance_type: Optional[InsuranceTypeEnum] = Query(None),
    coverage_status: Optional[CoverageStatusEnum] = Query(None),
    eligibility_status: Optional[EligibilityStatusEnum] = Query(None),
    needs_verification: Optional[bool] = Query(None),
    insurance_service: InsuranceService = Depends(get_insurance_service)
):
    """Get insurance records with pagination and filtering"""
    try:
        skip = (page - 1) * per_page
        
        # Build filters
        filters = {}
        if patient_id:
            filters['patient_id'] = patient_id
        if insurance_type:
            filters['insurance_type'] = insurance_type
        if coverage_status:
            filters['coverage_status'] = coverage_status
        if eligibility_status:
            filters['eligibility_status'] = eligibility_status
        if needs_verification is not None:
            filters['needs_verification'] = needs_verification
        
        records = insurance_service.search_insurance(
            filters=filters,
            skip=skip,
            limit=per_page
        )
        
        total = insurance_service.count(filters)
        pages = (total + per_page - 1) // per_page
        
        return PaginatedResponse(
            items=[InsuranceResponse.from_orm(record) for record in records],
            total=total,
            page=page,
            pages=pages,
            per_page=per_page,
            has_next=page < pages,
            has_prev=page > 1
        )
    except Exception as e:
        logger.error(f"Error getting insurance records: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve insurance records")

@router.post("/", response_model=InsuranceResponse, status_code=201)
async def create_insurance_record(
    insurance_data: InsuranceCreate,
    insurance_service: InsuranceService = Depends(get_insurance_service)
):
    """Create a new insurance record"""
    try:
        record = insurance_service.create(insurance_data.dict())
        return InsuranceResponse.from_orm(record)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating insurance record: {e}")
        raise HTTPException(status_code=500, detail="Failed to create insurance record")

@router.get("/search", response_model=List[InsuranceResponse])
async def search_insurance_records(
    search_params: InsuranceSearch = Depends(),
    insurance_service: InsuranceService = Depends(get_insurance_service)
):
    """Advanced insurance record search"""
    try:
        skip = (search_params.page - 1) * search_params.per_page
        
        records = insurance_service.advanced_search(
            search_params=search_params,
            skip=skip,
            limit=search_params.per_page
        )
        
        return [InsuranceResponse.from_orm(record) for record in records]
    except Exception as e:
        logger.error(f"Error searching insurance records: {e}")
        raise HTTPException(status_code=500, detail="Failed to search insurance records")

@router.get("/{insurance_id}", response_model=InsuranceResponse)
async def get_insurance_record(
    insurance_id: int,
    insurance_service: InsuranceService = Depends(get_insurance_service)
):
    """Get a specific insurance record by ID"""
    try:
        record = insurance_service.get_by_id(insurance_id)
        if not record:
            raise HTTPException(status_code=404, detail="Insurance record not found")
        return InsuranceResponse.from_orm(record)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting insurance record {insurance_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve insurance record")

@router.put("/{insurance_id}", response_model=InsuranceResponse)
async def update_insurance_record(
    insurance_id: int,
    insurance_data: InsuranceUpdate,
    insurance_service: InsuranceService = Depends(get_insurance_service)
):
    """Update an insurance record"""
    try:
        update_data = {k: v for k, v in insurance_data.dict().items() if v is not None}
        record = insurance_service.update(insurance_id, update_data)
        
        if not record:
            raise HTTPException(status_code=404, detail="Insurance record not found")
        
        return InsuranceResponse.from_orm(record)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating insurance record {insurance_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update insurance record")

@router.delete("/{insurance_id}", response_model=SuccessResponse)
async def delete_insurance_record(
    insurance_id: int,
    insurance_service: InsuranceService = Depends(get_insurance_service)
):
    """Delete (deactivate) an insurance record"""
    try:
        success = insurance_service.delete(insurance_id)
        if not success:
            raise HTTPException(status_code=404, detail="Insurance record not found")
        
        return SuccessResponse(message="Insurance record successfully deleted")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting insurance record {insurance_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete insurance record")

@router.get("/patient/{patient_id}", response_model=List[InsuranceSummary])
async def get_patient_insurance(
    patient_id: int,
    active_only: bool = Query(True),
    insurance_service: InsuranceService = Depends(get_insurance_service)
):
    """Get all insurance records for a specific patient"""
    try:
        records = insurance_service.get_patient_insurance(
            patient_id=patient_id,
            active_only=active_only
        )
        
        return [InsuranceSummary.from_orm(record) for record in records]
    except Exception as e:
        logger.error(f"Error getting patient insurance {patient_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve patient insurance")

@router.get("/patient/{patient_id}/primary", response_model=InsuranceResponse)
async def get_patient_primary_insurance(
    patient_id: int,
    insurance_service: InsuranceService = Depends(get_insurance_service)
):
    """Get the primary insurance for a patient"""
    try:
        record = insurance_service.get_primary_insurance(patient_id)
        if not record:
            raise HTTPException(status_code=404, detail="No primary insurance found for patient")
        
        return InsuranceResponse.from_orm(record)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting primary insurance {patient_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve primary insurance")

@router.post("/verify-eligibility", response_model=EligibilityVerificationResponse)
async def verify_eligibility(
    verification_request: EligibilityVerificationRequest,
    insurance_service: InsuranceService = Depends(get_insurance_service)
):
    """Verify insurance eligibility"""
    try:
        result = insurance_service.verify_eligibility(
            insurance_id=verification_request.insurance_id,
            service_type=verification_request.service_type,
            provider_npi=verification_request.provider_npi,
            force_refresh=verification_request.force_refresh
        )
        
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error verifying eligibility: {e}")
        raise HTTPException(status_code=500, detail="Failed to verify eligibility")

@router.post("/calculate-coverage", response_model=CoverageCalculationResponse)
async def calculate_coverage(
    calculation_request: CoverageCalculationRequest,
    insurance_service: InsuranceService = Depends(get_insurance_service)
):
    """Calculate patient cost and insurance coverage for a service"""
    try:
        result = insurance_service.calculate_coverage(
            insurance_id=calculation_request.insurance_id,
            service_cost=calculation_request.service_cost,
            service_type=calculation_request.service_type,
            cpt_code=calculation_request.cpt_code,
            diagnosis_code=calculation_request.diagnosis_code
        )
        
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error calculating coverage: {e}")
        raise HTTPException(status_code=500, detail="Failed to calculate coverage")

@router.post("/prior-authorization", response_model=PriorAuthorizationResponse)
async def request_prior_authorization(
    auth_request: PriorAuthorizationRequest,
    insurance_service: InsuranceService = Depends(get_insurance_service)
):
    """Request prior authorization for services"""
    try:
        result = insurance_service.request_prior_authorization(
            insurance_id=auth_request.insurance_id,
            service_description=auth_request.service_description,
            cpt_codes=auth_request.cpt_codes,
            diagnosis_codes=auth_request.diagnosis_codes,
            requested_date=auth_request.requested_date,
            provider_info=auth_request.provider_info,
            patient_notes=auth_request.patient_notes
        )
        
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error requesting prior authorization: {e}")
        raise HTTPException(status_code=500, detail="Failed to request prior authorization")

@router.get("/verification/pending", response_model=List[InsuranceResponse])
async def get_pending_verifications(
    limit: int = Query(50, le=200),
    insurance_service: InsuranceService = Depends(get_insurance_service)
):
    """Get insurance records that need eligibility verification"""
    try:
        records = insurance_service.get_pending_verifications(limit=limit)
        
        return [InsuranceResponse.from_orm(record) for record in records]
    except Exception as e:
        logger.error(f"Error getting pending verifications: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve pending verifications")

@router.get("/expiring", response_model=List[InsuranceResponse])
async def get_expiring_insurance(
    days_ahead: int = Query(30, ge=1, le=365),
    insurance_service: InsuranceService = Depends(get_insurance_service)
):
    """Get insurance records expiring within specified days"""
    try:
        records = insurance_service.get_expiring_insurance(days_ahead=days_ahead)
        
        return [InsuranceResponse.from_orm(record) for record in records]
    except Exception as e:
        logger.error(f"Error getting expiring insurance: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve expiring insurance")

@router.post("/{insurance_id}/update-deductibles", response_model=InsuranceResponse)
async def update_deductibles(
    insurance_id: int,
    individual_met: Optional[float] = Query(None),
    family_met: Optional[float] = Query(None),
    oop_individual_met: Optional[float] = Query(None),
    oop_family_met: Optional[float] = Query(None),
    insurance_service: InsuranceService = Depends(get_insurance_service)
):
    """Update deductible and out-of-pocket amounts met"""
    try:
        record = insurance_service.update_deductibles(
            insurance_id=insurance_id,
            individual_met=individual_met,
            family_met=family_met,
            oop_individual_met=oop_individual_met,
            oop_family_met=oop_family_met
        )
        
        if not record:
            raise HTTPException(status_code=404, detail="Insurance record not found")
        
        return InsuranceResponse.from_orm(record)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating deductibles {insurance_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update deductibles")

@router.get("/company/{company_name}/policies", response_model=List[InsuranceResponse])
async def get_policies_by_company(
    company_name: str,
    active_only: bool = Query(True),
    limit: int = Query(100, le=500),
    insurance_service: InsuranceService = Depends(get_insurance_service)
):
    """Get all policies for a specific insurance company"""
    try:
        records = insurance_service.get_by_company(
            company_name=company_name,
            active_only=active_only,
            limit=limit
        )
        
        return [InsuranceResponse.from_orm(record) for record in records]
    except Exception as e:
        logger.error(f"Error getting policies by company {company_name}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve policies by company")

@router.get("/stats/summary")
async def get_insurance_summary(
    insurance_service: InsuranceService = Depends(get_insurance_service)
):
    """Get summary statistics for insurance records"""
    try:
        summary = insurance_service.get_insurance_summary()
        
        return summary
    except Exception as e:
        logger.error(f"Error getting insurance summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve insurance summary")

@router.post("/batch-verify", response_model=dict)
async def batch_verify_eligibility(
    insurance_ids: List[int],
    force_refresh: bool = Query(False),
    insurance_service: InsuranceService = Depends(get_insurance_service)
):
    """Batch verify eligibility for multiple insurance records"""
    try:
        results = insurance_service.batch_verify_eligibility(
            insurance_ids=insurance_ids,
            force_refresh=force_refresh
        )
        
        return {
            "total_processed": len(insurance_ids),
            "successful": len([r for r in results if r.get('success', False)]),
            "failed": len([r for r in results if not r.get('success', False)]),
            "results": results
        }
    except Exception as e:
        logger.error(f"Error in batch verification: {e}")
        raise HTTPException(status_code=500, detail="Failed to perform batch verification")