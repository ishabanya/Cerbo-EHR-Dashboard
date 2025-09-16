from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, Enum, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from .base import Base

class ProviderTypeEnum(str, enum.Enum):
    PHYSICIAN = "physician"
    NURSE_PRACTITIONER = "nurse_practitioner"
    PHYSICIAN_ASSISTANT = "physician_assistant"
    NURSE = "nurse"
    THERAPIST = "therapist"
    TECHNICIAN = "technician"
    SPECIALIST = "specialist"
    CONSULTANT = "consultant"

class ProviderStatusEnum(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ON_LEAVE = "on_leave"
    RETIRED = "retired"

class Provider(Base):
    __tablename__ = "providers"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Personal Information
    first_name = Column(String(100), nullable=False, index=True)
    middle_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=False, index=True)
    title = Column(String(50), nullable=True)  # Dr., NP, PA, etc.
    
    # Professional Information
    provider_type = Column(Enum(ProviderTypeEnum), nullable=False)
    license_number = Column(String(100), nullable=True, index=True)
    npi_number = Column(String(10), nullable=True, unique=True, index=True)  # National Provider Identifier
    dea_number = Column(String(20), nullable=True)  # Drug Enforcement Administration
    
    # Specialties and Certifications
    specialties = Column(JSON, nullable=True)  # List of specialties
    board_certifications = Column(JSON, nullable=True)  # List of certifications
    languages_spoken = Column(JSON, default=["English"], nullable=False)
    
    # Contact Information
    email = Column(String(255), nullable=True, index=True)
    phone_primary = Column(String(20), nullable=True)
    phone_secondary = Column(String(20), nullable=True)
    
    # Office Information
    office_address_line_1 = Column(String(255), nullable=True)
    office_address_line_2 = Column(String(255), nullable=True)
    office_city = Column(String(100), nullable=True)
    office_state = Column(String(50), nullable=True)
    office_zip_code = Column(String(10), nullable=True)
    office_phone = Column(String(20), nullable=True)
    
    # Schedule and Availability
    default_appointment_duration = Column(Integer, default=30, nullable=False)  # minutes
    working_hours = Column(JSON, nullable=True)  # Weekly schedule
    availability_exceptions = Column(JSON, nullable=True)  # Holidays, vacations, etc.
    
    # Administrative
    employee_id = Column(String(50), nullable=True, unique=True, index=True)
    department = Column(String(100), nullable=True)
    hire_date = Column(DateTime, nullable=True)
    
    # Status and Metadata
    status = Column(Enum(ProviderStatusEnum), default=ProviderStatusEnum.ACTIVE, nullable=False, index=True)
    is_accepting_new_patients = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Notes and Bio
    bio = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    
    # External System IDs
    cerbo_provider_id = Column(String(100), nullable=True, unique=True, index=True)
    
    # Relationships
    appointments = relationship("Appointment", back_populates="provider", cascade="all, delete-orphan")
    clinical_records = relationship("ClinicalRecord", back_populates="provider", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Provider(id={self.id}, name='{self.title} {self.first_name} {self.last_name}', type='{self.provider_type}')>"
    
    @property
    def full_name(self) -> str:
        name_parts = []
        if self.title:
            name_parts.append(self.title)
        name_parts.append(self.first_name)
        if self.middle_name:
            name_parts.append(self.middle_name)
        name_parts.append(self.last_name)
        return " ".join(name_parts)
    
    @property
    def display_name(self) -> str:
        if self.title:
            return f"{self.title} {self.last_name}"
        return self.full_name
    
    @property
    def primary_specialty(self) -> str:
        if self.specialties and len(self.specialties) > 0:
            return self.specialties[0]
        return self.provider_type.value.replace("_", " ").title()
    
    def is_available_for_appointment(self, appointment_datetime: datetime, duration_minutes: int = None) -> bool:
        if self.status != ProviderStatusEnum.ACTIVE:
            return False
        
        duration = duration_minutes or self.default_appointment_duration
        # This would contain complex logic to check working hours and existing appointments
        # For now, return True if active
        return True
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "first_name": self.first_name,
            "middle_name": self.middle_name,
            "last_name": self.last_name,
            "title": self.title,
            "full_name": self.full_name,
            "display_name": self.display_name,
            "provider_type": self.provider_type.value if self.provider_type else None,
            "license_number": self.license_number,
            "npi_number": self.npi_number,
            "dea_number": self.dea_number,
            "specialties": self.specialties,
            "primary_specialty": self.primary_specialty,
            "board_certifications": self.board_certifications,
            "languages_spoken": self.languages_spoken,
            "email": self.email,
            "phone_primary": self.phone_primary,
            "phone_secondary": self.phone_secondary,
            "office_address_line_1": self.office_address_line_1,
            "office_address_line_2": self.office_address_line_2,
            "office_city": self.office_city,
            "office_state": self.office_state,
            "office_zip_code": self.office_zip_code,
            "office_phone": self.office_phone,
            "default_appointment_duration": self.default_appointment_duration,
            "working_hours": self.working_hours,
            "availability_exceptions": self.availability_exceptions,
            "employee_id": self.employee_id,
            "department": self.department,
            "hire_date": self.hire_date.isoformat() if self.hire_date else None,
            "status": self.status.value if self.status else None,
            "is_accepting_new_patients": self.is_accepting_new_patients,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "bio": self.bio,
            "notes": self.notes,
            "cerbo_provider_id": self.cerbo_provider_id
        }