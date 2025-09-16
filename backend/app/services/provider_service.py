from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func, desc, asc
from datetime import datetime, date, timedelta
import logging

from .base_repository import BaseRepository
from ..models.provider import Provider, ProviderTypeEnum, ProviderStatusEnum
from ..models.appointment import Appointment, AppointmentStatusEnum
from ..api.cerbo_client import CerboClient, CerboAPIException

logger = logging.getLogger(__name__)

class ProviderService(BaseRepository[Provider]):
    """
    Provider service with schedule management, specialty filtering, and CERBO API integration
    """
    
    def __init__(self, db: Session, cerbo_client: CerboClient = None):
        super().__init__(Provider, db)
        self.cerbo_client = cerbo_client
    
    def search_providers(
        self, 
        search_term: str, 
        search_type: str = "all",
        skip: int = 0, 
        limit: int = 100
    ) -> List[Provider]:
        """
        Advanced provider search with multiple criteria
        """
        try:
            if not search_term:
                return self.get_all(skip=skip, limit=limit)
            
            query = self.db.query(Provider)
            
            if search_type == "name":
                # Search by name (first, middle, last)
                query = query.filter(
                    or_(
                        Provider.first_name.ilike(f"%{search_term}%"),
                        Provider.middle_name.ilike(f"%{search_term}%"),
                        Provider.last_name.ilike(f"%{search_term}%"),
                        func.concat(Provider.first_name, ' ', Provider.last_name).ilike(f"%{search_term}%"),
                        func.concat(Provider.title, ' ', Provider.last_name).ilike(f"%{search_term}%")
                    )
                )
            elif search_type == "specialty":
                # Search by specialty (JSON field)
                query = query.filter(
                    Provider.specialties.contains([search_term])
                )
            elif search_type == "type":
                # Search by provider type
                try:
                    provider_type = ProviderTypeEnum(search_term.lower())
                    query = query.filter(Provider.provider_type == provider_type)
                except ValueError:
                    logger.warning(f"Invalid provider type for search: {search_term}")
                    return []
            elif search_type == "npi":
                # Search by NPI number
                query = query.filter(Provider.npi_number.ilike(f"%{search_term}%"))
            elif search_type == "license":
                # Search by license number
                query = query.filter(Provider.license_number.ilike(f"%{search_term}%"))
            elif search_type == "department":
                # Search by department
                query = query.filter(Provider.department.ilike(f"%{search_term}%"))
            elif search_type == "language":
                # Search by languages spoken
                query = query.filter(
                    Provider.languages_spoken.contains([search_term])
                )
            else:
                # Search all fields
                query = query.filter(
                    or_(
                        Provider.first_name.ilike(f"%{search_term}%"),
                        Provider.middle_name.ilike(f"%{search_term}%"),
                        Provider.last_name.ilike(f"%{search_term}%"),
                        Provider.npi_number.ilike(f"%{search_term}%"),
                        Provider.license_number.ilike(f"%{search_term}%"),
                        Provider.department.ilike(f"%{search_term}%"),
                        Provider.employee_id.ilike(f"%{search_term}%")
                    )
                )
            
            return query.filter(Provider.status == ProviderStatusEnum.ACTIVE).offset(skip).limit(limit).all()
            
        except Exception as e:
            logger.error(f"Error searching providers: {e}")
            raise
    
    def get_by_npi_number(self, npi: str) -> Optional[Provider]:
        """Get provider by NPI number"""
        return self.get_by_field("npi_number", npi)
    
    def get_by_license_number(self, license_number: str) -> Optional[Provider]:
        """Get provider by license number"""
        return self.get_by_field("license_number", license_number)
    
    def get_by_employee_id(self, employee_id: str) -> Optional[Provider]:
        """Get provider by employee ID"""
        return self.get_by_field("employee_id", employee_id)
    
    def get_by_cerbo_id(self, cerbo_id: str) -> Optional[Provider]:
        """Get provider by CERBO external ID"""
        return self.get_by_field("cerbo_provider_id", cerbo_id)
    
    def get_providers_by_specialty(self, specialty: str) -> List[Provider]:
        """Get providers by specialty"""
        try:
            return self.db.query(Provider).filter(
                and_(
                    Provider.specialties.contains([specialty]),
                    Provider.status == ProviderStatusEnum.ACTIVE
                )
            ).all()
        except Exception as e:
            logger.error(f"Error getting providers by specialty: {e}")
            raise
    
    def get_providers_by_type(self, provider_type: ProviderTypeEnum) -> List[Provider]:
        """Get providers by type"""
        try:
            return self.db.query(Provider).filter(
                and_(
                    Provider.provider_type == provider_type,
                    Provider.status == ProviderStatusEnum.ACTIVE
                )
            ).all()
        except Exception as e:
            logger.error(f"Error getting providers by type: {e}")
            raise
    
    def get_providers_by_department(self, department: str) -> List[Provider]:
        """Get providers by department"""
        try:
            return self.db.query(Provider).filter(
                and_(
                    Provider.department.ilike(f"%{department}%"),
                    Provider.status == ProviderStatusEnum.ACTIVE
                )
            ).all()
        except Exception as e:
            logger.error(f"Error getting providers by department: {e}")
            raise
    
    def get_providers_accepting_new_patients(self) -> List[Provider]:
        """Get providers who are accepting new patients"""
        try:
            return self.db.query(Provider).filter(
                and_(
                    Provider.is_accepting_new_patients == True,
                    Provider.status == ProviderStatusEnum.ACTIVE
                )
            ).all()
        except Exception as e:
            logger.error(f"Error getting providers accepting new patients: {e}")
            raise
    
    def get_providers_by_language(self, language: str) -> List[Provider]:
        """Get providers who speak a specific language"""
        try:
            return self.db.query(Provider).filter(
                and_(
                    Provider.languages_spoken.contains([language]),
                    Provider.status == ProviderStatusEnum.ACTIVE
                )
            ).all()
        except Exception as e:
            logger.error(f"Error getting providers by language: {e}")
            raise
    
    def get_provider_schedule(
        self, 
        provider_id: int, 
        start_date: date, 
        end_date: date
    ) -> Dict[str, Any]:
        """Get provider's schedule for a date range"""
        try:
            provider = self.get_by_id(provider_id)
            if not provider:
                return None
            
            # Get appointments in the date range
            appointments = self.db.query(Appointment).filter(
                and_(
                    Appointment.provider_id == provider_id,
                    func.date(Appointment.appointment_date) >= start_date,
                    func.date(Appointment.appointment_date) <= end_date,
                    Appointment.status.in_([
                        AppointmentStatusEnum.SCHEDULED,
                        AppointmentStatusEnum.CONFIRMED,
                        AppointmentStatusEnum.CHECKED_IN,
                        AppointmentStatusEnum.IN_PROGRESS,
                        AppointmentStatusEnum.COMPLETED
                    ])
                )
            ).order_by(Appointment.appointment_date).all()
            
            # Group appointments by date
            schedule_by_date = {}
            current_date = start_date
            
            while current_date <= end_date:
                date_str = current_date.isoformat()
                day_appointments = [
                    apt for apt in appointments 
                    if apt.appointment_date.date() == current_date
                ]
                
                # Calculate schedule statistics for the day
                total_scheduled_time = sum(apt.duration_minutes for apt in day_appointments)
                working_hours = self._get_working_hours_for_date(provider, current_date)
                
                schedule_by_date[date_str] = {
                    "date": date_str,
                    "appointments": [apt.to_dict() for apt in day_appointments],
                    "appointment_count": len(day_appointments),
                    "total_scheduled_minutes": total_scheduled_time,
                    "working_hours": working_hours,
                    "utilization_percentage": self._calculate_utilization(total_scheduled_time, working_hours)
                }
                
                current_date += timedelta(days=1)
            
            return {
                "provider": provider.to_dict(),
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "schedule": schedule_by_date,
                "summary": {
                    "total_appointments": len(appointments),
                    "total_scheduled_minutes": sum(apt.duration_minutes for apt in appointments),
                    "busiest_day": max(schedule_by_date.keys(), 
                                     key=lambda d: schedule_by_date[d]["appointment_count"],
                                     default=None),
                    "average_appointments_per_day": len(appointments) / ((end_date - start_date).days + 1)
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting provider schedule: {e}")
            raise
    
    def get_provider_availability(
        self, 
        provider_id: int, 
        target_date: date,
        appointment_duration: int = 30
    ) -> List[Dict[str, Any]]:
        """Get available time slots for a provider on a specific date"""
        try:
            provider = self.get_by_id(provider_id)
            if not provider or provider.status != ProviderStatusEnum.ACTIVE:
                return []
            
            # Get working hours for the date
            working_hours = self._get_working_hours_for_date(provider, target_date)
            if not working_hours:
                return []
            
            # Get existing appointments
            existing_appointments = self.db.query(Appointment).filter(
                and_(
                    Appointment.provider_id == provider_id,
                    func.date(Appointment.appointment_date) == target_date,
                    Appointment.status.in_([
                        AppointmentStatusEnum.SCHEDULED,
                        AppointmentStatusEnum.CONFIRMED,
                        AppointmentStatusEnum.CHECKED_IN,
                        AppointmentStatusEnum.IN_PROGRESS
                    ])
                )
            ).all()
            
            # Generate available slots
            available_slots = []
            start_time = datetime.combine(target_date, working_hours["start_time"])
            end_time = datetime.combine(target_date, working_hours["end_time"])
            slot_interval = timedelta(minutes=15)  # 15-minute intervals
            
            current_time = start_time
            while current_time + timedelta(minutes=appointment_duration) <= end_time:
                slot_end = current_time + timedelta(minutes=appointment_duration)
                
                # Check if slot conflicts with existing appointments
                is_available = True
                for appointment in existing_appointments:
                    apt_start = appointment.appointment_date
                    apt_end = apt_start + timedelta(minutes=appointment.duration_minutes)
                    
                    # Check for overlap
                    if (current_time < apt_end and slot_end > apt_start):
                        is_available = False
                        break
                
                if is_available:
                    available_slots.append({
                        "start_time": current_time,
                        "end_time": slot_end,
                        "duration_minutes": appointment_duration,
                        "slot_type": "available"
                    })
                
                current_time += slot_interval
            
            return available_slots
            
        except Exception as e:
            logger.error(f"Error getting provider availability: {e}")
            raise
    
    def get_provider_workload(self, provider_id: int, date_range_days: int = 30) -> Dict[str, Any]:
        """Get provider workload statistics"""
        try:
            provider = self.get_by_id(provider_id)
            if not provider:
                return None
            
            end_date = date.today()
            start_date = end_date - timedelta(days=date_range_days)
            
            # Get appointments in the period
            appointments = self.db.query(Appointment).filter(
                and_(
                    Appointment.provider_id == provider_id,
                    func.date(Appointment.appointment_date) >= start_date,
                    func.date(Appointment.appointment_date) <= end_date
                )
            ).all()
            
            # Calculate statistics
            total_appointments = len(appointments)
            completed_appointments = len([apt for apt in appointments if apt.status == AppointmentStatusEnum.COMPLETED])
            cancelled_appointments = len([apt for apt in appointments if apt.status == AppointmentStatusEnum.CANCELLED])
            no_show_appointments = len([apt for apt in appointments if apt.status == AppointmentStatusEnum.NO_SHOW])
            
            total_scheduled_minutes = sum(apt.duration_minutes for apt in appointments)
            
            # Calculate actual time spent
            actual_minutes = 0
            for apt in appointments:
                if apt.actual_start_time and apt.actual_end_time:
                    duration = apt.actual_end_time - apt.actual_start_time
                    actual_minutes += duration.total_seconds() / 60
            
            # Get unique patients seen
            unique_patients = len(set(apt.patient_id for apt in appointments))
            
            return {
                "provider": provider.to_dict(),
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "days": date_range_days
                },
                "appointments": {
                    "total": total_appointments,
                    "completed": completed_appointments,
                    "cancelled": cancelled_appointments,
                    "no_show": no_show_appointments,
                    "completion_rate": (completed_appointments / total_appointments * 100) if total_appointments > 0 else 0,
                    "cancellation_rate": (cancelled_appointments / total_appointments * 100) if total_appointments > 0 else 0,
                    "no_show_rate": (no_show_appointments / total_appointments * 100) if total_appointments > 0 else 0
                },
                "time": {
                    "scheduled_minutes": total_scheduled_minutes,
                    "actual_minutes": actual_minutes,
                    "scheduled_hours": round(total_scheduled_minutes / 60, 2),
                    "actual_hours": round(actual_minutes / 60, 2),
                    "average_appointment_duration": round(total_scheduled_minutes / total_appointments, 2) if total_appointments > 0 else 0
                },
                "patients": {
                    "unique_patients_seen": unique_patients,
                    "average_appointments_per_patient": round(total_appointments / unique_patients, 2) if unique_patients > 0 else 0
                },
                "daily_averages": {
                    "appointments_per_day": round(total_appointments / date_range_days, 2),
                    "hours_per_day": round(total_scheduled_minutes / (60 * date_range_days), 2)
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting provider workload: {e}")
            raise
    
    def update_provider_schedule(self, provider_id: int, schedule_data: Dict[str, Any]) -> Optional[Provider]:
        """Update provider's working hours and availability"""
        try:
            update_data = {}
            
            if "working_hours" in schedule_data:
                update_data["working_hours"] = schedule_data["working_hours"]
            
            if "availability_exceptions" in schedule_data:
                update_data["availability_exceptions"] = schedule_data["availability_exceptions"]
            
            if "default_appointment_duration" in schedule_data:
                update_data["default_appointment_duration"] = schedule_data["default_appointment_duration"]
            
            if "is_accepting_new_patients" in schedule_data:
                update_data["is_accepting_new_patients"] = schedule_data["is_accepting_new_patients"]
            
            return self.update(provider_id, update_data)
            
        except Exception as e:
            logger.error(f"Error updating provider schedule: {e}")
            raise
    
    def set_provider_status(self, provider_id: int, status: ProviderStatusEnum, reason: str = None) -> Optional[Provider]:
        """Set provider status (active, inactive, on leave, etc.)"""
        try:
            update_data = {"status": status}
            
            if reason:
                current_notes = self.get_by_id(provider_id).notes or ""
                update_data["notes"] = f"{current_notes}\nStatus change to {status.value}: {reason}".strip()
            
            return self.update(provider_id, update_data)
            
        except Exception as e:
            logger.error(f"Error setting provider status: {e}")
            raise
    
    async def create_provider_with_cerbo_sync(self, provider_data: Dict[str, Any]) -> Provider:
        """Create provider locally and sync with CERBO API"""
        try:
            # Create provider locally first
            provider = self.create(provider_data)
            
            # Sync with CERBO if client is available
            if self.cerbo_client:
                try:
                    cerbo_provider_data = self._convert_to_cerbo_format(provider)
                    cerbo_response = await self.cerbo_client.create_provider(cerbo_provider_data)
                    
                    # Update local provider with CERBO ID
                    if cerbo_response and 'id' in cerbo_response:
                        self.update(provider.id, {"cerbo_provider_id": cerbo_response['id']})
                        logger.info(f"Provider {provider.id} synced with CERBO ID: {cerbo_response['id']}")
                    
                except CerboAPIException as e:
                    logger.warning(f"Failed to sync provider {provider.id} with CERBO: {e}")
                    # Continue without CERBO sync
            
            return provider
        except Exception as e:
            logger.error(f"Error creating provider with CERBO sync: {e}")
            raise
    
    async def update_provider_with_cerbo_sync(self, provider_id: int, provider_data: Dict[str, Any]) -> Optional[Provider]:
        """Update provider locally and sync with CERBO API"""
        try:
            # Update provider locally
            provider = self.update(provider_id, provider_data)
            if not provider:
                return None
            
            # Sync with CERBO if client is available and provider has CERBO ID
            if self.cerbo_client and provider.cerbo_provider_id:
                try:
                    cerbo_provider_data = self._convert_to_cerbo_format(provider)
                    await self.cerbo_client.update_provider(provider.cerbo_provider_id, cerbo_provider_data)
                    logger.info(f"Provider {provider.id} updated in CERBO")
                    
                except CerboAPIException as e:
                    logger.warning(f"Failed to sync provider {provider.id} update with CERBO: {e}")
                    # Continue without CERBO sync
            
            return provider
        except Exception as e:
            logger.error(f"Error updating provider with CERBO sync: {e}")
            raise
    
    async def sync_from_cerbo(self, cerbo_provider_id: str) -> Optional[Provider]:
        """Sync provider data from CERBO API"""
        if not self.cerbo_client:
            raise ValueError("CERBO client not available")
        
        try:
            # Get provider data from CERBO
            cerbo_provider = await self.cerbo_client.get_provider(cerbo_provider_id)
            
            if not cerbo_provider:
                return None
            
            # Check if provider already exists locally
            existing_provider = self.get_by_cerbo_id(cerbo_provider_id)
            
            # Convert CERBO data to local format
            provider_data = self._convert_from_cerbo_format(cerbo_provider)
            provider_data['cerbo_provider_id'] = cerbo_provider_id
            
            if existing_provider:
                # Update existing provider
                return self.update(existing_provider.id, provider_data)
            else:
                # Create new provider
                return self.create(provider_data)
                
        except CerboAPIException as e:
            logger.error(f"Error syncing provider from CERBO: {e}")
            raise
    
    def get_provider_summary(self, provider_id: int) -> Dict[str, Any]:
        """Get comprehensive provider summary including related records"""
        try:
            provider = self.get_by_id(provider_id)
            if not provider:
                return None
            
            # Get related statistics
            total_appointments = self.db.query(Appointment).filter(
                Appointment.provider_id == provider_id
            ).count()
            
            recent_appointments = self.db.query(Appointment).filter(
                Appointment.provider_id == provider_id
            ).order_by(Appointment.appointment_date.desc()).limit(10).all()
            
            # Get current month statistics
            today = date.today()
            month_start = today.replace(day=1)
            month_appointments = self.db.query(Appointment).filter(
                and_(
                    Appointment.provider_id == provider_id,
                    func.date(Appointment.appointment_date) >= month_start,
                    func.date(Appointment.appointment_date) <= today
                )
            ).count()
            
            return {
                "provider": provider.to_dict(),
                "statistics": {
                    "total_appointments": total_appointments,
                    "current_month_appointments": month_appointments,
                    "specialties_count": len(provider.specialties) if provider.specialties else 0,
                    "languages_count": len(provider.languages_spoken) if provider.languages_spoken else 0
                },
                "recent_appointments": [apt.to_dict() for apt in recent_appointments],
                "schedule_info": {
                    "default_duration": provider.default_appointment_duration,
                    "accepting_new_patients": provider.is_accepting_new_patients,
                    "status": provider.status.value if provider.status else None
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting provider summary for {provider_id}: {e}")
            raise
    
    def _get_working_hours_for_date(self, provider: Provider, target_date: date) -> Dict[str, Any]:
        """Get working hours for a specific date (simplified implementation)"""
        # This is a simplified implementation
        # In a real system, this would parse the provider's working_hours JSON
        # and handle exceptions, holidays, etc.
        
        if not provider.working_hours:
            # Default working hours
            return {
                "start_time": datetime.min.time().replace(hour=9),  # 9 AM
                "end_time": datetime.min.time().replace(hour=17),   # 5 PM
                "break_start": datetime.min.time().replace(hour=12), # 12 PM
                "break_end": datetime.min.time().replace(hour=13)    # 1 PM
            }
        
        # Parse working hours (simplified)
        day_name = target_date.strftime("%A").lower()
        working_hours = provider.working_hours
        
        if day_name in working_hours:
            day_hours = working_hours[day_name]
            return {
                "start_time": datetime.strptime(day_hours.get("start", "09:00"), "%H:%M").time(),
                "end_time": datetime.strptime(day_hours.get("end", "17:00"), "%H:%M").time(),
                "break_start": datetime.strptime(day_hours.get("break_start", "12:00"), "%H:%M").time() if day_hours.get("break_start") else None,
                "break_end": datetime.strptime(day_hours.get("break_end", "13:00"), "%H:%M").time() if day_hours.get("break_end") else None
            }
        
        return None  # No working hours for this day
    
    def _calculate_utilization(self, scheduled_minutes: int, working_hours: Dict[str, Any]) -> float:
        """Calculate utilization percentage for a day"""
        if not working_hours:
            return 0
        
        start_time = working_hours["start_time"]
        end_time = working_hours["end_time"]
        
        # Calculate total working minutes
        start_datetime = datetime.combine(date.today(), start_time)
        end_datetime = datetime.combine(date.today(), end_time)
        total_working_minutes = (end_datetime - start_datetime).total_seconds() / 60
        
        # Subtract break time if specified
        if working_hours.get("break_start") and working_hours.get("break_end"):
            break_start = datetime.combine(date.today(), working_hours["break_start"])
            break_end = datetime.combine(date.today(), working_hours["break_end"])
            break_minutes = (break_end - break_start).total_seconds() / 60
            total_working_minutes -= break_minutes
        
        if total_working_minutes <= 0:
            return 0
        
        return round((scheduled_minutes / total_working_minutes) * 100, 2)
    
    def _convert_to_cerbo_format(self, provider: Provider) -> Dict[str, Any]:
        """Convert local provider model to CERBO API format"""
        return {
            "first_name": provider.first_name,
            "middle_name": provider.middle_name,
            "last_name": provider.last_name,
            "title": provider.title,
            "provider_type": provider.provider_type.value if provider.provider_type else None,
            "license_number": provider.license_number,
            "npi_number": provider.npi_number,
            "dea_number": provider.dea_number,
            "specialties": provider.specialties,
            "email": provider.email,
            "phone": provider.phone_primary,
            "office_address": {
                "line1": provider.office_address_line_1,
                "line2": provider.office_address_line_2,
                "city": provider.office_city,
                "state": provider.office_state,
                "zip": provider.office_zip_code
            },
            "department": provider.department,
            "status": provider.status.value if provider.status else None
        }
    
    def _convert_from_cerbo_format(self, cerbo_provider: Dict[str, Any]) -> Dict[str, Any]:
        """Convert CERBO API format to local provider model"""
        office_address = cerbo_provider.get('office_address', {})
        
        return {
            "first_name": cerbo_provider.get('first_name'),
            "middle_name": cerbo_provider.get('middle_name'),
            "last_name": cerbo_provider.get('last_name'),
            "title": cerbo_provider.get('title'),
            "provider_type": cerbo_provider.get('provider_type'),
            "license_number": cerbo_provider.get('license_number'),
            "npi_number": cerbo_provider.get('npi_number'),
            "dea_number": cerbo_provider.get('dea_number'),
            "specialties": cerbo_provider.get('specialties'),
            "email": cerbo_provider.get('email'),
            "phone_primary": cerbo_provider.get('phone'),
            "office_address_line_1": office_address.get('line1'),
            "office_address_line_2": office_address.get('line2'),
            "office_city": office_address.get('city'),
            "office_state": office_address.get('state'),
            "office_zip_code": office_address.get('zip'),
            "department": cerbo_provider.get('department'),
            "status": cerbo_provider.get('status', 'active')
        }