from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, Enum, ForeignKey, Numeric, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from .base import Base

class RecordTypeEnum(str, enum.Enum):
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

class SeverityEnum(str, enum.Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    SEVERE = "severe"
    CRITICAL = "critical"

class StatusEnum(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    RESOLVED = "resolved"
    CHRONIC = "chronic"
    PENDING = "pending"

class ClinicalRecord(Base):
    __tablename__ = "clinical_records"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign Keys
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    provider_id = Column(Integer, ForeignKey("providers.id"), nullable=False, index=True)
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=True, index=True)
    
    # Record Classification
    record_type = Column(Enum(RecordTypeEnum), nullable=False, index=True)
    record_date = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Clinical Content
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    clinical_notes = Column(Text, nullable=True)
    
    # Vital Signs (when applicable)
    temperature = Column(Numeric(4, 1), nullable=True)  # Fahrenheit
    blood_pressure_systolic = Column(Integer, nullable=True)
    blood_pressure_diastolic = Column(Integer, nullable=True)
    heart_rate = Column(Integer, nullable=True)  # bpm
    respiratory_rate = Column(Integer, nullable=True)  # breaths per minute
    oxygen_saturation = Column(Numeric(5, 2), nullable=True)  # percentage
    weight = Column(Numeric(5, 2), nullable=True)  # pounds
    height = Column(Numeric(5, 2), nullable=True)  # inches
    bmi = Column(Numeric(4, 1), nullable=True)
    pain_scale = Column(Integer, nullable=True)  # 1-10
    
    # Lab Results (when applicable)
    lab_test_name = Column(String(200), nullable=True)
    lab_result_value = Column(String(100), nullable=True)
    lab_result_unit = Column(String(50), nullable=True)
    lab_reference_range = Column(String(100), nullable=True)
    lab_abnormal_flag = Column(Boolean, default=False)
    
    # Diagnosis Information (when applicable)
    icd_10_code = Column(String(10), nullable=True, index=True)
    diagnosis_description = Column(Text, nullable=True)
    diagnosis_status = Column(Enum(StatusEnum), nullable=True)
    diagnosis_severity = Column(Enum(SeverityEnum), nullable=True)
    onset_date = Column(DateTime, nullable=True)
    resolution_date = Column(DateTime, nullable=True)
    
    # Prescription Information (when applicable)
    medication_name = Column(String(200), nullable=True)
    dosage = Column(String(100), nullable=True)
    frequency = Column(String(100), nullable=True)
    duration = Column(String(100), nullable=True)
    prescribing_instructions = Column(Text, nullable=True)
    
    # Procedure Information (when applicable)
    cpt_code = Column(String(10), nullable=True, index=True)
    procedure_description = Column(Text, nullable=True)
    procedure_outcome = Column(Text, nullable=True)
    
    # Allergy Information (when applicable)
    allergen = Column(String(200), nullable=True)
    allergy_type = Column(String(100), nullable=True)  # food, drug, environmental
    allergy_severity = Column(Enum(SeverityEnum), nullable=True)
    allergy_reaction = Column(Text, nullable=True)
    
    # Immunization Information (when applicable)
    vaccine_name = Column(String(200), nullable=True)
    vaccine_manufacturer = Column(String(100), nullable=True)
    lot_number = Column(String(50), nullable=True)
    vaccination_site = Column(String(100), nullable=True)
    next_due_date = Column(DateTime, nullable=True)
    
    # Additional structured data
    additional_data = Column(JSON, nullable=True)
    
    # File attachments
    attachments = Column(JSON, nullable=True)  # List of file references
    
    # Status and Metadata
    is_confidential = Column(Boolean, default=False)
    status = Column(Enum(StatusEnum), default=StatusEnum.ACTIVE, nullable=False)
    reviewed_by = Column(String(100), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # External System IDs
    cerbo_record_id = Column(String(100), nullable=True, unique=True, index=True)
    
    # Relationships
    patient = relationship("Patient", back_populates="clinical_records")
    provider = relationship("Provider", back_populates="clinical_records")
    appointment = relationship("Appointment", back_populates="clinical_records")
    
    def __repr__(self):
        return f"<ClinicalRecord(id={self.id}, patient_id={self.patient_id}, type='{self.record_type}', date='{self.record_date}')>"
    
    @property
    def blood_pressure(self) -> str:
        if self.blood_pressure_systolic and self.blood_pressure_diastolic:
            return f"{self.blood_pressure_systolic}/{self.blood_pressure_diastolic}"
        return None
    
    @property
    def is_vital_signs(self) -> bool:
        return self.record_type == RecordTypeEnum.VITAL_SIGNS
    
    @property
    def is_lab_result(self) -> bool:
        return self.record_type == RecordTypeEnum.LAB_RESULT
    
    @property
    def is_diagnosis(self) -> bool:
        return self.record_type == RecordTypeEnum.DIAGNOSIS
    
    @property
    def is_prescription(self) -> bool:
        return self.record_type == RecordTypeEnum.PRESCRIPTION
    
    @property
    def is_allergy(self) -> bool:
        return self.record_type == RecordTypeEnum.ALLERGY
    
    def calculate_bmi(self) -> float:
        if self.weight and self.height:
            # BMI = (weight in kg) / (height in meters)^2
            # Convert pounds to kg and inches to meters
            weight_kg = float(self.weight) * 0.453592
            height_m = float(self.height) * 0.0254
            bmi = weight_kg / (height_m ** 2)
            return round(bmi, 1)
        return None
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "patient_id": self.patient_id,
            "provider_id": self.provider_id,
            "appointment_id": self.appointment_id,
            "record_type": self.record_type.value if self.record_type else None,
            "record_date": self.record_date.isoformat() if self.record_date else None,
            "title": self.title,
            "description": self.description,
            "clinical_notes": self.clinical_notes,
            
            # Vital Signs
            "temperature": float(self.temperature) if self.temperature else None,
            "blood_pressure_systolic": self.blood_pressure_systolic,
            "blood_pressure_diastolic": self.blood_pressure_diastolic,
            "blood_pressure": self.blood_pressure,
            "heart_rate": self.heart_rate,
            "respiratory_rate": self.respiratory_rate,
            "oxygen_saturation": float(self.oxygen_saturation) if self.oxygen_saturation else None,
            "weight": float(self.weight) if self.weight else None,
            "height": float(self.height) if self.height else None,
            "bmi": float(self.bmi) if self.bmi else self.calculate_bmi(),
            "pain_scale": self.pain_scale,
            
            # Lab Results
            "lab_test_name": self.lab_test_name,
            "lab_result_value": self.lab_result_value,
            "lab_result_unit": self.lab_result_unit,
            "lab_reference_range": self.lab_reference_range,
            "lab_abnormal_flag": self.lab_abnormal_flag,
            
            # Diagnosis
            "icd_10_code": self.icd_10_code,
            "diagnosis_description": self.diagnosis_description,
            "diagnosis_status": self.diagnosis_status.value if self.diagnosis_status else None,
            "diagnosis_severity": self.diagnosis_severity.value if self.diagnosis_severity else None,
            "onset_date": self.onset_date.isoformat() if self.onset_date else None,
            "resolution_date": self.resolution_date.isoformat() if self.resolution_date else None,
            
            # Prescription
            "medication_name": self.medication_name,
            "dosage": self.dosage,
            "frequency": self.frequency,
            "duration": self.duration,
            "prescribing_instructions": self.prescribing_instructions,
            
            # Procedure
            "cpt_code": self.cpt_code,
            "procedure_description": self.procedure_description,
            "procedure_outcome": self.procedure_outcome,
            
            # Allergy
            "allergen": self.allergen,
            "allergy_type": self.allergy_type,
            "allergy_severity": self.allergy_severity.value if self.allergy_severity else None,
            "allergy_reaction": self.allergy_reaction,
            
            # Immunization
            "vaccine_name": self.vaccine_name,
            "vaccine_manufacturer": self.vaccine_manufacturer,
            "lot_number": self.lot_number,
            "vaccination_site": self.vaccination_site,
            "next_due_date": self.next_due_date.isoformat() if self.next_due_date else None,
            
            # Additional data
            "additional_data": self.additional_data,
            "attachments": self.attachments,
            
            # Status
            "is_confidential": self.is_confidential,
            "status": self.status.value if self.status else None,
            "reviewed_by": self.reviewed_by,
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
            
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "cerbo_record_id": self.cerbo_record_id,
            
            # Type indicators
            "is_vital_signs": self.is_vital_signs,
            "is_lab_result": self.is_lab_result,
            "is_diagnosis": self.is_diagnosis,
            "is_prescription": self.is_prescription,
            "is_allergy": self.is_allergy
        }