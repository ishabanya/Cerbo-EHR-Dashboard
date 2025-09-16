from pydantic import BaseModel
from typing import List, Optional, Any, Generic, TypeVar
from datetime import datetime

T = TypeVar('T')

class BaseSchema(BaseModel):
    """Base schema with common configuration"""
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response schema"""
    items: List[T]
    total: int
    page: int
    pages: int
    per_page: int
    has_next: bool
    has_prev: bool

class ErrorResponse(BaseModel):
    """Error response schema"""
    error: str
    status_code: int
    path: Optional[str] = None
    details: Optional[dict] = None

class SuccessResponse(BaseModel):
    """Success response schema"""
    message: str
    data: Optional[Any] = None

class SearchParams(BaseModel):
    """Common search parameters"""
    q: Optional[str] = None
    page: int = 1
    per_page: int = 50
    sort_by: Optional[str] = None
    sort_order: str = "asc"

class DateRangeFilter(BaseModel):
    """Date range filter"""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None