from pydantic import BaseModel, validator
from typing import Optional
from datetime import datetime, date
from enum import Enum

from .common import BaseSchema

class InsuranceTypeEnum(str, Enum):
    PRIMARY = "primary"
    SECONDARY = "secondary"
    TERTIARY = "tertiary"

class CoverageStatusEnum(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    EXPIRED = "expired"
    CANCELLED = "cancelled"

class EligibilityStatusEnum(str, Enum):
    VERIFIED = "verified"
    PENDING = "pending"
    FAILED = "failed"
    EXPIRED = "expired"
    UNKNOWN = "unknown"

class InsuranceBase(BaseSchema):
    """Base insurance schema with common fields"""
    patient_id: int
    insurance_type: InsuranceTypeEnum
    coverage_status: CoverageStatusEnum = CoverageStatusEnum.ACTIVE
    
    # Insurance Company Information
    insurance_company: str
    insurance_plan_name: Optional[str] = None
    insurance_plan_type: Optional[str] = None  # HMO, PPO, EPO, etc.
    
    # Policy Information
    policy_number: str
    group_number: Optional[str] = None
    member_id: str
    
    # Subscriber Information
    subscriber_name: Optional[str] = None
    subscriber_relationship: Optional[str] = None  # self, spouse, child, etc.
    subscriber_date_of_birth: Optional[date] = None
    subscriber_gender: Optional[str] = None
    subscriber_ssn: Optional[str] = None  # Encrypted in production
    
    # Coverage Dates
    effective_date: Optional[date] = None
    termination_date: Optional[date] = None
    
    # Benefits and Coverage
    deductible_individual: Optional[float] = None
    deductible_family: Optional[float] = None
    deductible_met_individual: float = 0
    deductible_met_family: float = 0
    
    out_of_pocket_max_individual: Optional[float] = None
    out_of_pocket_max_family: Optional[float] = None
    out_of_pocket_met_individual: float = 0
    out_of_pocket_met_family: float = 0
    
    # Copay Information
    copay_primary_care: Optional[float] = None
    copay_specialist: Optional[float] = None
    copay_urgent_care: Optional[float] = None
    copay_emergency_room: Optional[float] = None
    
    # Coinsurance
    coinsurance_percentage: Optional[float] = None
    
    # Authorization Requirements
    requires_referral: bool = False
    requires_prior_auth: bool = False
    
    # Contact Information
    customer_service_phone: Optional[str] = None
    claims_address: Optional[str] = None
    
    # Eligibility Verification
    eligibility_status: EligibilityStatusEnum = EligibilityStatusEnum.UNKNOWN
    last_verification_date: Optional[datetime] = None
    next_verification_date: Optional[datetime] = None
    eligibility_response: Optional[str] = None  # Raw response from verification
    
    # Prior Authorization
    prior_auth_number: Optional[str] = None
    prior_auth_expiration: Optional[date] = None
    prior_auth_services: Optional[str] = None
    
    # Status and Metadata
    is_active: bool = True
    notes: Optional[str] = None

    @validator('insurance_company', 'policy_number', 'member_id')
    def validate_required_fields(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('This field is required and cannot be empty')
        return v.strip()

    @validator('subscriber_relationship')
    def validate_subscriber_relationship(cls, v):
        if v:
            valid_relationships = ['self', 'spouse', 'child', 'parent', 'sibling', 'other']
            if v.lower() not in valid_relationships:
                raise ValueError(f'Subscriber relationship must be one of: {valid_relationships}')
        return v

    @validator('insurance_plan_type')
    def validate_plan_type(cls, v):
        if v:
            valid_types = ['HMO', 'PPO', 'EPO', 'POS', 'HDHP', 'Other']
            if v.upper() not in [t.upper() for t in valid_types]:
                raise ValueError(f'Insurance plan type must be one of: {valid_types}')
        return v

    @validator('coinsurance_percentage')
    def validate_coinsurance(cls, v):
        if v is not None and (v < 0 or v > 100):
            raise ValueError('Coinsurance percentage must be between 0 and 100')
        return v

    @validator('deductible_individual', 'deductible_family', 'out_of_pocket_max_individual', 'out_of_pocket_max_family')
    def validate_positive_amounts(cls, v):
        if v is not None and v < 0:
            raise ValueError('Amount must be positive')
        return v

    @validator('termination_date')
    def validate_termination_date(cls, v, values):
        if v and 'effective_date' in values and values['effective_date']:
            if v <= values['effective_date']:
                raise ValueError('Termination date must be after effective date')
        return v

class InsuranceCreate(InsuranceBase):
    """Schema for creating an insurance record"""
    pass

class InsuranceUpdate(BaseSchema):
    """Schema for updating an insurance record (all fields optional)"""
    patient_id: Optional[int] = None
    insurance_type: Optional[InsuranceTypeEnum] = None
    coverage_status: Optional[CoverageStatusEnum] = None
    
    # Insurance Company Information
    insurance_company: Optional[str] = None
    insurance_plan_name: Optional[str] = None
    insurance_plan_type: Optional[str] = None
    
    # Policy Information
    policy_number: Optional[str] = None
    group_number: Optional[str] = None
    member_id: Optional[str] = None
    
    # Subscriber Information
    subscriber_name: Optional[str] = None
    subscriber_relationship: Optional[str] = None
    subscriber_date_of_birth: Optional[date] = None
    subscriber_gender: Optional[str] = None
    subscriber_ssn: Optional[str] = None
    
    # Coverage Dates
    effective_date: Optional[date] = None
    termination_date: Optional[date] = None
    
    # Benefits and Coverage
    deductible_individual: Optional[float] = None
    deductible_family: Optional[float] = None
    deductible_met_individual: Optional[float] = None
    deductible_met_family: Optional[float] = None
    
    out_of_pocket_max_individual: Optional[float] = None
    out_of_pocket_max_family: Optional[float] = None
    out_of_pocket_met_individual: Optional[float] = None
    out_of_pocket_met_family: Optional[float] = None
    
    # Copay Information
    copay_primary_care: Optional[float] = None
    copay_specialist: Optional[float] = None
    copay_urgent_care: Optional[float] = None
    copay_emergency_room: Optional[float] = None
    
    # Coinsurance
    coinsurance_percentage: Optional[float] = None
    
    # Authorization Requirements
    requires_referral: Optional[bool] = None
    requires_prior_auth: Optional[bool] = None
    
    # Contact Information
    customer_service_phone: Optional[str] = None
    claims_address: Optional[str] = None
    
    # Eligibility Verification
    eligibility_status: Optional[EligibilityStatusEnum] = None
    last_verification_date: Optional[datetime] = None
    next_verification_date: Optional[datetime] = None
    eligibility_response: Optional[str] = None
    
    # Prior Authorization
    prior_auth_number: Optional[str] = None
    prior_auth_expiration: Optional[date] = None
    prior_auth_services: Optional[str] = None
    
    # Status and Metadata
    is_active: Optional[bool] = None
    notes: Optional[str] = None

class InsuranceResponse(InsuranceBase):
    """Schema for insurance response"""
    id: int
    is_primary: bool
    is_expired: bool
    is_active_coverage: bool
    needs_verification: bool
    deductible_remaining_individual: float
    deductible_remaining_family: float
    created_at: datetime
    updated_at: datetime
    cerbo_insurance_id: Optional[str] = None

class InsuranceSummary(BaseSchema):
    """Schema for insurance summary"""
    id: int
    insurance_type: InsuranceTypeEnum
    insurance_company: str
    policy_number: str
    coverage_status: CoverageStatusEnum
    is_active_coverage: bool
    needs_verification: bool
    effective_date: Optional[date] = None
    termination_date: Optional[date] = None

class InsuranceSearch(BaseSchema):
    """Schema for insurance search parameters"""
    patient_id: Optional[int] = None
    insurance_type: Optional[InsuranceTypeEnum] = None
    coverage_status: Optional[CoverageStatusEnum] = None
    eligibility_status: Optional[EligibilityStatusEnum] = None
    insurance_company: Optional[str] = None
    policy_number: Optional[str] = None
    member_id: Optional[str] = None
    is_active: Optional[bool] = True
    needs_verification: Optional[bool] = None
    effective_date_start: Optional[date] = None
    effective_date_end: Optional[date] = None
    page: int = 1
    per_page: int = 50
    sort_by: str = "insurance_type"
    sort_order: str = "asc"

    @validator('per_page')
    def validate_per_page(cls, v):
        if v < 1 or v > 100:
            raise ValueError('per_page must be between 1 and 100')
        return v

class EligibilityVerificationRequest(BaseSchema):
    """Schema for eligibility verification request"""
    insurance_id: int
    service_type: Optional[str] = None  # general, specialist, emergency, etc.
    provider_npi: Optional[str] = None
    force_refresh: bool = False

class EligibilityVerificationResponse(BaseSchema):
    """Schema for eligibility verification response"""
    insurance_id: int
    verification_successful: bool
    eligibility_status: EligibilityStatusEnum
    verified_at: datetime
    benefits: Optional[dict] = None
    errors: Optional[list] = None
    raw_response: Optional[str] = None

class CoverageCalculationRequest(BaseSchema):
    """Schema for coverage calculation request"""
    insurance_id: int
    service_cost: float
    service_type: str = "general"  # general, primary_care, specialist, etc.
    cpt_code: Optional[str] = None
    diagnosis_code: Optional[str] = None

class CoverageCalculationResponse(BaseSchema):
    """Schema for coverage calculation response"""
    insurance_id: int
    service_cost: float
    patient_cost: float
    insurance_covers: float
    calculation_method: str
    breakdown: dict
    notes: Optional[str] = None

class PriorAuthorizationRequest(BaseSchema):
    """Schema for prior authorization request"""
    insurance_id: int
    service_description: str
    cpt_codes: list
    diagnosis_codes: list
    requested_date: date
    provider_info: dict
    patient_notes: Optional[str] = None

class PriorAuthorizationResponse(BaseSchema):
    """Schema for prior authorization response"""
    insurance_id: int
    authorization_number: Optional[str] = None
    status: str  # approved, denied, pending
    approved_services: Optional[list] = None
    expiration_date: Optional[date] = None
    notes: Optional[str] = None