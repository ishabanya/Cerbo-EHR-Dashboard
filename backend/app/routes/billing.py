from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from ..utils.database import get_db
from ..services.billing_service import BillingService
from ..schemas.billing import (
    BillingCreate, BillingUpdate, BillingResponse,
    BillingSearch, BillingSummary, PaymentRequest, PaymentResponse,
    InsurancePaymentRequest, AdjustmentRequest, BillingReport,
    AgingReport, PaymentHistoryEntry, ClaimSubmissionRequest,
    ClaimSubmissionResponse, BillingStatusEnum, TransactionTypeEnum,
    PaymentMethodEnum
)
from ..schemas.common import PaginatedResponse, SuccessResponse

logger = logging.getLogger(__name__)

router = APIRouter()

def get_billing_service(db: Session = Depends(get_db)) -> BillingService:
    """Dependency to get billing service"""
    return BillingService(db)

@router.get("/", response_model=PaginatedResponse[BillingResponse])
async def get_billing_records(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    patient_id: Optional[int] = Query(None),
    transaction_type: Optional[TransactionTypeEnum] = Query(None),
    status: Optional[BillingStatusEnum] = Query(None),
    is_overdue: Optional[bool] = Query(None),
    has_balance: Optional[bool] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    billing_service: BillingService = Depends(get_billing_service)
):
    """Get billing records with pagination and filtering"""
    try:
        skip = (page - 1) * per_page
        
        # Build filters
        filters = {}
        if patient_id:
            filters['patient_id'] = patient_id
        if transaction_type:
            filters['transaction_type'] = transaction_type
        if status:
            filters['status'] = status
        if is_overdue is not None:
            filters['is_overdue'] = is_overdue
        if has_balance is not None:
            filters['has_balance'] = has_balance
        if start_date:
            filters['service_date'] = {'gte': start_date}
        if end_date:
            if 'service_date' in filters:
                filters['service_date']['lte'] = end_date
            else:
                filters['service_date'] = {'lte': end_date}
        
        records = billing_service.search_billing(
            filters=filters,
            skip=skip,
            limit=per_page
        )
        
        total = billing_service.count(filters)
        pages = (total + per_page - 1) // per_page
        
        return PaginatedResponse(
            items=[BillingResponse.from_orm(record) for record in records],
            total=total,
            page=page,
            pages=pages,
            per_page=per_page,
            has_next=page < pages,
            has_prev=page > 1
        )
    except Exception as e:
        logger.error(f"Error getting billing records: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve billing records")

@router.post("/", response_model=BillingResponse, status_code=201)
async def create_billing_record(
    billing_data: BillingCreate,
    billing_service: BillingService = Depends(get_billing_service)
):
    """Create a new billing record"""
    try:
        record = billing_service.create(billing_data.dict())
        return BillingResponse.from_orm(record)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating billing record: {e}")
        raise HTTPException(status_code=500, detail="Failed to create billing record")

@router.get("/search", response_model=List[BillingResponse])
async def search_billing_records(
    search_params: BillingSearch = Depends(),
    billing_service: BillingService = Depends(get_billing_service)
):
    """Advanced billing record search"""
    try:
        skip = (search_params.page - 1) * search_params.per_page
        
        records = billing_service.advanced_search(
            search_params=search_params,
            skip=skip,
            limit=search_params.per_page
        )
        
        return [BillingResponse.from_orm(record) for record in records]
    except Exception as e:
        logger.error(f"Error searching billing records: {e}")
        raise HTTPException(status_code=500, detail="Failed to search billing records")

@router.get("/{billing_id}", response_model=BillingResponse)
async def get_billing_record(
    billing_id: int,
    billing_service: BillingService = Depends(get_billing_service)
):
    """Get a specific billing record by ID"""
    try:
        record = billing_service.get_by_id(billing_id)
        if not record:
            raise HTTPException(status_code=404, detail="Billing record not found")
        return BillingResponse.from_orm(record)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting billing record {billing_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve billing record")

@router.put("/{billing_id}", response_model=BillingResponse)
async def update_billing_record(
    billing_id: int,
    billing_data: BillingUpdate,
    billing_service: BillingService = Depends(get_billing_service)
):
    """Update a billing record"""
    try:
        update_data = {k: v for k, v in billing_data.dict().items() if v is not None}
        record = billing_service.update(billing_id, update_data)
        
        if not record:
            raise HTTPException(status_code=404, detail="Billing record not found")
        
        return BillingResponse.from_orm(record)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating billing record {billing_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update billing record")

@router.delete("/{billing_id}", response_model=SuccessResponse)
async def delete_billing_record(
    billing_id: int,
    billing_service: BillingService = Depends(get_billing_service)
):
    """Delete a billing record"""
    try:
        success = billing_service.delete(billing_id)
        if not success:
            raise HTTPException(status_code=404, detail="Billing record not found")
        
        return SuccessResponse(message="Billing record successfully deleted")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting billing record {billing_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete billing record")

@router.get("/patient/{patient_id}", response_model=List[BillingSummary])
async def get_patient_billing(
    patient_id: int,
    status: Optional[BillingStatusEnum] = Query(None),
    has_balance: Optional[bool] = Query(None),
    limit: int = Query(100, le=500),
    billing_service: BillingService = Depends(get_billing_service)
):
    """Get all billing records for a specific patient"""
    try:
        records = billing_service.get_patient_billing(
            patient_id=patient_id,
            status=status,
            has_balance=has_balance,
            limit=limit
        )
        
        return [BillingSummary.from_orm(record) for record in records]
    except Exception as e:
        logger.error(f"Error getting patient billing {patient_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve patient billing")

@router.post("/process-payment", response_model=PaymentResponse)
async def process_payment(
    payment_request: PaymentRequest,
    billing_service: BillingService = Depends(get_billing_service)
):
    """Process a patient payment"""
    try:
        result = billing_service.process_payment(
            billing_id=payment_request.billing_id,
            amount=payment_request.amount,
            payment_method=payment_request.payment_method,
            payment_reference=payment_request.payment_reference,
            payment_date=payment_request.payment_date,
            notes=payment_request.notes
        )
        
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error processing payment: {e}")
        raise HTTPException(status_code=500, detail="Failed to process payment")

@router.post("/insurance-payment", response_model=BillingResponse)
async def process_insurance_payment(
    payment_request: InsurancePaymentRequest,
    billing_service: BillingService = Depends(get_billing_service)
):
    """Process an insurance payment"""
    try:
        record = billing_service.process_insurance_payment(
            billing_id=payment_request.billing_id,
            amount=payment_request.amount,
            is_primary=payment_request.is_primary,
            insurance_company=payment_request.insurance_company,
            check_number=payment_request.check_number,
            explanation_of_benefits=payment_request.explanation_of_benefits
        )
        
        if not record:
            raise HTTPException(status_code=404, detail="Billing record not found")
        
        return BillingResponse.from_orm(record)
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error processing insurance payment: {e}")
        raise HTTPException(status_code=500, detail="Failed to process insurance payment")

@router.post("/adjustment", response_model=BillingResponse)
async def process_adjustment(
    adjustment_request: AdjustmentRequest,
    billing_service: BillingService = Depends(get_billing_service)
):
    """Process a billing adjustment (write-off, discount, etc.)"""
    try:
        record = billing_service.process_adjustment(
            billing_id=adjustment_request.billing_id,
            adjustment_amount=adjustment_request.adjustment_amount,
            adjustment_reason=adjustment_request.adjustment_reason,
            adjustment_type=adjustment_request.adjustment_type,
            notes=adjustment_request.notes
        )
        
        if not record:
            raise HTTPException(status_code=404, detail="Billing record not found")
        
        return BillingResponse.from_orm(record)
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error processing adjustment: {e}")
        raise HTTPException(status_code=500, detail="Failed to process adjustment")

@router.get("/overdue", response_model=List[BillingResponse])
async def get_overdue_bills(
    days_overdue: int = Query(30, ge=1),
    limit: int = Query(100, le=500),
    billing_service: BillingService = Depends(get_billing_service)
):
    """Get overdue billing records"""
    try:
        records = billing_service.get_overdue_bills(
            days_overdue=days_overdue,
            limit=limit
        )
        
        return [BillingResponse.from_orm(record) for record in records]
    except Exception as e:
        logger.error(f"Error getting overdue bills: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve overdue bills")

@router.get("/aging-report", response_model=List[AgingReport])
async def get_aging_report(
    as_of_date: Optional[str] = Query(None),
    patient_id: Optional[int] = Query(None),
    billing_service: BillingService = Depends(get_billing_service)
):
    """Get accounts receivable aging report"""
    try:
        report = billing_service.generate_aging_report(
            as_of_date=as_of_date,
            patient_id=patient_id
        )
        
        return report
    except Exception as e:
        logger.error(f"Error generating aging report: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate aging report")

@router.get("/{billing_id}/payment-history", response_model=List[PaymentHistoryEntry])
async def get_payment_history(
    billing_id: int,
    billing_service: BillingService = Depends(get_billing_service)
):
    """Get payment history for a billing record"""
    try:
        history = billing_service.get_payment_history(billing_id)
        
        return history
    except Exception as e:
        logger.error(f"Error getting payment history {billing_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve payment history")

@router.post("/submit-claims", response_model=ClaimSubmissionResponse)
async def submit_claims(
    submission_request: ClaimSubmissionRequest,
    billing_service: BillingService = Depends(get_billing_service)
):
    """Submit billing claims to clearinghouse"""
    try:
        result = billing_service.submit_claims(
            billing_ids=submission_request.billing_ids,
            clearinghouse=submission_request.clearinghouse,
            priority=submission_request.priority,
            test_mode=submission_request.test_mode
        )
        
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error submitting claims: {e}")
        raise HTTPException(status_code=500, detail="Failed to submit claims")

@router.get("/reports/summary")
async def get_billing_summary(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    billing_service: BillingService = Depends(get_billing_service)
):
    """Get billing summary report"""
    try:
        summary = billing_service.get_billing_summary(
            start_date=start_date,
            end_date=end_date
        )
        
        return summary
    except Exception as e:
        logger.error(f"Error getting billing summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve billing summary")

@router.get("/reports/revenue")
async def get_revenue_report(
    start_date: str = Query(...),
    end_date: str = Query(...),
    group_by: str = Query("month"),  # day, week, month, year
    billing_service: BillingService = Depends(get_billing_service)
):
    """Get revenue report"""
    try:
        report = billing_service.generate_revenue_report(
            start_date=start_date,
            end_date=end_date,
            group_by=group_by
        )
        
        return report
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating revenue report: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate revenue report")

@router.get("/stats/dashboard")
async def get_billing_dashboard(
    billing_service: BillingService = Depends(get_billing_service)
):
    """Get billing dashboard statistics"""
    try:
        dashboard = billing_service.get_billing_dashboard()
        
        return dashboard
    except Exception as e:
        logger.error(f"Error getting billing dashboard: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve billing dashboard")

@router.post("/batch-update-status", response_model=dict)
async def batch_update_status(
    billing_ids: List[int],
    new_status: BillingStatusEnum,
    reason: Optional[str] = Query(None),
    billing_service: BillingService = Depends(get_billing_service)
):
    """Batch update status for multiple billing records"""
    try:
        results = billing_service.batch_update_status(
            billing_ids=billing_ids,
            new_status=new_status,
            reason=reason
        )
        
        return {
            "total_processed": len(billing_ids),
            "successful": len([r for r in results if r.get('success', False)]),
            "failed": len([r for r in results if not r.get('success', False)]),
            "results": results
        }
    except Exception as e:
        logger.error(f"Error in batch status update: {e}")
        raise HTTPException(status_code=500, detail="Failed to perform batch status update")

@router.get("/denied-claims", response_model=List[BillingResponse])
async def get_denied_claims(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    limit: int = Query(100, le=500),
    billing_service: BillingService = Depends(get_billing_service)
):
    """Get denied insurance claims that need attention"""
    try:
        records = billing_service.get_denied_claims(
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )
        
        return [BillingResponse.from_orm(record) for record in records]
    except Exception as e:
        logger.error(f"Error getting denied claims: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve denied claims")

@router.post("/{billing_id}/appeal", response_model=BillingResponse)
async def appeal_denied_claim(
    billing_id: int,
    appeal_reason: str = Query(...),
    supporting_documents: Optional[List[str]] = Query(None),
    billing_service: BillingService = Depends(get_billing_service)
):
    """Appeal a denied claim"""
    try:
        record = billing_service.appeal_claim(
            billing_id=billing_id,
            appeal_reason=appeal_reason,
            supporting_documents=supporting_documents
        )
        
        if not record:
            raise HTTPException(status_code=404, detail="Billing record not found")
        
        return BillingResponse.from_orm(record)
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error appealing claim {billing_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to appeal claim")