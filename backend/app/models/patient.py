from sqlalchemy import Column, Integer, String, DateTime, Date, Text, Boolean, Enum
from sqlalchemy.orm import relationship
from datetime import datetime, date
from typing import Optional, List
import enum

from .base import Base

class GenderEnum(str, enum.Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    UNKNOWN = "unknown"

class MaritalStatusEnum(str, enum.Enum):
    SINGLE = "single"
    MARRIED = "married"
    DIVORCED = "divorced"
    WIDOWED = "widowed"
    SEPARATED = "separated"
    UNKNOWN = "unknown"

class Patient(Base):
    __tablename__ = "patients"
    
    id = Column(Integer, primary_key=True, index=True)
    
    first_name = Column(String(100), nullable=False, index=True)
    middle_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=False, index=True)
    date_of_birth = Column(Date, nullable=False, index=True)
    gender = Column(Enum(GenderEnum), nullable=False)
    
    email = Column(String(255), nullable=True, index=True)
    phone_primary = Column(String(20), nullable=True, index=True)
    phone_secondary = Column(String(20), nullable=True)
    
    address_line_1 = Column(String(255), nullable=True)
    address_line_2 = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(50), nullable=True)
    zip_code = Column(String(10), nullable=True)
    country = Column(String(100), default="United States")
    
    marital_status = Column(Enum(MaritalStatusEnum), default=MaritalStatusEnum.UNKNOWN)
    social_security_number = Column(String(11), nullable=True)
    
    emergency_contact_name = Column(String(200), nullable=True)
    emergency_contact_phone = Column(String(20), nullable=True)
    emergency_contact_relationship = Column(String(100), nullable=True)
    
    medical_record_number = Column(String(50), unique=True, nullable=True, index=True)
    primary_language = Column(String(50), default="English")
    
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    notes = Column(Text, nullable=True)
    
    cerbo_patient_id = Column(String(100), nullable=True, unique=True, index=True)
    
    appointments = relationship("Appointment", back_populates="patient", cascade="all, delete-orphan")
    clinical_records = relationship("ClinicalRecord", back_populates="patient", cascade="all, delete-orphan")
    insurance_records = relationship("Insurance", back_populates="patient", cascade="all, delete-orphan")
    billing_records = relationship("Billing", back_populates="patient", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Patient(id={self.id}, name='{self.first_name} {self.last_name}', dob='{self.date_of_birth}')>"
    
    @property
    def full_name(self) -> str:
        if self.middle_name:
            return f"{self.first_name} {self.middle_name} {self.last_name}"
        return f"{self.first_name} {self.last_name}"
    
    @property
    def age(self) -> int:
        today = date.today()
        return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "first_name": self.first_name,
            "middle_name": self.middle_name,
            "last_name": self.last_name,
            "full_name": self.full_name,
            "date_of_birth": self.date_of_birth.isoformat() if self.date_of_birth else None,
            "age": self.age,
            "gender": self.gender.value if self.gender else None,
            "email": self.email,
            "phone_primary": self.phone_primary,
            "phone_secondary": self.phone_secondary,
            "address_line_1": self.address_line_1,
            "address_line_2": self.address_line_2,
            "city": self.city,
            "state": self.state,
            "zip_code": self.zip_code,
            "country": self.country,
            "marital_status": self.marital_status.value if self.marital_status else None,
            "emergency_contact_name": self.emergency_contact_name,
            "emergency_contact_phone": self.emergency_contact_phone,
            "emergency_contact_relationship": self.emergency_contact_relationship,
            "medical_record_number": self.medical_record_number,
            "primary_language": self.primary_language,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "notes": self.notes,
            "cerbo_patient_id": self.cerbo_patient_id
        }