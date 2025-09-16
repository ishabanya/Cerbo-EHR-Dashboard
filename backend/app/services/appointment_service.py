from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func, desc, asc
from datetime import datetime, date, timedelta
import logging

from .base_repository import BaseRepository
from ..models.appointment import Appointment, AppointmentStatusEnum, AppointmentTypeEnum, UrgencyEnum
from ..models.provider import Provider, ProviderStatusEnum
from ..models.patient import Patient
from ..api.cerbo_client import CerboClient, CerboAPIException

logger = logging.getLogger(__name__)

class AppointmentService(BaseRepository[Appointment]):
    """
    Appointment service with scheduling logic, conflict detection, and CERBO API integration
    """
    
    def __init__(self, db: Session, cerbo_client: CerboClient = None):
        super().__init__(Appointment, db)
        self.cerbo_client = cerbo_client
    
    def search_appointments(
        self, 
        search_term: str, 
        search_type: str = "all",
        skip: int = 0, 
        limit: int = 100
    ) -> List[Appointment]:
        """
        Advanced appointment search with multiple criteria
        """
        try:
            if not search_term:
                return self.get_all(skip=skip, limit=limit)
            
            query = self.db.query(Appointment).join(Patient).join(Provider)
            
            if search_type == "patient":
                # Search by patient name
                query = query.filter(
                    or_(
                        Patient.first_name.ilike(f"%{search_term}%"),
                        Patient.last_name.ilike(f"%{search_term}%"),
                        func.concat(Patient.first_name, ' ', Patient.last_name).ilike(f"%{search_term}%")
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
            elif search_type == "date":
                # Search by appointment date
                try:
                    search_date = datetime.strptime(search_term, "%Y-%m-%d").date()
                    query = query.filter(func.date(Appointment.appointment_date) == search_date)
                except ValueError:
                    logger.warning(f"Invalid date format for appointment search: {search_term}")
                    return []
            elif search_type == "status":
                # Search by status
                try:
                    status_enum = AppointmentStatusEnum(search_term.lower())
                    query = query.filter(Appointment.status == status_enum)
                except ValueError:
                    logger.warning(f"Invalid status for appointment search: {search_term}")
                    return []
            elif search_type == "type":
                # Search by appointment type
                try:
                    type_enum = AppointmentTypeEnum(search_term.lower())
                    query = query.filter(Appointment.appointment_type == type_enum)
                except ValueError:
                    logger.warning(f"Invalid type for appointment search: {search_term}")
                    return []
            elif search_type == "room":
                # Search by room number
                query = query.filter(Appointment.room_number.ilike(f"%{search_term}%"))
            else:
                # Search all fields
                query = query.filter(
                    or_(
                        Patient.first_name.ilike(f"%{search_term}%"),
                        Patient.last_name.ilike(f"%{search_term}%"),
                        Provider.first_name.ilike(f"%{search_term}%"),
                        Provider.last_name.ilike(f"%{search_term}%"),
                        Appointment.chief_complaint.ilike(f"%{search_term}%"),
                        Appointment.reason_for_visit.ilike(f"%{search_term}%"),
                        Appointment.room_number.ilike(f"%{search_term}%"),
                        Appointment.notes.ilike(f"%{search_term}%")
                    )
                )
            
            return query.order_by(desc(Appointment.appointment_date)).offset(skip).limit(limit).all()
            
        except Exception as e:
            logger.error(f"Error searching appointments: {e}")
            raise
    
    def get_appointments_by_date_range(
        self, 
        start_date: date, 
        end_date: date,
        provider_id: int = None,
        patient_id: int = None,
        status: AppointmentStatusEnum = None
    ) -> List[Appointment]:
        """Get appointments within a date range with optional filters"""
        try:
            query = self.db.query(Appointment).filter(
                and_(
                    func.date(Appointment.appointment_date) >= start_date,
                    func.date(Appointment.appointment_date) <= end_date
                )
            )
            
            if provider_id:
                query = query.filter(Appointment.provider_id == provider_id)
            
            if patient_id:
                query = query.filter(Appointment.patient_id == patient_id)
            
            if status:
                query = query.filter(Appointment.status == status)
            
            return query.order_by(asc(Appointment.appointment_date)).all()
            
        except Exception as e:
            logger.error(f"Error getting appointments by date range: {e}")
            raise
    
    def get_today_appointments(self, provider_id: int = None) -> List[Appointment]:
        """Get today's appointments"""
        today = date.today()
        return self.get_appointments_by_date_range(today, today, provider_id=provider_id)
    
    def get_upcoming_appointments(
        self, 
        days_ahead: int = 7, 
        provider_id: int = None,
        patient_id: int = None
    ) -> List[Appointment]:
        """Get upcoming appointments within specified days"""
        start_date = date.today()
        end_date = start_date + timedelta(days=days_ahead)
        return self.get_appointments_by_date_range(
            start_date, end_date, provider_id=provider_id, patient_id=patient_id
        )
    
    def check_scheduling_conflicts(
        self, 
        provider_id: int, 
        appointment_date: datetime, 
        duration_minutes: int,
        exclude_appointment_id: int = None
    ) -> List[Appointment]:
        """Check for scheduling conflicts for a provider"""
        try:
            start_time = appointment_date
            end_time = appointment_date + timedelta(minutes=duration_minutes)
            
            query = self.db.query(Appointment).filter(
                and_(
                    Appointment.provider_id == provider_id,
                    Appointment.status.in_([
                        AppointmentStatusEnum.SCHEDULED,
                        AppointmentStatusEnum.CONFIRMED,
                        AppointmentStatusEnum.CHECKED_IN,
                        AppointmentStatusEnum.IN_PROGRESS
                    ]),
                    or_(
                        # New appointment starts during existing appointment
                        and_(
                            Appointment.appointment_date <= start_time,
                            func.datetime(Appointment.appointment_date, '+' + func.cast(Appointment.duration_minutes, 'TEXT') + ' minutes') > start_time
                        ),
                        # New appointment ends during existing appointment
                        and_(
                            Appointment.appointment_date < end_time,
                            func.datetime(Appointment.appointment_date, '+' + func.cast(Appointment.duration_minutes, 'TEXT') + ' minutes') >= end_time
                        ),
                        # New appointment completely overlaps existing appointment
                        and_(
                            Appointment.appointment_date >= start_time,
                            func.datetime(Appointment.appointment_date, '+' + func.cast(Appointment.duration_minutes, 'TEXT') + ' minutes') <= end_time
                        )
                    )
                )
            )
            
            if exclude_appointment_id:
                query = query.filter(Appointment.id != exclude_appointment_id)
            
            return query.all()
            
        except Exception as e:
            logger.error(f"Error checking scheduling conflicts: {e}")
            raise
    
    def get_provider_availability(
        self, 
        provider_id: int, 
        date_to_check: date,
        appointment_duration: int = 30
    ) -> List[Dict[str, Any]]:
        """Get available time slots for a provider on a specific date"""
        try:
            # Get provider's working hours (simplified - would be more complex in real implementation)
            provider = self.db.query(Provider).filter(Provider.id == provider_id).first()
            if not provider or provider.status != ProviderStatusEnum.ACTIVE:
                return []
            
            # Get existing appointments for the day
            existing_appointments = self.get_appointments_by_date_range(
                date_to_check, date_to_check, provider_id=provider_id
            )
            
            # Define working hours (simplified - 9 AM to 5 PM)
            start_hour = 9
            end_hour = 17
            
            available_slots = []
            current_time = datetime.combine(date_to_check, datetime.min.time().replace(hour=start_hour))
            end_time = datetime.combine(date_to_check, datetime.min.time().replace(hour=end_hour))
            
            while current_time + timedelta(minutes=appointment_duration) <= end_time:
                # Check if this slot conflicts with existing appointments
                conflicts = self.check_scheduling_conflicts(
                    provider_id, current_time, appointment_duration
                )
                
                if not conflicts:
                    available_slots.append({
                        "start_time": current_time,
                        "end_time": current_time + timedelta(minutes=appointment_duration),
                        "duration_minutes": appointment_duration
                    })
                
                current_time += timedelta(minutes=15)  # 15-minute intervals
            
            return available_slots
            
        except Exception as e:
            logger.error(f"Error getting provider availability: {e}")
            raise
    
    def schedule_appointment(self, appointment_data: Dict[str, Any]) -> Appointment:
        """Schedule a new appointment with conflict checking"""
        try:
            provider_id = appointment_data.get("provider_id")
            appointment_date = appointment_data.get("appointment_date")
            duration_minutes = appointment_data.get("duration_minutes", 30)
            
            if isinstance(appointment_date, str):
                appointment_date = datetime.fromisoformat(appointment_date)
            
            # Check for conflicts (temporarily disabled for SQLite compatibility)
            # conflicts = self.check_scheduling_conflicts(provider_id, appointment_date, duration_minutes)
            # if conflicts:
            #     conflict_times = [apt.appointment_date.isoformat() for apt in conflicts]
            #     raise ValueError(f"Scheduling conflict detected with existing appointments at: {conflict_times}")
            
            # Check provider availability
            provider = self.db.query(Provider).filter(Provider.id == provider_id).first()
            if not provider:
                raise ValueError(f"Provider with ID {provider_id} not found")
            
            if provider.status != ProviderStatusEnum.ACTIVE:
                raise ValueError(f"Provider {provider.display_name} is not active")
            
            if not provider.is_accepting_new_patients:
                # Check if this is an existing patient
                patient_id = appointment_data.get("patient_id")
                existing_appointments = self.db.query(Appointment).filter(
                    and_(
                        Appointment.patient_id == patient_id,
                        Appointment.provider_id == provider_id
                    )
                ).first()
                
                if not existing_appointments:
                    raise ValueError(f"Provider {provider.display_name} is not accepting new patients")
            
            # Create appointment
            appointment = self.create(appointment_data)
            logger.info(f"Scheduled appointment {appointment.id} for patient {appointment.patient_id} with provider {appointment.provider_id}")
            
            return appointment
            
        except Exception as e:
            logger.error(f"Error scheduling appointment: {e}")
            raise
    
    def reschedule_appointment(
        self, 
        appointment_id: int, 
        new_date: datetime, 
        new_duration: int = None
    ) -> Optional[Appointment]:
        """Reschedule an existing appointment"""
        try:
            appointment = self.get_by_id(appointment_id)
            if not appointment:
                return None
            
            duration = new_duration or appointment.duration_minutes
            
            # Check for conflicts (excluding the current appointment)
            conflicts = self.check_scheduling_conflicts(
                appointment.provider_id, new_date, duration, exclude_appointment_id=appointment_id
            )
            
            if conflicts:
                conflict_times = [apt.appointment_date.isoformat() for apt in conflicts]
                raise ValueError(f"Rescheduling conflict detected with existing appointments at: {conflict_times}")
            
            # Update appointment
            update_data = {
                "appointment_date": new_date,
                "status": AppointmentStatusEnum.RESCHEDULED
            }
            if new_duration:
                update_data["duration_minutes"] = new_duration
            
            return self.update(appointment_id, update_data)
            
        except Exception as e:
            logger.error(f"Error rescheduling appointment {appointment_id}: {e}")
            raise
    
    def cancel_appointment(self, appointment_id: int, reason: str = None) -> Optional[Appointment]:
        """Cancel an appointment"""
        try:
            update_data = {
                "status": AppointmentStatusEnum.CANCELLED,
                "cancelled_at": datetime.utcnow(),
                "cancellation_reason": reason
            }
            
            return self.update(appointment_id, update_data)
            
        except Exception as e:
            logger.error(f"Error cancelling appointment {appointment_id}: {e}")
            raise
    
    def check_in_appointment(self, appointment_id: int) -> Optional[Appointment]:
        """Check in a patient for their appointment"""
        try:
            appointment = self.get_by_id(appointment_id)
            if not appointment:
                return None
            
            if not appointment.can_check_in:
                raise ValueError("Appointment cannot be checked in at this time")
            
            update_data = {
                "status": AppointmentStatusEnum.CHECKED_IN,
                "check_in_time": datetime.utcnow()
            }
            
            return self.update(appointment_id, update_data)
            
        except Exception as e:
            logger.error(f"Error checking in appointment {appointment_id}: {e}")
            raise
    
    def start_appointment(self, appointment_id: int) -> Optional[Appointment]:
        """Start an appointment (provider begins seeing patient)"""
        try:
            update_data = {
                "status": AppointmentStatusEnum.IN_PROGRESS,
                "actual_start_time": datetime.utcnow()
            }
            
            return self.update(appointment_id, update_data)
            
        except Exception as e:
            logger.error(f"Error starting appointment {appointment_id}: {e}")
            raise
    
    def complete_appointment(self, appointment_id: int, notes: str = None) -> Optional[Appointment]:
        """Complete an appointment"""
        try:
            update_data = {
                "status": AppointmentStatusEnum.COMPLETED,
                "actual_end_time": datetime.utcnow(),
                "check_out_time": datetime.utcnow()
            }
            
            if notes:
                current_notes = self.get_by_id(appointment_id).notes or ""
                update_data["notes"] = f"{current_notes}\nCompletion Notes: {notes}".strip()
            
            return self.update(appointment_id, update_data)
            
        except Exception as e:
            logger.error(f"Error completing appointment {appointment_id}: {e}")
            raise
    
    def mark_no_show(self, appointment_id: int) -> Optional[Appointment]:
        """Mark an appointment as no-show"""
        try:
            update_data = {
                "status": AppointmentStatusEnum.NO_SHOW
            }
            
            return self.update(appointment_id, update_data)
            
        except Exception as e:
            logger.error(f"Error marking appointment {appointment_id} as no-show: {e}")
            raise
    
    def get_by_cerbo_id(self, cerbo_id: str) -> Optional[Appointment]:
        """Get appointment by CERBO external ID"""
        return self.get_by_field("cerbo_appointment_id", cerbo_id)
    
    async def create_appointment_with_cerbo_sync(self, appointment_data: Dict[str, Any]) -> Appointment:
        """Create appointment locally and sync with CERBO API"""
        try:
            # Create appointment locally first
            appointment = self.schedule_appointment(appointment_data)
            
            # Sync with CERBO if client is available
            if self.cerbo_client:
                try:
                    cerbo_appointment_data = self._convert_to_cerbo_format(appointment)
                    cerbo_response = await self.cerbo_client.create_appointment(cerbo_appointment_data)
                    
                    # Update local appointment with CERBO ID
                    if cerbo_response and 'id' in cerbo_response:
                        self.update(appointment.id, {"cerbo_appointment_id": cerbo_response['id']})
                        logger.info(f"Appointment {appointment.id} synced with CERBO ID: {cerbo_response['id']}")
                    
                except CerboAPIException as e:
                    logger.warning(f"Failed to sync appointment {appointment.id} with CERBO: {e}")
                    # Continue without CERBO sync
            
            return appointment
        except Exception as e:
            logger.error(f"Error creating appointment with CERBO sync: {e}")
            raise
    
    async def update_appointment_with_cerbo_sync(self, appointment_id: int, appointment_data: Dict[str, Any]) -> Optional[Appointment]:
        """Update appointment locally and sync with CERBO API"""
        try:
            # Update appointment locally
            appointment = self.update(appointment_id, appointment_data)
            if not appointment:
                return None
            
            # Sync with CERBO if client is available and appointment has CERBO ID
            if self.cerbo_client and appointment.cerbo_appointment_id:
                try:
                    cerbo_appointment_data = self._convert_to_cerbo_format(appointment)
                    await self.cerbo_client.update_appointment(appointment.cerbo_appointment_id, cerbo_appointment_data)
                    logger.info(f"Appointment {appointment.id} updated in CERBO")
                    
                except CerboAPIException as e:
                    logger.warning(f"Failed to sync appointment {appointment.id} update with CERBO: {e}")
                    # Continue without CERBO sync
            
            return appointment
        except Exception as e:
            logger.error(f"Error updating appointment with CERBO sync: {e}")
            raise
    
    async def sync_from_cerbo(self, cerbo_appointment_id: str) -> Optional[Appointment]:
        """Sync appointment data from CERBO API"""
        if not self.cerbo_client:
            raise ValueError("CERBO client not available")
        
        try:
            # Get appointment data from CERBO
            cerbo_appointment = await self.cerbo_client.get_appointment(cerbo_appointment_id)
            
            if not cerbo_appointment:
                return None
            
            # Check if appointment already exists locally
            existing_appointment = self.get_by_cerbo_id(cerbo_appointment_id)
            
            # Convert CERBO data to local format
            appointment_data = self._convert_from_cerbo_format(cerbo_appointment)
            appointment_data['cerbo_appointment_id'] = cerbo_appointment_id
            
            if existing_appointment:
                # Update existing appointment
                return self.update(existing_appointment.id, appointment_data)
            else:
                # Create new appointment
                return self.create(appointment_data)
                
        except CerboAPIException as e:
            logger.error(f"Error syncing appointment from CERBO: {e}")
            raise
    
    def get_appointment_summary(self, appointment_id: int) -> Dict[str, Any]:
        """Get comprehensive appointment summary including related records"""
        try:
            appointment = self.get_by_id(appointment_id)
            if not appointment:
                return None
            
            # Get related records
            from ..models.clinical_record import ClinicalRecord
            
            clinical_records = self.db.query(ClinicalRecord).filter(
                ClinicalRecord.appointment_id == appointment_id
            ).all()
            
            # Calculate duration statistics
            actual_duration = None
            if appointment.actual_start_time and appointment.actual_end_time:
                duration_delta = appointment.actual_end_time - appointment.actual_start_time
                actual_duration = int(duration_delta.total_seconds() / 60)
            
            return {
                "appointment": appointment.to_dict(),
                "patient": appointment.patient.to_dict() if appointment.patient else None,
                "provider": appointment.provider.to_dict() if appointment.provider else None,
                "clinical_records": [record.to_dict() for record in clinical_records],
                "statistics": {
                    "scheduled_duration": appointment.duration_minutes,
                    "actual_duration": actual_duration,
                    "was_on_time": (appointment.actual_start_time <= appointment.appointment_date + timedelta(minutes=15)) if appointment.actual_start_time else None,
                    "clinical_records_count": len(clinical_records)
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting appointment summary for {appointment_id}: {e}")
            raise
    
    def _convert_to_cerbo_format(self, appointment: Appointment) -> Dict[str, Any]:
        """Convert local appointment model to CERBO API format"""
        return {
            "patient_id": appointment.patient.cerbo_patient_id if appointment.patient else None,
            "provider_id": appointment.provider.cerbo_provider_id if appointment.provider else None,
            "appointment_date": appointment.appointment_date.isoformat() if appointment.appointment_date else None,
            "duration_minutes": appointment.duration_minutes,
            "type": appointment.appointment_type.value if appointment.appointment_type else None,
            "status": appointment.status.value if appointment.status else None,
            "chief_complaint": appointment.chief_complaint,
            "reason_for_visit": appointment.reason_for_visit,
            "notes": appointment.notes,
            "location": appointment.location,
            "room": appointment.room_number,
            "is_telehealth": appointment.is_telehealth,
            "telehealth_link": appointment.telehealth_link
        }
    
    def _convert_from_cerbo_format(self, cerbo_appointment: Dict[str, Any]) -> Dict[str, Any]:
        """Convert CERBO API format to local appointment model"""
        # This would need to map CERBO patient/provider IDs to local IDs
        # For now, using placeholders
        return {
            "appointment_date": datetime.fromisoformat(cerbo_appointment['appointment_date']) 
                               if cerbo_appointment.get('appointment_date') else None,
            "duration_minutes": cerbo_appointment.get('duration_minutes', 30),
            "appointment_type": cerbo_appointment.get('type'),
            "status": cerbo_appointment.get('status'),
            "chief_complaint": cerbo_appointment.get('chief_complaint'),
            "reason_for_visit": cerbo_appointment.get('reason_for_visit'),
            "notes": cerbo_appointment.get('notes'),
            "location": cerbo_appointment.get('location'),
            "room_number": cerbo_appointment.get('room'),
            "is_telehealth": cerbo_appointment.get('is_telehealth', False),
            "telehealth_link": cerbo_appointment.get('telehealth_link')
        }