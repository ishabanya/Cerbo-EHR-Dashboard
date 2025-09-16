from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, Enum, ForeignKey, Numeric, Date
from sqlalchemy.orm import relationship
from datetime import datetime, date
import enum

from .base import Base

class InsuranceTypeEnum(str, enum.Enum):
    PRIMARY = "primary"
    SECONDARY = "secondary"
    TERTIARY = "tertiary"

class CoverageStatusEnum(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    EXPIRED = "expired"
    CANCELLED = "cancelled"

class EligibilityStatusEnum(str, enum.Enum):
    VERIFIED = "verified"
    PENDING = "pending"
    FAILED = "failed"
    EXPIRED = "expired"
    UNKNOWN = "unknown"

class Insurance(Base):
    __tablename__ = "insurance"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign Key
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    
    # Insurance Classification
    insurance_type = Column(Enum(InsuranceTypeEnum), nullable=False, index=True)
    coverage_status = Column(Enum(CoverageStatusEnum), default=CoverageStatusEnum.ACTIVE, nullable=False)
    
    # Insurance Company Information
    insurance_company = Column(String(200), nullable=False, index=True)
    insurance_plan_name = Column(String(200), nullable=True)
    insurance_plan_type = Column(String(100), nullable=True)  # HMO, PPO, EPO, etc.
    
    # Policy Information
    policy_number = Column(String(100), nullable=False, index=True)
    group_number = Column(String(100), nullable=True)
    member_id = Column(String(100), nullable=False, index=True)
    
    # Subscriber Information
    subscriber_name = Column(String(200), nullable=True)
    subscriber_relationship = Column(String(50), nullable=True)  # self, spouse, child, etc.
    subscriber_date_of_birth = Column(Date, nullable=True)
    subscriber_gender = Column(String(20), nullable=True)
    subscriber_ssn = Column(String(11), nullable=True)  # Encrypted in production
    
    # Coverage Dates
    effective_date = Column(Date, nullable=True)
    termination_date = Column(Date, nullable=True)
    
    # Benefits and Coverage
    deductible_individual = Column(Numeric(10, 2), nullable=True)
    deductible_family = Column(Numeric(10, 2), nullable=True)
    deductible_met_individual = Column(Numeric(10, 2), default=0)
    deductible_met_family = Column(Numeric(10, 2), default=0)
    
    out_of_pocket_max_individual = Column(Numeric(10, 2), nullable=True)
    out_of_pocket_max_family = Column(Numeric(10, 2), nullable=True)
    out_of_pocket_met_individual = Column(Numeric(10, 2), default=0)
    out_of_pocket_met_family = Column(Numeric(10, 2), default=0)
    
    # Copay Information
    copay_primary_care = Column(Numeric(6, 2), nullable=True)
    copay_specialist = Column(Numeric(6, 2), nullable=True)
    copay_urgent_care = Column(Numeric(6, 2), nullable=True)
    copay_emergency_room = Column(Numeric(6, 2), nullable=True)
    
    # Coinsurance
    coinsurance_percentage = Column(Numeric(5, 2), nullable=True)
    
    # Authorization Requirements
    requires_referral = Column(Boolean, default=False)
    requires_prior_auth = Column(Boolean, default=False)
    
    # Contact Information
    customer_service_phone = Column(String(20), nullable=True)
    claims_address = Column(Text, nullable=True)
    
    # Eligibility Verification
    eligibility_status = Column(Enum(EligibilityStatusEnum), default=EligibilityStatusEnum.UNKNOWN, nullable=False)
    last_verification_date = Column(DateTime, nullable=True)
    next_verification_date = Column(DateTime, nullable=True)
    eligibility_response = Column(Text, nullable=True)  # Raw response from verification
    
    # Prior Authorization
    prior_auth_number = Column(String(100), nullable=True)
    prior_auth_expiration = Column(Date, nullable=True)
    prior_auth_services = Column(Text, nullable=True)
    
    # Status and Metadata
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Notes
    notes = Column(Text, nullable=True)
    
    # External System IDs
    cerbo_insurance_id = Column(String(100), nullable=True, unique=True, index=True)
    
    # Relationships
    patient = relationship("Patient", back_populates="insurance_records")
    
    def __repr__(self):
        return f"<Insurance(id={self.id}, patient_id={self.patient_id}, company='{self.insurance_company}', type='{self.insurance_type}')>"
    
    @property
    def is_primary(self) -> bool:
        return self.insurance_type == InsuranceTypeEnum.PRIMARY
    
    @property
    def is_expired(self) -> bool:
        if self.termination_date:
            return self.termination_date < date.today()
        return False
    
    @property
    def is_active_coverage(self) -> bool:
        return (self.coverage_status == CoverageStatusEnum.ACTIVE and 
                not self.is_expired and 
                self.is_active)
    
    @property
    def needs_verification(self) -> bool:
        if not self.last_verification_date:
            return True
        
        if self.next_verification_date:
            return datetime.utcnow().date() >= self.next_verification_date.date()
        
        # Default: verify if last verification was more than 30 days ago
        from datetime import timedelta
        threshold = datetime.utcnow() - timedelta(days=30)
        return self.last_verification_date < threshold
    
    @property
    def deductible_remaining_individual(self) -> float:
        if self.deductible_individual and self.deductible_met_individual:
            remaining = float(self.deductible_individual) - float(self.deductible_met_individual)
            return max(0, remaining)
        return 0
    
    @property
    def deductible_remaining_family(self) -> float:
        if self.deductible_family and self.deductible_met_family:
            remaining = float(self.deductible_family) - float(self.deductible_met_family)
            return max(0, remaining)
        return 0
    
    def get_estimated_patient_cost(self, service_cost: float, service_type: str = "general") -> dict:
        """Calculate estimated patient cost for a service"""
        if not self.is_active_coverage:
            return {"patient_cost": service_cost, "reason": "No active coverage"}
        
        # Simple calculation - would be more complex in real implementation
        copay = 0
        if service_type == "primary_care" and self.copay_primary_care:
            copay = float(self.copay_primary_care)
        elif service_type == "specialist" and self.copay_specialist:
            copay = float(self.copay_specialist)
        
        # If there's a copay, that's typically the patient cost for covered services
        if copay > 0:
            return {
                "patient_cost": copay,
                "insurance_covers": service_cost - copay,
                "calculation_method": "copay"
            }
        
        # Otherwise, apply deductible and coinsurance logic
        deductible_remaining = self.deductible_remaining_individual
        coinsurance = float(self.coinsurance_percentage or 0) / 100
        
        if deductible_remaining > 0:
            if service_cost <= deductible_remaining:
                return {
                    "patient_cost": service_cost,
                    "insurance_covers": 0,
                    "calculation_method": "deductible_not_met"
                }
            else:
                deductible_portion = deductible_remaining
                remaining_cost = service_cost - deductible_remaining
                coinsurance_portion = remaining_cost * coinsurance
                total_patient_cost = deductible_portion + coinsurance_portion
                
                return {
                    "patient_cost": round(total_patient_cost, 2),
                    "insurance_covers": round(service_cost - total_patient_cost, 2),
                    "calculation_method": "deductible_plus_coinsurance"
                }
        else:
            # Deductible met, only coinsurance applies
            patient_cost = service_cost * coinsurance
            return {
                "patient_cost": round(patient_cost, 2),
                "insurance_covers": round(service_cost - patient_cost, 2),
                "calculation_method": "coinsurance_only"
            }
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "patient_id": self.patient_id,
            "insurance_type": self.insurance_type.value if self.insurance_type else None,
            "coverage_status": self.coverage_status.value if self.coverage_status else None,
            "insurance_company": self.insurance_company,
            "insurance_plan_name": self.insurance_plan_name,
            "insurance_plan_type": self.insurance_plan_type,
            "policy_number": self.policy_number,
            "group_number": self.group_number,
            "member_id": self.member_id,
            "subscriber_name": self.subscriber_name,
            "subscriber_relationship": self.subscriber_relationship,
            "subscriber_date_of_birth": self.subscriber_date_of_birth.isoformat() if self.subscriber_date_of_birth else None,
            "subscriber_gender": self.subscriber_gender,
            "effective_date": self.effective_date.isoformat() if self.effective_date else None,
            "termination_date": self.termination_date.isoformat() if self.termination_date else None,
            "deductible_individual": float(self.deductible_individual) if self.deductible_individual else None,
            "deductible_family": float(self.deductible_family) if self.deductible_family else None,
            "deductible_met_individual": float(self.deductible_met_individual) if self.deductible_met_individual else 0,
            "deductible_met_family": float(self.deductible_met_family) if self.deductible_met_family else 0,
            "deductible_remaining_individual": self.deductible_remaining_individual,
            "deductible_remaining_family": self.deductible_remaining_family,
            "out_of_pocket_max_individual": float(self.out_of_pocket_max_individual) if self.out_of_pocket_max_individual else None,
            "out_of_pocket_max_family": float(self.out_of_pocket_max_family) if self.out_of_pocket_max_family else None,
            "out_of_pocket_met_individual": float(self.out_of_pocket_met_individual) if self.out_of_pocket_met_individual else 0,
            "out_of_pocket_met_family": float(self.out_of_pocket_met_family) if self.out_of_pocket_met_family else 0,
            "copay_primary_care": float(self.copay_primary_care) if self.copay_primary_care else None,
            "copay_specialist": float(self.copay_specialist) if self.copay_specialist else None,
            "copay_urgent_care": float(self.copay_urgent_care) if self.copay_urgent_care else None,
            "copay_emergency_room": float(self.copay_emergency_room) if self.copay_emergency_room else None,
            "coinsurance_percentage": float(self.coinsurance_percentage) if self.coinsurance_percentage else None,
            "requires_referral": self.requires_referral,
            "requires_prior_auth": self.requires_prior_auth,
            "customer_service_phone": self.customer_service_phone,
            "claims_address": self.claims_address,
            "eligibility_status": self.eligibility_status.value if self.eligibility_status else None,
            "last_verification_date": self.last_verification_date.isoformat() if self.last_verification_date else None,
            "next_verification_date": self.next_verification_date.isoformat() if self.next_verification_date else None,
            "eligibility_response": self.eligibility_response,
            "prior_auth_number": self.prior_auth_number,
            "prior_auth_expiration": self.prior_auth_expiration.isoformat() if self.prior_auth_expiration else None,
            "prior_auth_services": self.prior_auth_services,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "notes": self.notes,
            "cerbo_insurance_id": self.cerbo_insurance_id,
            "is_primary": self.is_primary,
            "is_expired": self.is_expired,
            "is_active_coverage": self.is_active_coverage,
            "needs_verification": self.needs_verification
        }