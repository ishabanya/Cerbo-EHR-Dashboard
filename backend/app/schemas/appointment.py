from pydantic import BaseModel, validator
from typing import Optional
from datetime import datetime
from enum import Enum

from .common import BaseSchema

class AppointmentStatusEnum(str, Enum):
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    CHECKED_IN = "checked_in"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"
    RESCHEDULED = "rescheduled"

class AppointmentTypeEnum(str, Enum):
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

class UrgencyEnum(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class AppointmentBase(BaseSchema):
    """Base appointment schema"""
    patient_id: int
    provider_id: int
    appointment_date: datetime
    duration_minutes: int = 30
    appointment_type: AppointmentTypeEnum
    status: AppointmentStatusEnum = AppointmentStatusEnum.SCHEDULED
    urgency: UrgencyEnum = UrgencyEnum.MEDIUM
    chief_complaint: Optional[str] = None
    reason_for_visit: Optional[str] = None
    notes: Optional[str] = None
    room_number: Optional[str] = None
    location: Optional[str] = None
    is_telehealth: bool = False
    telehealth_link: Optional[str] = None
    estimated_cost: Optional[float] = None
    copay_amount: Optional[float] = None

    @validator('duration_minutes')
    def validate_duration(cls, v):
        if v < 15 or v > 480:  # 15 minutes to 8 hours
            raise ValueError('Duration must be between 15 and 480 minutes')
        return v

    @validator('appointment_date')
    def validate_future_date(cls, v):
        if v < datetime.utcnow():
            raise ValueError('Appointment date must be in the future')
        return v

class AppointmentCreate(AppointmentBase):
    """Schema for creating an appointment"""
    pass

class AppointmentUpdate(BaseSchema):
    """Schema for updating an appointment"""
    patient_id: Optional[int] = None
    provider_id: Optional[int] = None
    appointment_date: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    appointment_type: Optional[AppointmentTypeEnum] = None
    status: Optional[AppointmentStatusEnum] = None
    urgency: Optional[UrgencyEnum] = None
    chief_complaint: Optional[str] = None
    reason_for_visit: Optional[str] = None
    notes: Optional[str] = None
    room_number: Optional[str] = None
    location: Optional[str] = None
    is_telehealth: Optional[bool] = None
    telehealth_link: Optional[str] = None
    estimated_cost: Optional[float] = None
    copay_amount: Optional[float] = None
    cancellation_reason: Optional[str] = None

class AppointmentResponse(AppointmentBase):
    """Schema for appointment response"""
    id: int
    end_time: datetime
    scheduled_by: Optional[str] = None
    check_in_time: Optional[datetime] = None
    check_out_time: Optional[datetime] = None
    actual_start_time: Optional[datetime] = None
    actual_end_time: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    cancelled_at: Optional[datetime] = None
    cancellation_reason: Optional[str] = None
    cerbo_appointment_id: Optional[str] = None
    is_past: bool
    is_today: bool
    can_check_in: bool

class AppointmentSearch(BaseSchema):
    """Schema for appointment search parameters"""
    patient_id: Optional[int] = None
    provider_id: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: Optional[AppointmentStatusEnum] = None
    appointment_type: Optional[AppointmentTypeEnum] = None
    urgency: Optional[UrgencyEnum] = None
    is_telehealth: Optional[bool] = None
    room_number: Optional[str] = None
    page: int = 1
    per_page: int = 50
    sort_by: str = "appointment_date"
    sort_order: str = "asc"

class AppointmentConflictCheck(BaseSchema):
    """Schema for checking appointment conflicts"""
    provider_id: int
    appointment_date: datetime
    duration_minutes: int = 30
    exclude_appointment_id: Optional[int] = None