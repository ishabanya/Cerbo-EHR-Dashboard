from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date
import logging

from ..utils.database import get_db
from ..services.appointment_service import AppointmentService
from ..schemas.appointment import (
    AppointmentCreate, AppointmentUpdate, AppointmentResponse,
    AppointmentSearch, AppointmentConflictCheck
)
from ..schemas.common import PaginatedResponse, SuccessResponse

logger = logging.getLogger(__name__)

router = APIRouter()

def get_appointment_service(db: Session = Depends(get_db)) -> AppointmentService:
    """Dependency to get appointment service"""
    return AppointmentService(db)

@router.get("/", response_model=PaginatedResponse[AppointmentResponse])
async def get_appointments(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    patient_id: Optional[int] = Query(None),
    provider_id: Optional[int] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    status: Optional[str] = Query(None),
    appointment_service: AppointmentService = Depends(get_appointment_service)
):
    """Get appointments with pagination and filtering"""
    try:
        skip = (page - 1) * per_page
        
        if start_date and end_date:
            # Use date range method if dates are provided
            appointments = appointment_service.get_appointments_by_date_range(
                start_date=start_date,
                end_date=end_date,
                provider_id=provider_id,
                patient_id=patient_id
            )
        else:
            # Use search method for general queries
            appointments = appointment_service.search_appointments(
                search_term="",
                search_type="all",
                skip=skip,
                limit=per_page
            )
        
        # Filter by status if provided
        if status and appointments:
            appointments = [apt for apt in appointments if apt.status.value == status]
        
        # Apply pagination
        total = len(appointments)
        appointments = appointments[skip:skip + per_page]
        pages = (total + per_page - 1) // per_page
        
        return PaginatedResponse(
            items=[AppointmentResponse.from_orm(apt) for apt in appointments],
            total=total,
            page=page,
            pages=pages,
            per_page=per_page,
            has_next=page < pages,
            has_prev=page > 1
        )
    except Exception as e:
        logger.error(f"Error getting appointments: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve appointments")

@router.post("/", response_model=AppointmentResponse, status_code=201)
async def create_appointment(
    appointment_data: AppointmentCreate,
    appointment_service: AppointmentService = Depends(get_appointment_service)
):
    """Create a new appointment"""
    try:
        appointment = appointment_service.schedule_appointment(appointment_data.dict())
        return AppointmentResponse.from_orm(appointment)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating appointment: {e}")
        raise HTTPException(status_code=500, detail="Failed to create appointment")

@router.get("/{appointment_id}", response_model=AppointmentResponse)
async def get_appointment(
    appointment_id: int,
    appointment_service: AppointmentService = Depends(get_appointment_service)
):
    """Get a specific appointment by ID"""
    try:
        appointment = appointment_service.get_by_id(appointment_id)
        if not appointment:
            raise HTTPException(status_code=404, detail="Appointment not found")
        return AppointmentResponse.from_orm(appointment)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting appointment {appointment_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve appointment")

@router.put("/{appointment_id}", response_model=AppointmentResponse)
async def update_appointment(
    appointment_id: int,
    appointment_data: AppointmentUpdate,
    appointment_service: AppointmentService = Depends(get_appointment_service)
):
    """Update an appointment"""
    try:
        update_data = {k: v for k, v in appointment_data.dict().items() if v is not None}
        appointment = appointment_service.update(appointment_id, update_data)
        
        if not appointment:
            raise HTTPException(status_code=404, detail="Appointment not found")
        
        return AppointmentResponse.from_orm(appointment)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating appointment {appointment_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update appointment")

@router.delete("/{appointment_id}", response_model=SuccessResponse)
async def cancel_appointment(
    appointment_id: int,
    reason: Optional[str] = Query(None),
    appointment_service: AppointmentService = Depends(get_appointment_service)
):
    """Cancel an appointment"""
    try:
        appointment = appointment_service.cancel_appointment(appointment_id, reason)
        if not appointment:
            raise HTTPException(status_code=404, detail="Appointment not found")
        
        return SuccessResponse(message="Appointment successfully cancelled")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling appointment {appointment_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to cancel appointment")

@router.post("/check-conflicts", response_model=dict)
async def check_appointment_conflicts(
    conflict_data: AppointmentConflictCheck,
    appointment_service: AppointmentService = Depends(get_appointment_service)
):
    """Check for appointment scheduling conflicts"""
    try:
        conflicts = appointment_service.check_scheduling_conflicts(
            provider_id=conflict_data.provider_id,
            appointment_date=conflict_data.appointment_date,
            duration_minutes=conflict_data.duration_minutes,
            exclude_appointment_id=conflict_data.exclude_appointment_id
        )
        
        return {
            "has_conflicts": len(conflicts) > 0,
            "conflicts": [AppointmentResponse.from_orm(apt) for apt in conflicts]
        }
    except Exception as e:
        logger.error(f"Error checking conflicts: {e}")
        raise HTTPException(status_code=500, detail="Failed to check appointment conflicts")

@router.get("/provider/{provider_id}/availability")
async def get_provider_availability(
    provider_id: int,
    start_date: date = Query(...),
    end_date: date = Query(...),
    appointment_service: AppointmentService = Depends(get_appointment_service)
):
    """Get provider availability for a date range"""
    try:
        availability = appointment_service.get_provider_availability(
            provider_id=provider_id,
            start_date=start_date,
            end_date=end_date
        )
        return {"availability": availability}
    except Exception as e:
        logger.error(f"Error getting provider availability: {e}")
        raise HTTPException(status_code=500, detail="Failed to get provider availability")

@router.post("/{appointment_id}/check-in", response_model=AppointmentResponse)
async def check_in_appointment(
    appointment_id: int,
    appointment_service: AppointmentService = Depends(get_appointment_service)
):
    """Check in a patient for their appointment"""
    try:
        appointment = appointment_service.check_in_appointment(appointment_id)
        if not appointment:
            raise HTTPException(status_code=404, detail="Appointment not found")
        
        return AppointmentResponse.from_orm(appointment)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking in appointment {appointment_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to check in appointment")

@router.post("/{appointment_id}/start", response_model=AppointmentResponse)
async def start_appointment(
    appointment_id: int,
    appointment_service: AppointmentService = Depends(get_appointment_service)
):
    """Start an appointment"""
    try:
        appointment = appointment_service.start_appointment(appointment_id)
        if not appointment:
            raise HTTPException(status_code=404, detail="Appointment not found")
        
        return AppointmentResponse.from_orm(appointment)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting appointment {appointment_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to start appointment")

@router.post("/{appointment_id}/complete", response_model=AppointmentResponse)
async def complete_appointment(
    appointment_id: int,
    notes: Optional[str] = Query(None),
    appointment_service: AppointmentService = Depends(get_appointment_service)
):
    """Complete an appointment"""
    try:
        appointment = appointment_service.complete_appointment(appointment_id, notes)
        if not appointment:
            raise HTTPException(status_code=404, detail="Appointment not found")
        
        return AppointmentResponse.from_orm(appointment)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error completing appointment {appointment_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to complete appointment")

@router.post("/{appointment_id}/no-show", response_model=AppointmentResponse)
async def mark_no_show(
    appointment_id: int,
    appointment_service: AppointmentService = Depends(get_appointment_service)
):
    """Mark an appointment as no-show"""
    try:
        appointment = appointment_service.mark_no_show(appointment_id)
        if not appointment:
            raise HTTPException(status_code=404, detail="Appointment not found")
        
        return AppointmentResponse.from_orm(appointment)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking no-show {appointment_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to mark appointment as no-show")

@router.get("/today/overview")
async def get_today_overview(
    appointment_service: AppointmentService = Depends(get_appointment_service)
):
    """Get today's appointment overview"""
    try:
        today = date.today()
        appointments = appointment_service.get_appointments_by_date_range(today, today)
        
        # Categorize appointments
        overview = {
            'total': len(appointments),
            'scheduled': len([a for a in appointments if a.status.value == 'scheduled']),
            'confirmed': len([a for a in appointments if a.status.value == 'confirmed']),
            'checked_in': len([a for a in appointments if a.status.value == 'checked_in']),
            'in_progress': len([a for a in appointments if a.status.value == 'in_progress']),
            'completed': len([a for a in appointments if a.status.value == 'completed']),
            'cancelled': len([a for a in appointments if a.status.value == 'cancelled']),
            'no_show': len([a for a in appointments if a.status.value == 'no_show']),
            'appointments': [AppointmentResponse.from_orm(apt) for apt in appointments]
        }
        
        return overview
    except Exception as e:
        logger.error(f"Error getting today's overview: {e}")
        raise HTTPException(status_code=500, detail="Failed to get today's overview")