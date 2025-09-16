from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, Enum, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from .base import Base

class AppointmentStatusEnum(str, enum.Enum):
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    CHECKED_IN = "checked_in"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"
    RESCHEDULED = "rescheduled"

class AppointmentTypeEnum(str, enum.Enum):
    CONSULTATION = "consultation"
    FOLLOW_UP = "follow_up"
    PHYSICAL_EXAM = "physical_exam"
    PROCEDURE = "procedure"
    EMERGENCY = "emergency"
    TELEHEALTH = "telehealth"
    VACCINATION = "vaccination"
    LAB_WORK = "lab_work"
    IMAGING = "imaging"
    THERAPY = "therapy"

class UrgencyEnum(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class Appointment(Base):
    __tablename__ = "appointments"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign Keys
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    provider_id = Column(Integer, ForeignKey("providers.id"), nullable=False, index=True)
    
    # Appointment Details
    appointment_date = Column(DateTime, nullable=False, index=True)
    duration_minutes = Column(Integer, default=30, nullable=False)
    appointment_type = Column(Enum(AppointmentTypeEnum), nullable=False)
    status = Column(Enum(AppointmentStatusEnum), default=AppointmentStatusEnum.SCHEDULED, nullable=False, index=True)
    urgency = Column(Enum(UrgencyEnum), default=UrgencyEnum.MEDIUM, nullable=False)
    
    # Appointment Information
    chief_complaint = Column(Text, nullable=True)
    reason_for_visit = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    
    # Location and Logistics
    room_number = Column(String(20), nullable=True)
    location = Column(String(200), nullable=True)
    is_telehealth = Column(Boolean, default=False, nullable=False)
    telehealth_link = Column(String(500), nullable=True)
    
    # Scheduling Information
    scheduled_by = Column(String(100), nullable=True)  # User who scheduled
    check_in_time = Column(DateTime, nullable=True)
    check_out_time = Column(DateTime, nullable=True)
    actual_start_time = Column(DateTime, nullable=True)
    actual_end_time = Column(DateTime, nullable=True)
    
    # Billing and Insurance
    estimated_cost = Column(Numeric(10, 2), nullable=True)
    copay_amount = Column(Numeric(10, 2), nullable=True)
    
    # External References
    cerbo_appointment_id = Column(String(100), nullable=True, unique=True, index=True)
    
    # Status and Metadata
    is_recurring = Column(Boolean, default=False, nullable=False)
    recurring_pattern = Column(String(100), nullable=True)  # weekly, monthly, etc.
    parent_appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    cancelled_at = Column(DateTime, nullable=True)
    cancellation_reason = Column(Text, nullable=True)
    
    # Relationships
    patient = relationship("Patient", back_populates="appointments")
    provider = relationship("Provider", back_populates="appointments")
    clinical_records = relationship("ClinicalRecord", back_populates="appointment", cascade="all, delete-orphan")
    
    # Self-referential for recurring appointments
    child_appointments = relationship("Appointment", remote_side=[parent_appointment_id])
    
    def __repr__(self):
        return f"<Appointment(id={self.id}, patient_id={self.patient_id}, date='{self.appointment_date}', status='{self.status}')>"
    
    @property
    def end_time(self) -> datetime:
        from datetime import timedelta
        return self.appointment_date + timedelta(minutes=self.duration_minutes)
    
    @property
    def is_past(self) -> bool:
        return self.appointment_date < datetime.utcnow()
    
    @property
    def is_today(self) -> bool:
        today = datetime.utcnow().date()
        return self.appointment_date.date() == today
    
    @property
    def can_check_in(self) -> bool:
        from datetime import timedelta
        now = datetime.utcnow()
        # Allow check-in 30 minutes before appointment
        check_in_window = self.appointment_date - timedelta(minutes=30)
        return (self.status == AppointmentStatusEnum.CONFIRMED and 
                check_in_window <= now <= self.end_time)
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "patient_id": self.patient_id,
            "provider_id": self.provider_id,
            "appointment_date": self.appointment_date.isoformat() if self.appointment_date else None,
            "end_time": self.end_time.isoformat() if self.appointment_date else None,
            "duration_minutes": self.duration_minutes,
            "appointment_type": self.appointment_type.value if self.appointment_type else None,
            "status": self.status.value if self.status else None,
            "urgency": self.urgency.value if self.urgency else None,
            "chief_complaint": self.chief_complaint,
            "reason_for_visit": self.reason_for_visit,
            "notes": self.notes,
            "room_number": self.room_number,
            "location": self.location,
            "is_telehealth": self.is_telehealth,
            "telehealth_link": self.telehealth_link,
            "scheduled_by": self.scheduled_by,
            "check_in_time": self.check_in_time.isoformat() if self.check_in_time else None,
            "check_out_time": self.check_out_time.isoformat() if self.check_out_time else None,
            "actual_start_time": self.actual_start_time.isoformat() if self.actual_start_time else None,
            "actual_end_time": self.actual_end_time.isoformat() if self.actual_end_time else None,
            "estimated_cost": float(self.estimated_cost) if self.estimated_cost else None,
            "copay_amount": float(self.copay_amount) if self.copay_amount else None,
            "cerbo_appointment_id": self.cerbo_appointment_id,
            "is_recurring": self.is_recurring,
            "recurring_pattern": self.recurring_pattern,
            "parent_appointment_id": self.parent_appointment_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "cancelled_at": self.cancelled_at.isoformat() if self.cancelled_at else None,
            "cancellation_reason": self.cancellation_reason,
            "is_past": self.is_past,
            "is_today": self.is_today,
            "can_check_in": self.can_check_in
        }