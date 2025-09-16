from pydantic import BaseModel, validator
from typing import Optional, List
from datetime import datetime, date
from enum import Enum

from .common import BaseSchema

class BillingStatusEnum(str, Enum):
    DRAFT = "draft"
    PENDING = "pending"
    SUBMITTED = "submitted"
    PAID = "paid"
    PARTIALLY_PAID = "partially_paid"
    DENIED = "denied"
    APPEALED = "appealed"
    WRITTEN_OFF = "written_off"
    REFUNDED = "refunded"

class TransactionTypeEnum(str, Enum):
    CHARGE = "charge"
    PAYMENT = "payment"
    ADJUSTMENT = "adjustment"
    REFUND = "refund"
    WRITE_OFF = "write_off"

class PaymentMethodEnum(str, Enum):
    CASH = "cash"
    CHECK = "check"
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    BANK_TRANSFER = "bank_transfer"
    INSURANCE = "insurance"
    OTHER = "other"

class BillingBase(BaseSchema):
    """Base billing schema with common fields"""
    patient_id: int
    appointment_id: Optional[int] = None
    
    # Billing Identification
    invoice_number: Optional[str] = None
    claim_number: Optional[str] = None
    transaction_type: TransactionTypeEnum
    
    # Service Information
    service_date: datetime
    procedure_code: Optional[str] = None  # CPT code
    procedure_description: Optional[str] = None
    diagnosis_code: Optional[str] = None  # ICD-10 code
    diagnosis_description: Optional[str] = None
    
    # Provider Information
    rendering_provider: Optional[str] = None
    referring_provider: Optional[str] = None
    facility: Optional[str] = None
    
    # Financial Information
    charge_amount: float = 0
    allowed_amount: Optional[float] = None  # Insurance allowed amount
    paid_amount: float = 0
    adjustment_amount: float = 0
    balance_amount: float = 0
    
    # Insurance Information
    primary_insurance_paid: float = 0
    secondary_insurance_paid: float = 0
    patient_responsibility: float = 0
    
    # Payment Information
    payment_method: Optional[PaymentMethodEnum] = None
    payment_reference: Optional[str] = None  # Check number, transaction ID, etc.
    payment_date: Optional[datetime] = None
    
    # Status and Processing
    status: BillingStatusEnum = BillingStatusEnum.DRAFT
    submission_date: Optional[datetime] = None
    processing_date: Optional[datetime] = None
    
    # Denial and Appeal Information
    denial_reason: Optional[str] = None
    denial_code: Optional[str] = None
    appeal_date: Optional[datetime] = None
    appeal_reference: Optional[str] = None
    
    # Authorization
    authorization_number: Optional[str] = None
    authorization_date: Optional[datetime] = None
    
    # Billing Notes
    notes: Optional[str] = None
    internal_notes: Optional[str] = None
    
    # Follow-up
    follow_up_date: Optional[datetime] = None
    follow_up_notes: Optional[str] = None
    
    # Metadata
    created_by: Optional[str] = None
    updated_by: Optional[str] = None

    @validator('charge_amount', 'paid_amount', 'adjustment_amount', 'balance_amount')
    def validate_amounts(cls, v):
        if v < 0:
            raise ValueError('Amount cannot be negative')
        return v

    @validator('procedure_code')
    def validate_procedure_code(cls, v):
        if v and not v.isdigit():
            raise ValueError('Procedure code must contain only digits')
        return v

    @validator('diagnosis_code')
    def validate_diagnosis_code(cls, v):
        if v and len(v) > 10:
            raise ValueError('Diagnosis code cannot exceed 10 characters')
        return v

    @validator('payment_date')
    def validate_payment_date(cls, v, values):
        if v and 'service_date' in values and values['service_date']:
            if v < values['service_date']:
                raise ValueError('Payment date cannot be before service date')
        return v

class BillingCreate(BillingBase):
    """Schema for creating a billing record"""
    pass

class BillingUpdate(BaseSchema):
    """Schema for updating a billing record (all fields optional)"""
    patient_id: Optional[int] = None
    appointment_id: Optional[int] = None
    
    # Billing Identification
    invoice_number: Optional[str] = None
    claim_number: Optional[str] = None
    transaction_type: Optional[TransactionTypeEnum] = None
    
    # Service Information
    service_date: Optional[datetime] = None
    procedure_code: Optional[str] = None
    procedure_description: Optional[str] = None
    diagnosis_code: Optional[str] = None
    diagnosis_description: Optional[str] = None
    
    # Provider Information
    rendering_provider: Optional[str] = None
    referring_provider: Optional[str] = None
    facility: Optional[str] = None
    
    # Financial Information
    charge_amount: Optional[float] = None
    allowed_amount: Optional[float] = None
    paid_amount: Optional[float] = None
    adjustment_amount: Optional[float] = None
    balance_amount: Optional[float] = None
    
    # Insurance Information
    primary_insurance_paid: Optional[float] = None
    secondary_insurance_paid: Optional[float] = None
    patient_responsibility: Optional[float] = None
    
    # Payment Information
    payment_method: Optional[PaymentMethodEnum] = None
    payment_reference: Optional[str] = None
    payment_date: Optional[datetime] = None
    
    # Status and Processing
    status: Optional[BillingStatusEnum] = None
    submission_date: Optional[datetime] = None
    processing_date: Optional[datetime] = None
    
    # Denial and Appeal Information
    denial_reason: Optional[str] = None
    denial_code: Optional[str] = None
    appeal_date: Optional[datetime] = None
    appeal_reference: Optional[str] = None
    
    # Authorization
    authorization_number: Optional[str] = None
    authorization_date: Optional[datetime] = None
    
    # Billing Notes
    notes: Optional[str] = None
    internal_notes: Optional[str] = None
    
    # Follow-up
    follow_up_date: Optional[datetime] = None
    follow_up_notes: Optional[str] = None
    
    # Metadata
    created_by: Optional[str] = None
    updated_by: Optional[str] = None

class BillingResponse(BillingBase):
    """Schema for billing response"""
    id: int
    is_paid_in_full: bool
    is_overdue: bool
    payment_percentage: float
    days_outstanding: int
    created_at: datetime
    updated_at: datetime
    cerbo_billing_id: Optional[str] = None
    clearinghouse_id: Optional[str] = None

class BillingSummary(BaseSchema):
    """Schema for billing summary"""
    id: int
    patient_id: int
    invoice_number: Optional[str] = None
    service_date: datetime
    transaction_type: TransactionTypeEnum
    status: BillingStatusEnum
    charge_amount: float
    paid_amount: float
    balance_amount: float
    is_overdue: bool
    days_outstanding: int

class BillingSearch(BaseSchema):
    """Schema for billing search parameters"""
    patient_id: Optional[int] = None
    transaction_type: Optional[TransactionTypeEnum] = None
    status: Optional[BillingStatusEnum] = None
    payment_method: Optional[PaymentMethodEnum] = None
    procedure_code: Optional[str] = None
    diagnosis_code: Optional[str] = None
    invoice_number: Optional[str] = None
    claim_number: Optional[str] = None
    service_date_start: Optional[datetime] = None
    service_date_end: Optional[datetime] = None
    payment_date_start: Optional[datetime] = None
    payment_date_end: Optional[datetime] = None
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None
    is_overdue: Optional[bool] = None
    has_balance: Optional[bool] = None
    page: int = 1
    per_page: int = 50
    sort_by: str = "service_date"
    sort_order: str = "desc"

    @validator('per_page')
    def validate_per_page(cls, v):
        if v < 1 or v > 100:
            raise ValueError('per_page must be between 1 and 100')
        return v

    @validator('min_amount', 'max_amount')
    def validate_amounts(cls, v):
        if v is not None and v < 0:
            raise ValueError('Amount must be positive')
        return v

class PaymentRequest(BaseSchema):
    """Schema for processing payment"""
    billing_id: int
    amount: float
    payment_method: PaymentMethodEnum
    payment_reference: Optional[str] = None
    payment_date: Optional[datetime] = None
    notes: Optional[str] = None

    @validator('amount')
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError('Payment amount must be positive')
        return v

class PaymentResponse(BaseSchema):
    """Schema for payment response"""
    billing_id: int
    payment_amount: float
    new_balance: float
    payment_successful: bool
    transaction_id: Optional[str] = None
    processed_at: datetime

class InsurancePaymentRequest(BaseSchema):
    """Schema for insurance payment"""
    billing_id: int
    amount: float
    is_primary: bool = True
    insurance_company: Optional[str] = None
    check_number: Optional[str] = None
    explanation_of_benefits: Optional[str] = None

class AdjustmentRequest(BaseSchema):
    """Schema for billing adjustment"""
    billing_id: int
    adjustment_amount: float
    adjustment_reason: str
    adjustment_type: str = "write_off"  # write_off, discount, correction
    notes: Optional[str] = None

    @validator('adjustment_amount')
    def validate_amount(cls, v):
        if v < 0:
            raise ValueError('Adjustment amount cannot be negative')
        return v

class BillingReport(BaseSchema):
    """Schema for billing reports"""
    report_type: str
    date_range: dict
    filters: dict
    summary: dict
    details: List[dict]
    generated_at: datetime

class AgingReport(BaseSchema):
    """Schema for aging report"""
    patient_id: int
    patient_name: str
    total_outstanding: float
    current: float  # 0-30 days
    days_31_60: float
    days_61_90: float
    days_91_120: float
    over_120_days: float
    oldest_invoice_date: Optional[date] = None

class PaymentHistoryEntry(BaseSchema):
    """Schema for payment history entry"""
    date: datetime
    amount: float
    method: PaymentMethodEnum
    reference: Optional[str] = None
    notes: Optional[str] = None

class ClaimSubmissionRequest(BaseSchema):
    """Schema for claim submission"""
    billing_ids: List[int]
    clearinghouse: Optional[str] = None
    priority: str = "normal"  # normal, urgent
    test_mode: bool = False

class ClaimSubmissionResponse(BaseSchema):
    """Schema for claim submission response"""
    submission_id: str
    billing_ids: List[int]
    submitted_count: int
    failed_count: int
    errors: List[dict]
    submitted_at: datetime
    estimated_processing_time: Optional[str] = None