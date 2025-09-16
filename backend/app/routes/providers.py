from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
import logging

from ..utils.database import get_db
from ..services.provider_service import ProviderService
from ..schemas.provider import (
    ProviderCreate, ProviderUpdate, ProviderResponse, ProviderSearch
)
from ..schemas.common import PaginatedResponse, SuccessResponse

logger = logging.getLogger(__name__)

router = APIRouter()

def get_provider_service(db: Session = Depends(get_db)) -> ProviderService:
    """Dependency to get provider service"""
    return ProviderService(db)

@router.get("/", response_model=PaginatedResponse[ProviderResponse])
async def get_providers(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    search: Optional[str] = Query(None),
    provider_type: Optional[str] = Query(None),
    specialty: Optional[str] = Query(None),
    status: Optional[str] = Query("active"),
    provider_service: ProviderService = Depends(get_provider_service)
):
    """Get all providers with pagination and filtering"""
    try:
        skip = (page - 1) * per_page
        
        if search:
            providers = provider_service.search_providers(
                search_term=search,
                provider_type=provider_type,
                specialty=specialty,
                status=status,
                skip=skip,
                limit=per_page
            )
        else:
            filters = {}
            if provider_type:
                filters['provider_type'] = provider_type
            if specialty:
                filters['specialties'] = {'like': specialty}
            if status:
                filters['status'] = status
            
            providers = provider_service.get_by_fields(filters) if filters else provider_service.get_all(skip=skip, limit=per_page)
        
        total = provider_service.count({"status": status} if status else {})
        pages = (total + per_page - 1) // per_page
        
        return PaginatedResponse(
            items=[ProviderResponse.from_orm(provider) for provider in providers],
            total=total,
            page=page,
            pages=pages,
            per_page=per_page,
            has_next=page < pages,
            has_prev=page > 1
        )
    except Exception as e:
        logger.error(f"Error getting providers: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve providers")

@router.post("/", response_model=ProviderResponse, status_code=201)
async def create_provider(
    provider_data: ProviderCreate,
    provider_service: ProviderService = Depends(get_provider_service)
):
    """Create a new provider"""
    try:
        provider = provider_service.create(provider_data.dict())
        return ProviderResponse.from_orm(provider)
    except Exception as e:
        logger.error(f"Error creating provider: {e}")
        raise HTTPException(status_code=500, detail="Failed to create provider")

@router.get("/{provider_id}", response_model=ProviderResponse)
async def get_provider(
    provider_id: int,
    provider_service: ProviderService = Depends(get_provider_service)
):
    """Get a specific provider by ID"""
    try:
        provider = provider_service.get_by_id(provider_id)
        if not provider:
            raise HTTPException(status_code=404, detail="Provider not found")
        return ProviderResponse.from_orm(provider)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting provider {provider_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve provider")

@router.put("/{provider_id}", response_model=ProviderResponse)
async def update_provider(
    provider_id: int,
    provider_data: ProviderUpdate,
    provider_service: ProviderService = Depends(get_provider_service)
):
    """Update a provider"""
    try:
        update_data = {k: v for k, v in provider_data.dict().items() if v is not None}
        provider = provider_service.update(provider_id, update_data)
        
        if not provider:
            raise HTTPException(status_code=404, detail="Provider not found")
        
        return ProviderResponse.from_orm(provider)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating provider {provider_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update provider")

@router.get("/specialty/{specialty}")
async def get_providers_by_specialty(
    specialty: str,
    provider_service: ProviderService = Depends(get_provider_service)
):
    """Get providers by specialty"""
    try:
        providers = provider_service.get_providers_by_specialty(specialty)
        return [ProviderResponse.from_orm(provider) for provider in providers]
    except Exception as e:
        logger.error(f"Error getting providers by specialty: {e}")
        raise HTTPException(status_code=500, detail="Failed to get providers by specialty")

@router.get("/{provider_id}/schedule")
async def get_provider_schedule(
    provider_id: int,
    start_date: date = Query(...),
    end_date: date = Query(...),
    provider_service: ProviderService = Depends(get_provider_service)
):
    """Get provider schedule for date range"""
    try:
        schedule = provider_service.get_provider_schedule(provider_id, start_date, end_date)
        return {"schedule": schedule}
    except Exception as e:
        logger.error(f"Error getting provider schedule: {e}")
        raise HTTPException(status_code=500, detail="Failed to get provider schedule")

@router.get("/{provider_id}/availability")
async def get_provider_availability(
    provider_id: int,
    start_date: date = Query(...),
    end_date: date = Query(...),
    provider_service: ProviderService = Depends(get_provider_service)
):
    """Get provider availability"""
    try:
        availability = provider_service.get_provider_availability(provider_id, start_date, end_date)
        return {"availability": availability}
    except Exception as e:
        logger.error(f"Error getting provider availability: {e}")
        raise HTTPException(status_code=500, detail="Failed to get provider availability")

@router.get("/{provider_id}/workload")
async def get_provider_workload(
    provider_id: int,
    start_date: date = Query(...),
    end_date: date = Query(...),
    provider_service: ProviderService = Depends(get_provider_service)
):
    """Get provider workload statistics"""
    try:
        workload = provider_service.get_provider_workload(provider_id, start_date, end_date)
        return workload
    except Exception as e:
        logger.error(f"Error getting provider workload: {e}")
        raise HTTPException(status_code=500, detail="Failed to get provider workload")