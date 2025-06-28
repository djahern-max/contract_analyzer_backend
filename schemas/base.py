# schemas/base.py
"""
Base Pydantic schemas that are shared across the application.
"""

from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime


class BaseResponse(BaseModel):
    """Base response schema with common fields"""

    class Config:
        from_attributes = True


class SuccessResponse(BaseModel):
    """Standard success response"""

    success: bool = True
    message: str
    data: Optional[Any] = None


class ErrorResponse(BaseModel):
    """Standard error response"""

    success: bool = False
    message: str
    error_code: Optional[str] = None
    details: Optional[dict] = None


class PaginationResponse(BaseModel):
    """Pagination metadata"""

    page: int
    per_page: int
    total: int
    pages: int
    has_next: bool
    has_prev: bool


class TimestampMixin(BaseModel):
    """Mixin for models with timestamps"""

    created_at: str
    updated_at: Optional[str] = None
