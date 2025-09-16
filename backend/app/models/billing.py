from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, Enum, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from .base import Base

class BillingStatusEnum(str, enum.Enum):
    DRAFT = "draft"
    PENDING = "pending"
    SUBMITTED = "submitted"
    PAID = "paid"
    PARTIALLY_PAID = "partially_paid"
    DENIED = "denied"
    APPEALED = "appealed"
    WRITTEN_OFF = "written_off"
    REFUNDED = "refunded"

class TransactionTypeEnum(str, enum.Enum):
    CHARGE = "charge"
    PAYMENT = "payment"
    ADJUSTMENT = "adjustment"
    REFUND = "refund"
    WRITE_OFF = "write_off"

class PaymentMethodEnum(str, enum.Enum):
    CASH = "cash"
    CHECK = "check"
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    BANK_TRANSFER = "bank_transfer"
    INSURANCE = "insurance"
    OTHER = "other"

class Billing(Base):
    __tablename__ = "billing"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign Keys
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=True, index=True)
    
    # Billing Identification
    invoice_number = Column(String(50), unique=True, nullable=True, index=True)
    claim_number = Column(String(50), nullable=True, index=True)
    transaction_type = Column(Enum(TransactionTypeEnum), nullable=False, index=True)
    
    # Service Information
    service_date = Column(DateTime, nullable=False, index=True)
    procedure_code = Column(String(10), nullable=True, index=True)  # CPT code
    procedure_description = Column(String(500), nullable=True)
    diagnosis_code = Column(String(10), nullable=True, index=True)  # ICD-10 code
    diagnosis_description = Column(String(500), nullable=True)
    
    # Provider Information
    rendering_provider = Column(String(200), nullable=True)
    referring_provider = Column(String(200), nullable=True)
    facility = Column(String(200), nullable=True)
    
    # Financial Information
    charge_amount = Column(Numeric(10, 2), nullable=False, default=0)
    allowed_amount = Column(Numeric(10, 2), nullable=True)  # Insurance allowed amount
    paid_amount = Column(Numeric(10, 2), nullable=False, default=0)
    adjustment_amount = Column(Numeric(10, 2), nullable=False, default=0)
    balance_amount = Column(Numeric(10, 2), nullable=False, default=0)
    
    # Insurance Information
    primary_insurance_paid = Column(Numeric(10, 2), nullable=False, default=0)
    secondary_insurance_paid = Column(Numeric(10, 2), nullable=False, default=0)
    patient_responsibility = Column(Numeric(10, 2), nullable=False, default=0)
    
    # Payment Information
    payment_method = Column(Enum(PaymentMethodEnum), nullable=True)
    payment_reference = Column(String(100), nullable=True)  # Check number, transaction ID, etc.
    payment_date = Column(DateTime, nullable=True)
    
    # Status and Processing
    status = Column(Enum(BillingStatusEnum), default=BillingStatusEnum.DRAFT, nullable=False, index=True)
    submission_date = Column(DateTime, nullable=True)
    processing_date = Column(DateTime, nullable=True)
    
    # Denial and Appeal Information
    denial_reason = Column(Text, nullable=True)
    denial_code = Column(String(20), nullable=True)
    appeal_date = Column(DateTime, nullable=True)
    appeal_reference = Column(String(100), nullable=True)
    
    # Authorization
    authorization_number = Column(String(100), nullable=True)
    authorization_date = Column(DateTime, nullable=True)
    
    # Billing Notes
    notes = Column(Text, nullable=True)
    internal_notes = Column(Text, nullable=True)
    
    # Follow-up
    follow_up_date = Column(DateTime, nullable=True)
    follow_up_notes = Column(Text, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = Column(String(100), nullable=True)
    updated_by = Column(String(100), nullable=True)
    
    # External System IDs
    cerbo_billing_id = Column(String(100), nullable=True, unique=True, index=True)
    clearinghouse_id = Column(String(100), nullable=True)
    
    # Relationships
    patient = relationship("Patient", back_populates="billing_records")
    
    def __repr__(self):
        return f"<Billing(id={self.id}, patient_id={self.patient_id}, invoice='{self.invoice_number}', amount='{self.charge_amount}')>"
    
    @property
    def is_paid_in_full(self) -> bool:
        return self.balance_amount == 0 and self.charge_amount > 0
    
    @property
    def is_overdue(self) -> bool:
        if self.is_paid_in_full or not self.service_date:
            return False
        
        # Consider overdue if service was more than 30 days ago and has balance
        from datetime import timedelta
        threshold = datetime.utcnow() - timedelta(days=30)
        return self.service_date < threshold and self.balance_amount > 0
    
    @property
    def payment_percentage(self) -> float:
        if self.charge_amount == 0:
            return 0
        return (float(self.paid_amount) / float(self.charge_amount)) * 100
    
    @property
    def days_outstanding(self) -> int:
        if not self.service_date or self.is_paid_in_full:
            return 0
        
        delta = datetime.utcnow() - self.service_date
        return delta.days
    
    def calculate_balance(self) -> None:
        """Recalculate the balance amount based on charges, payments, and adjustments"""
        self.balance_amount = (self.charge_amount - 
                             self.paid_amount - 
                             self.adjustment_amount - 
                             self.primary_insurance_paid - 
                             self.secondary_insurance_paid)
    
    def add_payment(self, amount: float, method: PaymentMethodEnum, reference: str = None) -> None:
        """Add a payment to this billing record"""
        self.paid_amount += amount
        self.payment_method = method
        self.payment_reference = reference
        self.payment_date = datetime.utcnow()
        self.calculate_balance()
        
        if self.balance_amount <= 0:
            self.status = BillingStatusEnum.PAID
        elif self.paid_amount > 0:
            self.status = BillingStatusEnum.PARTIALLY_PAID
    
    def add_insurance_payment(self, amount: float, is_primary: bool = True) -> None:
        """Add an insurance payment"""
        if is_primary:
            self.primary_insurance_paid += amount
        else:
            self.secondary_insurance_paid += amount
        
        self.calculate_balance()
        
        if self.balance_amount <= 0:
            self.status = BillingStatusEnum.PAID
        elif (self.primary_insurance_paid + self.secondary_insurance_paid) > 0:
            self.status = BillingStatusEnum.PARTIALLY_PAID
    
    def add_adjustment(self, amount: float, reason: str = None) -> None:
        """Add an adjustment (typically a write-off or discount)"""
        self.adjustment_amount += amount
        if reason:
            self.notes = f"{self.notes or ''}\nAdjustment: {reason}".strip()
        self.calculate_balance()
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "patient_id": self.patient_id,
            "appointment_id": self.appointment_id,
            "invoice_number": self.invoice_number,
            "claim_number": self.claim_number,
            "transaction_type": self.transaction_type.value if self.transaction_type else None,
            "service_date": self.service_date.isoformat() if self.service_date else None,
            "procedure_code": self.procedure_code,
            "procedure_description": self.procedure_description,
            "diagnosis_code": self.diagnosis_code,
            "diagnosis_description": self.diagnosis_description,
            "rendering_provider": self.rendering_provider,
            "referring_provider": self.referring_provider,
            "facility": self.facility,
            "charge_amount": float(self.charge_amount) if self.charge_amount else 0,
            "allowed_amount": float(self.allowed_amount) if self.allowed_amount else None,
            "paid_amount": float(self.paid_amount) if self.paid_amount else 0,
            "adjustment_amount": float(self.adjustment_amount) if self.adjustment_amount else 0,
            "balance_amount": float(self.balance_amount) if self.balance_amount else 0,
            "primary_insurance_paid": float(self.primary_insurance_paid) if self.primary_insurance_paid else 0,
            "secondary_insurance_paid": float(self.secondary_insurance_paid) if self.secondary_insurance_paid else 0,
            "patient_responsibility": float(self.patient_responsibility) if self.patient_responsibility else 0,
            "payment_method": self.payment_method.value if self.payment_method else None,
            "payment_reference": self.payment_reference,
            "payment_date": self.payment_date.isoformat() if self.payment_date else None,
            "status": self.status.value if self.status else None,
            "submission_date": self.submission_date.isoformat() if self.submission_date else None,
            "processing_date": self.processing_date.isoformat() if self.processing_date else None,
            "denial_reason": self.denial_reason,
            "denial_code": self.denial_code,
            "appeal_date": self.appeal_date.isoformat() if self.appeal_date else None,
            "appeal_reference": self.appeal_reference,
            "authorization_number": self.authorization_number,
            "authorization_date": self.authorization_date.isoformat() if self.authorization_date else None,
            "notes": self.notes,
            "internal_notes": self.internal_notes,
            "follow_up_date": self.follow_up_date.isoformat() if self.follow_up_date else None,
            "follow_up_notes": self.follow_up_notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "created_by": self.created_by,
            "updated_by": self.updated_by,
            "cerbo_billing_id": self.cerbo_billing_id,
            "clearinghouse_id": self.clearinghouse_id,
            "is_paid_in_full": self.is_paid_in_full,
            "is_overdue": self.is_overdue,
            "payment_percentage": round(self.payment_percentage, 2),
            "days_outstanding": self.days_outstanding
        }