from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func
from datetime import date, datetime
import logging

from .base_repository import BaseRepository
from ..models.patient import Patient
from ..api.cerbo_client import CerboClient, CerboAPIException

logger = logging.getLogger(__name__)

class PatientService(BaseRepository[Patient]):
    
    def __init__(self, db: Session, cerbo_client: CerboClient = None):
        super().__init__(Patient, db)
        self.cerbo_client = cerbo_client
    
    def search_patients(
        self, 
        search_term: str, 
        search_type: str = "all",
        skip: int = 0, 
        limit: int = 100
    ) -> List[Patient]:
        try:
            if not search_term:
                return self.get_all(skip=skip, limit=limit)
            
            query = self.db.query(Patient)
            
            if search_type == "name":
                query = query.filter(
                    or_(
                        Patient.first_name.ilike(f"%{search_term}%"),
                        Patient.middle_name.ilike(f"%{search_term}%"),
                        Patient.last_name.ilike(f"%{search_term}%"),
                        func.concat(Patient.first_name, ' ', Patient.last_name).ilike(f"%{search_term}%")
                    )
                )
            elif search_type == "phone":
                clean_search = ''.join(filter(str.isdigit, search_term))
                query = query.filter(
                    or_(
                        Patient.phone_primary.contains(clean_search),
                        Patient.phone_secondary.contains(clean_search)
                    )
                )
            elif search_type == "email":
                query = query.filter(Patient.email.ilike(f"%{search_term}%"))
            elif search_type == "mrn":
                query = query.filter(Patient.medical_record_number.ilike(f"%{search_term}%"))
            elif search_type == "dob":
                try:
                    search_date = datetime.strptime(search_term, "%Y-%m-%d").date()
                    query = query.filter(Patient.date_of_birth == search_date)
                except ValueError:
                    logger.warning(f"Invalid date format for DOB search: {search_term}")
                    return []
            else:
                query = query.filter(
                    or_(
                        Patient.first_name.ilike(f"%{search_term}%"),
                        Patient.middle_name.ilike(f"%{search_term}%"),
                        Patient.last_name.ilike(f"%{search_term}%"),
                        Patient.email.ilike(f"%{search_term}%"),
                        Patient.phone_primary.contains(search_term),
                        Patient.phone_secondary.contains(search_term),
                        Patient.medical_record_number.ilike(f"%{search_term}%")
                    )
                )
            
            return query.filter(Patient.is_active == True).offset(skip).limit(limit).all()
            
        except Exception as e:
            logger.error(f"Error searching patients: {e}")
            raise
    
    def get_by_medical_record_number(self, mrn: str) -> Optional[Patient]:
        return self.get_by_field("medical_record_number", mrn)
    
    def get_by_cerbo_id(self, cerbo_id: str) -> Optional[Patient]:
        return self.get_by_field("cerbo_patient_id", cerbo_id)
    
    def get_patients_by_age_range(self, min_age: int, max_age: int) -> List[Patient]:
        try:
            today = date.today()
            max_birth_date = date(today.year - min_age, today.month, today.day)
            min_birth_date = date(today.year - max_age, today.month, today.day)
            
            return self.db.query(Patient).filter(
                and_(
                    Patient.date_of_birth >= min_birth_date,
                    Patient.date_of_birth <= max_birth_date,
                    Patient.is_active == True
                )
            ).all()
        except Exception as e:
            logger.error(f"Error getting patients by age range: {e}")
            raise
    
    def get_patients_by_provider(self, provider_id: int) -> List[Patient]:
        try:
            from ..models.appointment import Appointment
            
            return self.db.query(Patient).join(Appointment).filter(
                and_(
                    Appointment.provider_id == provider_id,
                    Patient.is_active == True
                )
            ).distinct().all()
        except Exception as e:
            logger.error(f"Error getting patients by provider: {e}")
            raise
    
    async def create_patient_with_cerbo_sync(self, patient_data: Dict[str, Any]) -> Patient:
        try:
            patient = self.create(patient_data)
            
            if self.cerbo_client:
                try:
                    cerbo_patient_data = self._convert_to_cerbo_format(patient)
                    cerbo_response = await self.cerbo_client.create_patient(cerbo_patient_data)
                    
                    if cerbo_response and 'id' in cerbo_response:
                        self.update(patient.id, {"cerbo_patient_id": cerbo_response['id']})
                        logger.info(f"Patient {patient.id} synced with CERBO ID: {cerbo_response['id']}")
                    
                except CerboAPIException as e:
                    logger.warning(f"Failed to sync patient {patient.id} with CERBO: {e}")
            
            return patient
        except Exception as e:
            logger.error(f"Error creating patient with CERBO sync: {e}")
            raise
    
    async def update_patient_with_cerbo_sync(self, patient_id: int, patient_data: Dict[str, Any]) -> Optional[Patient]:
        try:
            patient = self.update(patient_id, patient_data)
            if not patient:
                return None
            
            if self.cerbo_client and patient.cerbo_patient_id:
                try:
                    cerbo_patient_data = self._convert_to_cerbo_format(patient)
                    await self.cerbo_client.update_patient(patient.cerbo_patient_id, cerbo_patient_data)
                    logger.info(f"Patient {patient.id} updated in CERBO")
                    
                except CerboAPIException as e:
                    logger.warning(f"Failed to sync patient {patient.id} update with CERBO: {e}")
            
            return patient
        except Exception as e:
            logger.error(f"Error updating patient with CERBO sync: {e}")
            raise
    
    async def sync_from_cerbo(self, cerbo_patient_id: str) -> Optional[Patient]:
        if not self.cerbo_client:
            raise ValueError("CERBO client not available")
        
        try:
            cerbo_patient = await self.cerbo_client.get_patient(cerbo_patient_id)
            
            if not cerbo_patient:
                return None
            
            existing_patient = self.get_by_cerbo_id(cerbo_patient_id)
            
            patient_data = self._convert_from_cerbo_format(cerbo_patient)
            patient_data['cerbo_patient_id'] = cerbo_patient_id
            
            if existing_patient:
                return self.update(existing_patient.id, patient_data)
            else:
                return self.create(patient_data)
                
        except CerboAPIException as e:
            logger.error(f"Error syncing patient from CERBO: {e}")
            raise
    
    async def bulk_sync_from_cerbo(self, limit: int = 100) -> List[Patient]:
        if not self.cerbo_client:
            raise ValueError("CERBO client not available")
        
        try:
            cerbo_response = await self.cerbo_client.get_patients(limit=limit)
            
            if not cerbo_response or 'patients' not in cerbo_response:
                return []
            
            synced_patients = []
            
            for cerbo_patient in cerbo_response['patients']:
                try:
                    patient = self.sync_from_cerbo(cerbo_patient['id'])
                    if patient:
                        synced_patients.append(patient)
                except Exception as e:
                    logger.warning(f"Failed to sync patient {cerbo_patient.get('id')}: {e}")
                    continue
            
            logger.info(f"Synced {len(synced_patients)} patients from CERBO")
            return synced_patients
            
        except CerboAPIException as e:
            logger.error(f"Error bulk syncing patients from CERBO: {e}")
            raise
    
    def deactivate_patient(self, patient_id: int, reason: str = None) -> Optional[Patient]:
        try:
            update_data = {"is_active": False}
            if reason:
                current_notes = self.get_by_id(patient_id).notes or ""
                update_data["notes"] = f"{current_notes}\nDeactivated: {reason}".strip()
            
            return self.update(patient_id, update_data)
        except Exception as e:
            logger.error(f"Error deactivating patient {patient_id}: {e}")
            raise
    
    def reactivate_patient(self, patient_id: int) -> Optional[Patient]:
        try:
            return self.update(patient_id, {"is_active": True})
        except Exception as e:
            logger.error(f"Error reactivating patient {patient_id}: {e}")
            raise
    
    def get_patient_summary(self, patient_id: int) -> Dict[str, Any]:
        try:
            patient = self.get_by_id(patient_id)
            if not patient:
                return None
            
            from ..models.appointment import Appointment
            from ..models.clinical_record import ClinicalRecord
            from ..models.billing import Billing
            
            appointment_count = self.db.query(Appointment).filter(
                Appointment.patient_id == patient_id
            ).count()
            
            clinical_record_count = self.db.query(ClinicalRecord).filter(
                ClinicalRecord.patient_id == patient_id
            ).count()
            
            billing_count = self.db.query(Billing).filter(
                Billing.patient_id == patient_id
            ).count()
            
            recent_appointments = self.db.query(Appointment).filter(
                Appointment.patient_id == patient_id
            ).order_by(Appointment.appointment_date.desc()).limit(5).all()
            
            return {
                "patient": patient.to_dict(),
                "counts": {
                    "appointments": appointment_count,
                    "clinical_records": clinical_record_count,
                    "billing_records": billing_count
                },
                "recent_appointments": [apt.to_dict() for apt in recent_appointments]
            }
            
        except Exception as e:
            logger.error(f"Error getting patient summary for {patient_id}: {e}")
            raise
    
    def _convert_to_cerbo_format(self, patient: Patient) -> Dict[str, Any]:
        return {
            "first_name": patient.first_name,
            "middle_name": patient.middle_name,
            "last_name": patient.last_name,
            "date_of_birth": patient.date_of_birth.isoformat() if patient.date_of_birth else None,
            "gender": patient.gender.value if patient.gender else None,
            "email": patient.email,
            "phone": patient.phone_primary,
            "address": {
                "line1": patient.address_line_1,
                "line2": patient.address_line_2,
                "city": patient.city,
                "state": patient.state,
                "zip": patient.zip_code,
                "country": patient.country
            },
            "emergency_contact": {
                "name": patient.emergency_contact_name,
                "phone": patient.emergency_contact_phone,
                "relationship": patient.emergency_contact_relationship
            }
        }
    
    def _convert_from_cerbo_format(self, cerbo_patient: Dict[str, Any]) -> Dict[str, Any]:
        address = cerbo_patient.get('address', {})
        emergency_contact = cerbo_patient.get('emergency_contact', {})
        
        return {
            "first_name": cerbo_patient.get('first_name'),
            "middle_name": cerbo_patient.get('middle_name'),
            "last_name": cerbo_patient.get('last_name'),
            "date_of_birth": datetime.strptime(cerbo_patient['date_of_birth'], "%Y-%m-%d").date() 
                           if cerbo_patient.get('date_of_birth') else None,
            "gender": cerbo_patient.get('gender'),
            "email": cerbo_patient.get('email'),
            "phone_primary": cerbo_patient.get('phone'),
            "address_line_1": address.get('line1'),
            "address_line_2": address.get('line2'),
            "city": address.get('city'),
            "state": address.get('state'),
            "zip_code": address.get('zip'),
            "country": address.get('country', 'United States'),
            "emergency_contact_name": emergency_contact.get('name'),
            "emergency_contact_phone": emergency_contact.get('phone'),
            "emergency_contact_relationship": emergency_contact.get('relationship'),
        }