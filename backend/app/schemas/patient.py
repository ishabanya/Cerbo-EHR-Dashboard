from pydantic import BaseModel, EmailStr, validator
from typing import Optional
from datetime import date, datetime
from enum import Enum

from .common import BaseSchema

class GenderEnum(str, Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    UNKNOWN = "unknown"

class MaritalStatusEnum(str, Enum):
    SINGLE = "single"
    MARRIED = "married"
    DIVORCED = "divorced"
    WIDOWED = "widowed"
    SEPARATED = "separated"
    UNKNOWN = "unknown"

class PatientBase(BaseSchema):
    """Base patient schema with common fields"""
    first_name: str
    middle_name: Optional[str] = None
    last_name: str
    date_of_birth: date
    gender: GenderEnum
    email: Optional[EmailStr] = None
    phone_primary: Optional[str] = None
    phone_secondary: Optional[str] = None
    address_line_1: Optional[str] = None
    address_line_2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    country: str = "United States"
    marital_status: MaritalStatusEnum = MaritalStatusEnum.UNKNOWN
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_relationship: Optional[str] = None
    medical_record_number: Optional[str] = None
    primary_language: str = "English"
    notes: Optional[str] = None

    @validator('phone_primary', 'phone_secondary', 'emergency_contact_phone')
    def validate_phone(cls, v):
        if v and len(v) > 0:
            # Remove non-digit characters
            digits = ''.join(filter(str.isdigit, v))
            if len(digits) != 10:
                raise ValueError('Phone number must contain exactly 10 digits')
        return v

    @validator('zip_code')
    def validate_zip_code(cls, v):
        if v and len(v) > 0:
            # US zip code validation (5 or 9 digits)
            digits = ''.join(filter(str.isdigit, v))
            if len(digits) not in [5, 9]:
                raise ValueError('Zip code must be 5 or 9 digits')
        return v

class PatientCreate(PatientBase):
    """Schema for creating a patient"""
    pass

class PatientUpdate(BaseSchema):
    """Schema for updating a patient (all fields optional)"""
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[GenderEnum] = None
    email: Optional[EmailStr] = None
    phone_primary: Optional[str] = None
    phone_secondary: Optional[str] = None
    address_line_1: Optional[str] = None
    address_line_2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    country: Optional[str] = None
    marital_status: Optional[MaritalStatusEnum] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    emergency_contact_relationship: Optional[str] = None
    medical_record_number: Optional[str] = None
    primary_language: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None

class PatientResponse(PatientBase):
    """Schema for patient response"""
    id: int
    full_name: str
    age: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    cerbo_patient_id: Optional[str] = None

class PatientSummary(BaseSchema):
    """Schema for patient summary with related data counts"""
    id: int
    full_name: str
    age: int
    gender: GenderEnum
    phone_primary: Optional[str] = None
    email: Optional[EmailStr] = None
    last_appointment: Optional[datetime] = None
    appointment_count: int = 0
    clinical_record_count: int = 0
    is_active: bool

class PatientSearch(BaseSchema):
    """Schema for patient search parameters"""
    search_term: Optional[str] = None
    search_type: str = "all"  # all, name, phone, email, mrn, dob
    min_age: Optional[int] = None
    max_age: Optional[int] = None
    gender: Optional[GenderEnum] = None
    state: Optional[str] = None
    is_active: Optional[bool] = True
    page: int = 1
    per_page: int = 50
    sort_by: str = "last_name"
    sort_order: str = "asc"

    @validator('search_type')
    def validate_search_type(cls, v):
        valid_types = ["all", "name", "phone", "email", "mrn", "dob"]
        if v not in valid_types:
            raise ValueError(f'search_type must be one of: {valid_types}')
        return v

    @validator('min_age', 'max_age')
    def validate_age(cls, v):
        if v is not None and (v < 0 or v > 150):
            raise ValueError('Age must be between 0 and 150')
        return v

    @validator('per_page')
    def validate_per_page(cls, v):
        if v < 1 or v > 100:
            raise ValueError('per_page must be between 1 and 100')
        return v