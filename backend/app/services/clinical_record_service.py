from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func, desc, asc
from datetime import datetime, date, timedelta
import logging

from .base_repository import BaseRepository
from ..models.clinical_record import ClinicalRecord, RecordTypeEnum, SeverityEnum, StatusEnum
from ..models.patient import Patient
from ..models.provider import Provider
from ..models.appointment import Appointment
from ..api.cerbo_client import CerboClient, CerboAPIException

logger = logging.getLogger(__name__)

class ClinicalRecordService(BaseRepository[ClinicalRecord]):
    """
    Clinical Record service for medical records, vital signs, lab results, and CERBO API integration
    """
    
    def __init__(self, db: Session, cerbo_client: CerboClient = None):
        super().__init__(ClinicalRecord, db)
        self.cerbo_client = cerbo_client
    
    def search_clinical_records(
        self, 
        search_term: str, 
        search_type: str = "all",
        skip: int = 0, 
        limit: int = 100
    ) -> List[ClinicalRecord]:
        """
        Advanced clinical record search with multiple criteria
        """
        try:
            if not search_term:
                return self.get_all(skip=skip, limit=limit, order_by="record_date", order_direction="desc")
            
            query = self.db.query(ClinicalRecord).join(Patient).join(Provider)
            
            if search_type == "patient":
                # Search by patient name
                query = query.filter(
                    or_(
                        Patient.first_name.ilike(f"%{search_term}%"),
                        Patient.last_name.ilike(f"%{search_term}%"),
                        func.concat(Patient.first_name, ' ', Patient.last_name).ilike(f"%{search_term}%"),
                        Patient.medical_record_number.ilike(f"%{search_term}%")
                    )
                )
            elif search_type == "provider":
                # Search by provider name
                query = query.filter(
                    or_(
                        Provider.first_name.ilike(f"%{search_term}%"),
                        Provider.last_name.ilike(f"%{search_term}%"),
                        func.concat(Provider.first_name, ' ', Provider.last_name).ilike(f"%{search_term}%")
                    )
                )
            elif search_type == "diagnosis":
                # Search by diagnosis
                query = query.filter(
                    or_(
                        ClinicalRecord.icd_10_code.ilike(f"%{search_term}%"),
                        ClinicalRecord.diagnosis_description.ilike(f"%{search_term}%")
                    )
                )
            elif search_type == "medication":
                # Search by medication
                query = query.filter(ClinicalRecord.medication_name.ilike(f"%{search_term}%"))
            elif search_type == "lab":
                # Search by lab test
                query = query.filter(
                    or_(
                        ClinicalRecord.lab_test_name.ilike(f"%{search_term}%"),
                        ClinicalRecord.lab_result_value.ilike(f"%{search_term}%")
                    )
                )
            elif search_type == "procedure":
                # Search by procedure
                query = query.filter(
                    or_(
                        ClinicalRecord.cpt_code.ilike(f"%{search_term}%"),
                        ClinicalRecord.procedure_description.ilike(f"%{search_term}%")
                    )
                )
            elif search_type == "allergy":
                # Search by allergy
                query = query.filter(
                    or_(
                        ClinicalRecord.allergen.ilike(f"%{search_term}%"),
                        ClinicalRecord.allergy_reaction.ilike(f"%{search_term}%")
                    )
                )
            elif search_type == "vaccine":
                # Search by vaccine
                query = query.filter(ClinicalRecord.vaccine_name.ilike(f"%{search_term}%"))
            elif search_type == "type":
                # Search by record type
                try:
                    record_type = RecordTypeEnum(search_term.lower())
                    query = query.filter(ClinicalRecord.record_type == record_type)
                except ValueError:
                    logger.warning(f"Invalid record type for search: {search_term}")
                    return []
            else:
                # Search all text fields
                query = query.filter(
                    or_(
                        ClinicalRecord.title.ilike(f"%{search_term}%"),
                        ClinicalRecord.description.ilike(f"%{search_term}%"),
                        ClinicalRecord.clinical_notes.ilike(f"%{search_term}%"),
                        ClinicalRecord.diagnosis_description.ilike(f"%{search_term}%"),
                        ClinicalRecord.medication_name.ilike(f"%{search_term}%"),
                        ClinicalRecord.lab_test_name.ilike(f"%{search_term}%"),
                        ClinicalRecord.procedure_description.ilike(f"%{search_term}%"),
                        ClinicalRecord.allergen.ilike(f"%{search_term}%"),
                        ClinicalRecord.vaccine_name.ilike(f"%{search_term}%"),
                        ClinicalRecord.icd_10_code.ilike(f"%{search_term}%"),
                        ClinicalRecord.cpt_code.ilike(f"%{search_term}%")
                    )
                )
            
            return query.order_by(desc(ClinicalRecord.record_date)).offset(skip).limit(limit).all()
            
        except Exception as e:
            logger.error(f"Error searching clinical records: {e}")
            raise
    
    def get_records_by_patient(
        self, 
        patient_id: int, 
        record_type: RecordTypeEnum = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[ClinicalRecord]:
        """Get clinical records for a specific patient"""
        try:
            query = self.db.query(ClinicalRecord).filter(ClinicalRecord.patient_id == patient_id)
            
            if record_type:
                query = query.filter(ClinicalRecord.record_type == record_type)
            
            return query.order_by(desc(ClinicalRecord.record_date)).offset(skip).limit(limit).all()
            
        except Exception as e:
            logger.error(f"Error getting records for patient {patient_id}: {e}")
            raise
    
    def get_records_by_provider(
        self, 
        provider_id: int,
        record_type: RecordTypeEnum = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[ClinicalRecord]:
        """Get clinical records created by a specific provider"""
        try:
            query = self.db.query(ClinicalRecord).filter(ClinicalRecord.provider_id == provider_id)
            
            if record_type:
                query = query.filter(ClinicalRecord.record_type == record_type)
            
            return query.order_by(desc(ClinicalRecord.record_date)).offset(skip).limit(limit).all()
            
        except Exception as e:
            logger.error(f"Error getting records for provider {provider_id}: {e}")
            raise
    
    def get_records_by_appointment(self, appointment_id: int) -> List[ClinicalRecord]:
        """Get clinical records for a specific appointment"""
        try:
            return self.db.query(ClinicalRecord).filter(
                ClinicalRecord.appointment_id == appointment_id
            ).order_by(desc(ClinicalRecord.record_date)).all()
            
        except Exception as e:
            logger.error(f"Error getting records for appointment {appointment_id}: {e}")
            raise
    
    def get_records_by_date_range(
        self, 
        start_date: date, 
        end_date: date,
        patient_id: int = None,
        provider_id: int = None,
        record_type: RecordTypeEnum = None
    ) -> List[ClinicalRecord]:
        """Get clinical records within a date range"""
        try:
            query = self.db.query(ClinicalRecord).filter(
                and_(
                    func.date(ClinicalRecord.record_date) >= start_date,
                    func.date(ClinicalRecord.record_date) <= end_date
                )
            )
            
            if patient_id:
                query = query.filter(ClinicalRecord.patient_id == patient_id)
            
            if provider_id:
                query = query.filter(ClinicalRecord.provider_id == provider_id)
            
            if record_type:
                query = query.filter(ClinicalRecord.record_type == record_type)
            
            return query.order_by(desc(ClinicalRecord.record_date)).all()
            
        except Exception as e:
            logger.error(f"Error getting records by date range: {e}")
            raise
    
    def get_vital_signs_history(self, patient_id: int, days_back: int = 30) -> List[ClinicalRecord]:
        """Get vital signs history for a patient"""
        try:
            end_date = date.today()
            start_date = end_date - timedelta(days=days_back)
            
            return self.db.query(ClinicalRecord).filter(
                and_(
                    ClinicalRecord.patient_id == patient_id,
                    ClinicalRecord.record_type == RecordTypeEnum.VITAL_SIGNS,
                    func.date(ClinicalRecord.record_date) >= start_date,
                    func.date(ClinicalRecord.record_date) <= end_date
                )
            ).order_by(desc(ClinicalRecord.record_date)).all()
            
        except Exception as e:
            logger.error(f"Error getting vital signs history for patient {patient_id}: {e}")
            raise
    
    def get_lab_results(
        self, 
        patient_id: int, 
        test_name: str = None, 
        abnormal_only: bool = False
    ) -> List[ClinicalRecord]:
        """Get lab results for a patient"""
        try:
            query = self.db.query(ClinicalRecord).filter(
                and_(
                    ClinicalRecord.patient_id == patient_id,
                    ClinicalRecord.record_type == RecordTypeEnum.LAB_RESULT
                )
            )
            
            if test_name:
                query = query.filter(ClinicalRecord.lab_test_name.ilike(f"%{test_name}%"))
            
            if abnormal_only:
                query = query.filter(ClinicalRecord.lab_abnormal_flag == True)
            
            return query.order_by(desc(ClinicalRecord.record_date)).all()
            
        except Exception as e:
            logger.error(f"Error getting lab results for patient {patient_id}: {e}")
            raise
    
    def get_active_diagnoses(self, patient_id: int) -> List[ClinicalRecord]:
        """Get active diagnoses for a patient"""
        try:
            return self.db.query(ClinicalRecord).filter(
                and_(
                    ClinicalRecord.patient_id == patient_id,
                    ClinicalRecord.record_type == RecordTypeEnum.DIAGNOSIS,
                    ClinicalRecord.diagnosis_status.in_([StatusEnum.ACTIVE, StatusEnum.CHRONIC])
                )
            ).order_by(desc(ClinicalRecord.record_date)).all()
            
        except Exception as e:
            logger.error(f"Error getting active diagnoses for patient {patient_id}: {e}")
            raise
    
    def get_current_medications(self, patient_id: int) -> List[ClinicalRecord]:
        """Get current medications for a patient"""
        try:
            return self.db.query(ClinicalRecord).filter(
                and_(
                    ClinicalRecord.patient_id == patient_id,
                    ClinicalRecord.record_type == RecordTypeEnum.PRESCRIPTION,
                    ClinicalRecord.status == StatusEnum.ACTIVE
                )
            ).order_by(desc(ClinicalRecord.record_date)).all()
            
        except Exception as e:
            logger.error(f"Error getting current medications for patient {patient_id}: {e}")
            raise
    
    def get_allergies(self, patient_id: int) -> List[ClinicalRecord]:
        """Get allergies for a patient"""
        try:
            return self.db.query(ClinicalRecord).filter(
                and_(
                    ClinicalRecord.patient_id == patient_id,
                    ClinicalRecord.record_type == RecordTypeEnum.ALLERGY,
                    ClinicalRecord.status == StatusEnum.ACTIVE
                )
            ).order_by(desc(ClinicalRecord.record_date)).all()
            
        except Exception as e:
            logger.error(f"Error getting allergies for patient {patient_id}: {e}")
            raise
    
    def get_immunization_history(self, patient_id: int) -> List[ClinicalRecord]:
        """Get immunization history for a patient"""
        try:
            return self.db.query(ClinicalRecord).filter(
                and_(
                    ClinicalRecord.patient_id == patient_id,
                    ClinicalRecord.record_type == RecordTypeEnum.IMMUNIZATION
                )
            ).order_by(desc(ClinicalRecord.record_date)).all()
            
        except Exception as e:
            logger.error(f"Error getting immunization history for patient {patient_id}: {e}")
            raise
    
    def create_vital_signs(self, vital_signs_data: Dict[str, Any]) -> ClinicalRecord:
        """Create a vital signs record"""
        try:
            record_data = {
                **vital_signs_data,
                "record_type": RecordTypeEnum.VITAL_SIGNS,
                "title": "Vital Signs",
                "status": StatusEnum.ACTIVE
            }
            
            # Calculate BMI if height and weight are provided
            if vital_signs_data.get("height") and vital_signs_data.get("weight"):
                height_inches = float(vital_signs_data["height"])
                weight_lbs = float(vital_signs_data["weight"])
                
                # BMI = (weight in kg) / (height in meters)^2
                weight_kg = weight_lbs * 0.453592
                height_m = height_inches * 0.0254
                bmi = weight_kg / (height_m ** 2)
                record_data["bmi"] = round(bmi, 1)
            
            return self.create(record_data)
            
        except Exception as e:
            logger.error(f"Error creating vital signs record: {e}")
            raise
    
    def create_lab_result(self, lab_data: Dict[str, Any]) -> ClinicalRecord:
        """Create a lab result record"""
        try:
            record_data = {
                **lab_data,
                "record_type": RecordTypeEnum.LAB_RESULT,
                "title": f"Lab: {lab_data.get('lab_test_name', 'Unknown Test')}",
                "status": StatusEnum.ACTIVE
            }
            
            return self.create(record_data)
            
        except Exception as e:
            logger.error(f"Error creating lab result record: {e}")
            raise
    
    def create_diagnosis(self, diagnosis_data: Dict[str, Any]) -> ClinicalRecord:
        """Create a diagnosis record"""
        try:
            record_data = {
                **diagnosis_data,
                "record_type": RecordTypeEnum.DIAGNOSIS,
                "title": f"Diagnosis: {diagnosis_data.get('diagnosis_description', 'Unspecified')}",
                "status": diagnosis_data.get("diagnosis_status", StatusEnum.ACTIVE)
            }
            
            return self.create(record_data)
            
        except Exception as e:
            logger.error(f"Error creating diagnosis record: {e}")
            raise
    
    def create_prescription(self, prescription_data: Dict[str, Any]) -> ClinicalRecord:
        """Create a prescription record"""
        try:
            record_data = {
                **prescription_data,
                "record_type": RecordTypeEnum.PRESCRIPTION,
                "title": f"Prescription: {prescription_data.get('medication_name', 'Unknown Medication')}",
                "status": StatusEnum.ACTIVE
            }
            
            return self.create(record_data)
            
        except Exception as e:
            logger.error(f"Error creating prescription record: {e}")
            raise
    
    def create_allergy(self, allergy_data: Dict[str, Any]) -> ClinicalRecord:
        """Create an allergy record"""
        try:
            record_data = {
                **allergy_data,
                "record_type": RecordTypeEnum.ALLERGY,
                "title": f"Allergy: {allergy_data.get('allergen', 'Unknown Allergen')}",
                "status": StatusEnum.ACTIVE
            }
            
            return self.create(record_data)
            
        except Exception as e:
            logger.error(f"Error creating allergy record: {e}")
            raise
    
    def create_immunization(self, immunization_data: Dict[str, Any]) -> ClinicalRecord:
        """Create an immunization record"""
        try:
            record_data = {
                **immunization_data,
                "record_type": RecordTypeEnum.IMMUNIZATION,
                "title": f"Immunization: {immunization_data.get('vaccine_name', 'Unknown Vaccine')}",
                "status": StatusEnum.ACTIVE
            }
            
            return self.create(record_data)
            
        except Exception as e:
            logger.error(f"Error creating immunization record: {e}")
            raise
    
    def get_by_cerbo_id(self, cerbo_id: str) -> Optional[ClinicalRecord]:
        """Get clinical record by CERBO external ID"""
        return self.get_by_field("cerbo_record_id", cerbo_id)
    
    async def create_record_with_cerbo_sync(self, record_data: Dict[str, Any]) -> ClinicalRecord:
        """Create clinical record locally and sync with CERBO API"""
        try:
            # Create record locally first
            record = self.create(record_data)
            
            # Sync with CERBO if client is available
            if self.cerbo_client:
                try:
                    cerbo_record_data = self._convert_to_cerbo_format(record)
                    cerbo_response = await self.cerbo_client.create_clinical_record(
                        record.patient.cerbo_patient_id, cerbo_record_data
                    )
                    
                    # Update local record with CERBO ID
                    if cerbo_response and 'id' in cerbo_response:
                        self.update(record.id, {"cerbo_record_id": cerbo_response['id']})
                        logger.info(f"Clinical record {record.id} synced with CERBO ID: {cerbo_response['id']}")
                    
                except CerboAPIException as e:
                    logger.warning(f"Failed to sync clinical record {record.id} with CERBO: {e}")
                    # Continue without CERBO sync
            
            return record
        except Exception as e:
            logger.error(f"Error creating clinical record with CERBO sync: {e}")
            raise
    
    async def update_record_with_cerbo_sync(self, record_id: int, record_data: Dict[str, Any]) -> Optional[ClinicalRecord]:
        """Update clinical record locally and sync with CERBO API"""
        try:
            # Update record locally
            record = self.update(record_id, record_data)
            if not record:
                return None
            
            # Sync with CERBO if client is available and record has CERBO ID
            if self.cerbo_client and record.cerbo_record_id:
                try:
                    cerbo_record_data = self._convert_to_cerbo_format(record)
                    await self.cerbo_client.update_clinical_record(record.cerbo_record_id, cerbo_record_data)
                    logger.info(f"Clinical record {record.id} updated in CERBO")
                    
                except CerboAPIException as e:
                    logger.warning(f"Failed to sync clinical record {record.id} update with CERBO: {e}")
                    # Continue without CERBO sync
            
            return record
        except Exception as e:
            logger.error(f"Error updating clinical record with CERBO sync: {e}")
            raise
    
    async def sync_from_cerbo(self, cerbo_record_id: str) -> Optional[ClinicalRecord]:
        """Sync clinical record data from CERBO API"""
        if not self.cerbo_client:
            raise ValueError("CERBO client not available")
        
        try:
            # Get record data from CERBO
            cerbo_record = await self.cerbo_client.get_clinical_record(cerbo_record_id)
            
            if not cerbo_record:
                return None
            
            # Check if record already exists locally
            existing_record = self.get_by_cerbo_id(cerbo_record_id)
            
            # Convert CERBO data to local format
            record_data = self._convert_from_cerbo_format(cerbo_record)
            record_data['cerbo_record_id'] = cerbo_record_id
            
            if existing_record:
                # Update existing record
                return self.update(existing_record.id, record_data)
            else:
                # Create new record
                return self.create(record_data)
                
        except CerboAPIException as e:
            logger.error(f"Error syncing clinical record from CERBO: {e}")
            raise
    
    def get_patient_medical_summary(self, patient_id: int) -> Dict[str, Any]:
        """Get comprehensive medical summary for a patient"""
        try:
            patient = self.db.query(Patient).filter(Patient.id == patient_id).first()
            if not patient:
                return None
            
            # Get all record types
            vital_signs = self.get_vital_signs_history(patient_id, days_back=90)
            lab_results = self.get_lab_results(patient_id)
            diagnoses = self.get_active_diagnoses(patient_id)
            medications = self.get_current_medications(patient_id)
            allergies = self.get_allergies(patient_id)
            immunizations = self.get_immunization_history(patient_id)
            
            # Get latest vital signs
            latest_vitals = vital_signs[0] if vital_signs else None
            
            # Get abnormal lab results
            abnormal_labs = [lab for lab in lab_results if lab.lab_abnormal_flag]
            
            return {
                "patient": patient.to_dict(),
                "latest_vital_signs": latest_vitals.to_dict() if latest_vitals else None,
                "active_diagnoses": [dx.to_dict() for dx in diagnoses],
                "current_medications": [med.to_dict() for med in medications],
                "allergies": [allergy.to_dict() for allergy in allergies],
                "recent_immunizations": [imm.to_dict() for imm in immunizations[-5:]],  # Last 5
                "abnormal_lab_results": [lab.to_dict() for lab in abnormal_labs[-10:]],  # Last 10
                "summary_statistics": {
                    "total_diagnoses": len(diagnoses),
                    "total_medications": len(medications),
                    "total_allergies": len(allergies),
                    "total_immunizations": len(immunizations),
                    "abnormal_labs_count": len(abnormal_labs),
                    "vital_signs_entries": len(vital_signs)
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting patient medical summary for {patient_id}: {e}")
            raise
    
    def get_record_statistics(
        self, 
        start_date: date = None, 
        end_date: date = None,
        provider_id: int = None
    ) -> Dict[str, Any]:
        """Get clinical record statistics"""
        try:
            if not start_date:
                start_date = date.today() - timedelta(days=30)
            if not end_date:
                end_date = date.today()
            
            query = self.db.query(ClinicalRecord).filter(
                and_(
                    func.date(ClinicalRecord.record_date) >= start_date,
                    func.date(ClinicalRecord.record_date) <= end_date
                )
            )
            
            if provider_id:
                query = query.filter(ClinicalRecord.provider_id == provider_id)
            
            records = query.all()
            
            # Count by record type
            type_counts = {}
            for record_type in RecordTypeEnum:
                type_counts[record_type.value] = len([r for r in records if r.record_type == record_type])
            
            # Count by status
            status_counts = {}
            for status in StatusEnum:
                status_counts[status.value] = len([r for r in records if r.status == status])
            
            return {
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "days": (end_date - start_date).days + 1
                },
                "total_records": len(records),
                "records_by_type": type_counts,
                "records_by_status": status_counts,
                "unique_patients": len(set(r.patient_id for r in records)),
                "unique_providers": len(set(r.provider_id for r in records)),
                "average_records_per_day": round(len(records) / ((end_date - start_date).days + 1), 2)
            }
            
        except Exception as e:
            logger.error(f"Error getting record statistics: {e}")
            raise
    
    def _convert_to_cerbo_format(self, record: ClinicalRecord) -> Dict[str, Any]:
        """Convert local clinical record model to CERBO API format"""
        return {
            "type": record.record_type.value if record.record_type else None,
            "date": record.record_date.isoformat() if record.record_date else None,
            "title": record.title,
            "description": record.description,
            "notes": record.clinical_notes,
            "vital_signs": {
                "temperature": float(record.temperature) if record.temperature else None,
                "blood_pressure": f"{record.blood_pressure_systolic}/{record.blood_pressure_diastolic}" if record.blood_pressure_systolic and record.blood_pressure_diastolic else None,
                "heart_rate": record.heart_rate,
                "respiratory_rate": record.respiratory_rate,
                "oxygen_saturation": float(record.oxygen_saturation) if record.oxygen_saturation else None,
                "weight": float(record.weight) if record.weight else None,
                "height": float(record.height) if record.height else None,
                "bmi": float(record.bmi) if record.bmi else None,
                "pain_scale": record.pain_scale
            } if record.record_type == RecordTypeEnum.VITAL_SIGNS else None,
            "lab_result": {
                "test_name": record.lab_test_name,
                "result_value": record.lab_result_value,
                "unit": record.lab_result_unit,
                "reference_range": record.lab_reference_range,
                "abnormal": record.lab_abnormal_flag
            } if record.record_type == RecordTypeEnum.LAB_RESULT else None,
            "diagnosis": {
                "icd_10_code": record.icd_10_code,
                "description": record.diagnosis_description,
                "status": record.diagnosis_status.value if record.diagnosis_status else None,
                "severity": record.diagnosis_severity.value if record.diagnosis_severity else None
            } if record.record_type == RecordTypeEnum.DIAGNOSIS else None,
            "prescription": {
                "medication_name": record.medication_name,
                "dosage": record.dosage,
                "frequency": record.frequency,
                "duration": record.duration,
                "instructions": record.prescribing_instructions
            } if record.record_type == RecordTypeEnum.PRESCRIPTION else None
        }
    
    def _convert_from_cerbo_format(self, cerbo_record: Dict[str, Any]) -> Dict[str, Any]:
        """Convert CERBO API format to local clinical record model"""
        base_data = {
            "record_type": cerbo_record.get('type'),
            "record_date": datetime.fromisoformat(cerbo_record['date']) if cerbo_record.get('date') else None,
            "title": cerbo_record.get('title'),
            "description": cerbo_record.get('description'),
            "clinical_notes": cerbo_record.get('notes')
        }
        
        # Add type-specific data
        if cerbo_record.get('vital_signs'):
            vital_signs = cerbo_record['vital_signs']
            bp = vital_signs.get('blood_pressure', '').split('/') if vital_signs.get('blood_pressure') else ['', '']
            
            base_data.update({
                "temperature": vital_signs.get('temperature'),
                "blood_pressure_systolic": int(bp[0]) if bp[0] and bp[0].isdigit() else None,
                "blood_pressure_diastolic": int(bp[1]) if len(bp) > 1 and bp[1] and bp[1].isdigit() else None,
                "heart_rate": vital_signs.get('heart_rate'),
                "respiratory_rate": vital_signs.get('respiratory_rate'),
                "oxygen_saturation": vital_signs.get('oxygen_saturation'),
                "weight": vital_signs.get('weight'),
                "height": vital_signs.get('height'),
                "bmi": vital_signs.get('bmi'),
                "pain_scale": vital_signs.get('pain_scale')
            })
        
        if cerbo_record.get('lab_result'):
            lab_result = cerbo_record['lab_result']
            base_data.update({
                "lab_test_name": lab_result.get('test_name'),
                "lab_result_value": lab_result.get('result_value'),
                "lab_result_unit": lab_result.get('unit'),
                "lab_reference_range": lab_result.get('reference_range'),
                "lab_abnormal_flag": lab_result.get('abnormal', False)
            })
        
        if cerbo_record.get('diagnosis'):
            diagnosis = cerbo_record['diagnosis']
            base_data.update({
                "icd_10_code": diagnosis.get('icd_10_code'),
                "diagnosis_description": diagnosis.get('description'),
                "diagnosis_status": diagnosis.get('status'),
                "diagnosis_severity": diagnosis.get('severity')
            })
        
        if cerbo_record.get('prescription'):
            prescription = cerbo_record['prescription']
            base_data.update({
                "medication_name": prescription.get('medication_name'),
                "dosage": prescription.get('dosage'),
                "frequency": prescription.get('frequency'),
                "duration": prescription.get('duration'),
                "prescribing_instructions": prescription.get('instructions')
            })
        
        return base_data
    
    # Alias methods for API compatibility
    def get_patient_allergies(self, patient_id: int, active_only: bool = True) -> List[ClinicalRecord]:
        """Alias for get_allergies with active filter"""
        allergies = self.get_allergies(patient_id)
        if active_only:
            return [allergy for allergy in allergies if allergy.status == StatusEnum.ACTIVE]
        return allergies
    
    def get_patient_medications(self, patient_id: int, active_only: bool = True) -> List[ClinicalRecord]:
        """Alias for get_current_medications with active filter"""
        medications = self.get_current_medications(patient_id)
        if not active_only:
            # If not filtering by active, get all prescription records
            all_prescriptions = self.db.query(ClinicalRecord).filter(
                and_(
                    ClinicalRecord.patient_id == patient_id,
                    ClinicalRecord.record_type == RecordTypeEnum.PRESCRIPTION
                )
            ).order_by(desc(ClinicalRecord.record_date)).all()
            return all_prescriptions
        return medications
    
    def get_patient_diagnoses(self, patient_id: int, active_only: bool = True) -> List[ClinicalRecord]:
        """Alias for get_active_diagnoses with active filter"""
        if active_only:
            return self.get_active_diagnoses(patient_id)
        else:
            # Get all diagnosis records
            all_diagnoses = self.db.query(ClinicalRecord).filter(
                and_(
                    ClinicalRecord.patient_id == patient_id,
                    ClinicalRecord.record_type == RecordTypeEnum.DIAGNOSIS
                )
            ).order_by(desc(ClinicalRecord.record_date)).all()
            return all_diagnoses
    
    def get_latest_vital_signs(self, patient_id: int) -> Optional[ClinicalRecord]:
        """Get the latest vital signs for a patient"""
        try:
            vital_signs = self.get_vital_signs_history(patient_id, days_back=30)
            return vital_signs[0] if vital_signs else None
        except Exception as e:
            logger.error(f"Error getting latest vital signs for patient {patient_id}: {e}")
            raise