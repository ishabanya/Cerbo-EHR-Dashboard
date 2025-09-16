from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List
from datetime import datetime, date
from enum import Enum

from .common import BaseSchema

class ProviderTypeEnum(str, Enum):
    PHYSICIAN = "physician"
    NURSE_PRACTITIONER = "nurse_practitioner"
    PHYSICIAN_ASSISTANT = "physician_assistant"
    NURSE = "nurse"
    THERAPIST = "therapist"
    TECHNICIAN = "technician"
    SPECIALIST = "specialist"
    CONSULTANT = "consultant"

class ProviderStatusEnum(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ON_LEAVE = "on_leave"
    RETIRED = "retired"

class ProviderBase(BaseSchema):
    """Base provider schema"""
    first_name: str
    middle_name: Optional[str] = None
    last_name: str
    title: Optional[str] = None
    provider_type: ProviderTypeEnum
    license_number: Optional[str] = None
    npi_number: Optional[str] = None
    dea_number: Optional[str] = None
    specialties: Optional[List[str]] = None
    board_certifications: Optional[List[str]] = None
    languages_spoken: List[str] = ["English"]
    email: Optional[EmailStr] = None
    phone_primary: Optional[str] = None
    phone_secondary: Optional[str] = None
    office_address_line_1: Optional[str] = None
    office_address_line_2: Optional[str] = None
    office_city: Optional[str] = None
    office_state: Optional[str] = None
    office_zip_code: Optional[str] = None
    office_phone: Optional[str] = None
    default_appointment_duration: int = 30
    department: Optional[str] = None
    is_accepting_new_patients: bool = True
    bio: Optional[str] = None
    notes: Optional[str] = None

    @validator('npi_number')
    def validate_npi(cls, v):
        if v and len(v) != 10:
            raise ValueError('NPI number must be exactly 10 digits')
        return v

class ProviderCreate(ProviderBase):
    """Schema for creating a provider"""
    pass

class ProviderUpdate(BaseSchema):
    """Schema for updating a provider"""
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    last_name: Optional[str] = None
    title: Optional[str] = None
    provider_type: Optional[ProviderTypeEnum] = None
    license_number: Optional[str] = None
    npi_number: Optional[str] = None
    dea_number: Optional[str] = None
    specialties: Optional[List[str]] = None
    board_certifications: Optional[List[str]] = None
    languages_spoken: Optional[List[str]] = None
    email: Optional[EmailStr] = None
    phone_primary: Optional[str] = None
    phone_secondary: Optional[str] = None
    office_address_line_1: Optional[str] = None
    office_address_line_2: Optional[str] = None
    office_city: Optional[str] = None
    office_state: Optional[str] = None
    office_zip_code: Optional[str] = None
    office_phone: Optional[str] = None
    default_appointment_duration: Optional[int] = None
    department: Optional[str] = None
    status: Optional[ProviderStatusEnum] = None
    is_accepting_new_patients: Optional[bool] = None
    bio: Optional[str] = None
    notes: Optional[str] = None

class ProviderResponse(ProviderBase):
    """Schema for provider response"""
    id: int
    full_name: str
    display_name: str
    primary_specialty: str
    status: ProviderStatusEnum
    employee_id: Optional[str] = None
    hire_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    cerbo_provider_id: Optional[str] = None

class ProviderSearch(BaseSchema):
    """Schema for provider search parameters"""
    search_term: Optional[str] = None
    provider_type: Optional[ProviderTypeEnum] = None
    specialty: Optional[str] = None
    status: Optional[ProviderStatusEnum] = None
    is_accepting_new_patients: Optional[bool] = None
    department: Optional[str] = None
    page: int = 1
    per_page: int = 50
    sort_by: str = "last_name"
    sort_order: str = "asc"