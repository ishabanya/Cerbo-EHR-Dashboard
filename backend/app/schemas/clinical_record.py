from pydantic import BaseModel, validator
from typing import Optional, List
from datetime import datetime, date
from enum import Enum
from decimal import Decimal

from .common import BaseSchema

class RecordTypeEnum(str, Enum):
    CLINICAL_NOTE = "clinical_note"
    VITAL_SIGNS = "vital_signs"
    LAB_RESULT = "lab_result"
    IMAGING_RESULT = "imaging_result"
    DIAGNOSIS = "diagnosis"
    PRESCRIPTION = "prescription"
    PROCEDURE_NOTE = "procedure_note"
    PROGRESS_NOTE = "progress_note"
    DISCHARGE_SUMMARY = "discharge_summary"
    ALLERGY = "allergy"
    IMMUNIZATION = "immunization"

class SeverityEnum(str, Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    SEVERE = "severe"
    CRITICAL = "critical"

class StatusEnum(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    RESOLVED = "resolved"
    CHRONIC = "chronic"
    PENDING = "pending"

class ClinicalRecordBase(BaseSchema):
    """Base clinical record schema with common fields"""
    patient_id: int
    provider_id: int
    appointment_id: Optional[int] = None
    record_type: RecordTypeEnum
    record_date: datetime
    title: str
    description: Optional[str] = None
    clinical_notes: Optional[str] = None
    
    # Vital Signs (when applicable)
    temperature: Optional[float] = None  # Fahrenheit
    blood_pressure_systolic: Optional[int] = None
    blood_pressure_diastolic: Optional[int] = None
    heart_rate: Optional[int] = None  # bpm
    respiratory_rate: Optional[int] = None  # breaths per minute
    oxygen_saturation: Optional[float] = None  # percentage
    weight: Optional[float] = None  # pounds
    height: Optional[float] = None  # inches
    bmi: Optional[float] = None
    pain_scale: Optional[int] = None  # 1-10
    
    # Lab Results (when applicable)
    lab_test_name: Optional[str] = None
    lab_result_value: Optional[str] = None
    lab_result_unit: Optional[str] = None
    lab_reference_range: Optional[str] = None
    lab_abnormal_flag: bool = False
    
    # Diagnosis Information (when applicable)
    icd_10_code: Optional[str] = None
    diagnosis_description: Optional[str] = None
    diagnosis_status: Optional[StatusEnum] = None
    diagnosis_severity: Optional[SeverityEnum] = None
    onset_date: Optional[datetime] = None
    resolution_date: Optional[datetime] = None
    
    # Prescription Information (when applicable)
    medication_name: Optional[str] = None
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    duration: Optional[str] = None
    prescribing_instructions: Optional[str] = None
    
    # Procedure Information (when applicable)
    cpt_code: Optional[str] = None
    procedure_description: Optional[str] = None
    procedure_outcome: Optional[str] = None
    
    # Allergy Information (when applicable)
    allergen: Optional[str] = None
    allergy_type: Optional[str] = None  # food, drug, environmental
    allergy_severity: Optional[SeverityEnum] = None
    allergy_reaction: Optional[str] = None
    
    # Immunization Information (when applicable)
    vaccine_name: Optional[str] = None
    vaccine_manufacturer: Optional[str] = None
    lot_number: Optional[str] = None
    vaccination_site: Optional[str] = None
    next_due_date: Optional[datetime] = None
    
    # Additional structured data
    additional_data: Optional[dict] = None
    
    # File attachments
    attachments: Optional[List[str]] = None  # List of file references
    
    # Status and Metadata
    is_confidential: bool = False
    status: StatusEnum = StatusEnum.ACTIVE
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None

    @validator('pain_scale')
    def validate_pain_scale(cls, v):
        if v is not None and (v < 1 or v > 10):
            raise ValueError('Pain scale must be between 1 and 10')
        return v

    @validator('temperature')
    def validate_temperature(cls, v):
        if v is not None and (v < 90 or v > 115):
            raise ValueError('Temperature must be between 90 and 115 degrees Fahrenheit')
        return v

    @validator('blood_pressure_systolic', 'blood_pressure_diastolic')
    def validate_blood_pressure(cls, v):
        if v is not None and (v < 50 or v > 300):
            raise ValueError('Blood pressure must be between 50 and 300 mmHg')
        return v

    @validator('heart_rate')
    def validate_heart_rate(cls, v):
        if v is not None and (v < 30 or v > 250):
            raise ValueError('Heart rate must be between 30 and 250 bpm')
        return v

    @validator('respiratory_rate')
    def validate_respiratory_rate(cls, v):
        if v is not None and (v < 5 or v > 60):
            raise ValueError('Respiratory rate must be between 5 and 60 breaths per minute')
        return v

    @validator('oxygen_saturation')
    def validate_oxygen_saturation(cls, v):
        if v is not None and (v < 50 or v > 100):
            raise ValueError('Oxygen saturation must be between 50 and 100 percent')
        return v

class ClinicalRecordCreate(ClinicalRecordBase):
    """Schema for creating a clinical record"""
    pass

class ClinicalRecordUpdate(BaseSchema):
    """Schema for updating a clinical record (all fields optional)"""
    patient_id: Optional[int] = None
    provider_id: Optional[int] = None
    appointment_id: Optional[int] = None
    record_type: Optional[RecordTypeEnum] = None
    record_date: Optional[datetime] = None
    title: Optional[str] = None
    description: Optional[str] = None
    clinical_notes: Optional[str] = None
    
    # Vital Signs
    temperature: Optional[float] = None
    blood_pressure_systolic: Optional[int] = None
    blood_pressure_diastolic: Optional[int] = None
    heart_rate: Optional[int] = None
    respiratory_rate: Optional[int] = None
    oxygen_saturation: Optional[float] = None
    weight: Optional[float] = None
    height: Optional[float] = None
    bmi: Optional[float] = None
    pain_scale: Optional[int] = None
    
    # Lab Results
    lab_test_name: Optional[str] = None
    lab_result_value: Optional[str] = None
    lab_result_unit: Optional[str] = None
    lab_reference_range: Optional[str] = None
    lab_abnormal_flag: Optional[bool] = None
    
    # Diagnosis Information
    icd_10_code: Optional[str] = None
    diagnosis_description: Optional[str] = None
    diagnosis_status: Optional[StatusEnum] = None
    diagnosis_severity: Optional[SeverityEnum] = None
    onset_date: Optional[datetime] = None
    resolution_date: Optional[datetime] = None
    
    # Prescription Information
    medication_name: Optional[str] = None
    dosage: Optional[str] = None
    frequency: Optional[str] = None
    duration: Optional[str] = None
    prescribing_instructions: Optional[str] = None
    
    # Procedure Information
    cpt_code: Optional[str] = None
    procedure_description: Optional[str] = None
    procedure_outcome: Optional[str] = None
    
    # Allergy Information
    allergen: Optional[str] = None
    allergy_type: Optional[str] = None
    allergy_severity: Optional[SeverityEnum] = None
    allergy_reaction: Optional[str] = None
    
    # Immunization Information
    vaccine_name: Optional[str] = None
    vaccine_manufacturer: Optional[str] = None
    lot_number: Optional[str] = None
    vaccination_site: Optional[str] = None
    next_due_date: Optional[datetime] = None
    
    # Additional structured data
    additional_data: Optional[dict] = None
    
    # File attachments
    attachments: Optional[List[str]] = None
    
    # Status and Metadata
    is_confidential: Optional[bool] = None
    status: Optional[StatusEnum] = None
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None

class ClinicalRecordResponse(ClinicalRecordBase):
    """Schema for clinical record response"""
    id: int
    blood_pressure: Optional[str] = None  # Combined systolic/diastolic
    is_vital_signs: bool
    is_lab_result: bool
    is_diagnosis: bool
    is_prescription: bool
    is_allergy: bool
    created_at: datetime
    updated_at: datetime
    cerbo_record_id: Optional[str] = None

class ClinicalRecordSummary(BaseSchema):
    """Schema for clinical record summary"""
    id: int
    record_type: RecordTypeEnum
    record_date: datetime
    title: str
    status: StatusEnum
    diagnosis_description: Optional[str] = None
    medication_name: Optional[str] = None
    lab_test_name: Optional[str] = None
    is_confidential: bool

class ClinicalRecordSearch(BaseSchema):
    """Schema for clinical record search parameters"""
    patient_id: Optional[int] = None
    provider_id: Optional[int] = None
    record_type: Optional[RecordTypeEnum] = None
    status: Optional[StatusEnum] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    icd_10_code: Optional[str] = None
    cpt_code: Optional[str] = None
    medication_name: Optional[str] = None
    is_confidential: Optional[bool] = None
    search_term: Optional[str] = None
    page: int = 1
    per_page: int = 50
    sort_by: str = "record_date"
    sort_order: str = "desc"

    @validator('per_page')
    def validate_per_page(cls, v):
        if v < 1 or v > 100:
            raise ValueError('per_page must be between 1 and 100')
        return v

class VitalSignsCreate(BaseSchema):
    """Specialized schema for creating vital signs records"""
    patient_id: int
    provider_id: int
    appointment_id: Optional[int] = None
    record_date: datetime = None
    temperature: Optional[float] = None
    blood_pressure_systolic: Optional[int] = None
    blood_pressure_diastolic: Optional[int] = None
    heart_rate: Optional[int] = None
    respiratory_rate: Optional[int] = None
    oxygen_saturation: Optional[float] = None
    weight: Optional[float] = None
    height: Optional[float] = None
    pain_scale: Optional[int] = None
    notes: Optional[str] = None

    def __init__(self, **data):
        if 'record_date' not in data or data['record_date'] is None:
            data['record_date'] = datetime.utcnow()
        super().__init__(**data)

class DiagnosisCreate(BaseSchema):
    """Specialized schema for creating diagnosis records"""
    patient_id: int
    provider_id: int
    appointment_id: Optional[int] = None
    record_date: datetime = None
    icd_10_code: str
    diagnosis_description: str
    diagnosis_status: StatusEnum = StatusEnum.ACTIVE
    diagnosis_severity: Optional[SeverityEnum] = None
    onset_date: Optional[datetime] = None
    clinical_notes: Optional[str] = None

    def __init__(self, **data):
        if 'record_date' not in data or data['record_date'] is None:
            data['record_date'] = datetime.utcnow()
        super().__init__(**data)

class PrescriptionCreate(BaseSchema):
    """Specialized schema for creating prescription records"""
    patient_id: int
    provider_id: int
    appointment_id: Optional[int] = None
    record_date: datetime = None
    medication_name: str
    dosage: str
    frequency: str
    duration: Optional[str] = None
    prescribing_instructions: Optional[str] = None
    clinical_notes: Optional[str] = None

    def __init__(self, **data):
        if 'record_date' not in data or data['record_date'] is None:
            data['record_date'] = datetime.utcnow()
        super().__init__(**data)