# schemas/project.py
"""
Project-related Pydantic schemas.
"""

from pydantic import BaseModel, validator
from typing import List, Optional
from .base import BaseResponse, TimestampMixin


class ProjectCreate(BaseModel):
    """Schema for creating a new project"""

    name: str
    description: Optional[str] = None
    job_number: Optional[str] = None

    @validator("name")
    def validate_name(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError("Project name cannot be empty")
        if len(v) > 255:
            raise ValueError("Project name cannot exceed 255 characters")
        return v.strip()

    @validator("job_number")
    def validate_job_number(cls, v):
        if v and len(v) > 50:
            raise ValueError("Job number cannot exceed 50 characters")
        return v.strip() if v else v


class ProjectUpdate(BaseModel):
    """Schema for updating a project"""

    name: Optional[str] = None
    description: Optional[str] = None
    job_number: Optional[str] = None

    @validator("name")
    def validate_name(cls, v):
        if v is not None:
            if not v or len(v.strip()) == 0:
                raise ValueError("Project name cannot be empty")
            if len(v) > 255:
                raise ValueError("Project name cannot exceed 255 characters")
            return v.strip()
        return v

    @validator("job_number")
    def validate_job_number(cls, v):
        if v is not None:
            if len(v) > 50:
                raise ValueError("Job number cannot exceed 50 characters")
            return v.strip() if v else v
        return v


class ContractSummary(BaseModel):
    """Summary schema for contracts within project responses"""

    id: int
    file_name: str
    is_processed: str
    created_at: str

    class Config:
        from_attributes = True


class ProjectResponse(BaseResponse, TimestampMixin):
    """Schema for project information in responses"""

    id: int
    name: str
    description: Optional[str] = None
    job_number: Optional[str] = None
    contract_count: int = 0
    contracts: List[ContractSummary] = []


class ProjectListResponse(BaseModel):
    """Schema for paginated project lists"""

    projects: List[ProjectResponse]
    total: int
    page: int = 1
    per_page: int = 10
    has_next: bool = False
    has_prev: bool = False


class ProjectSearchParams(BaseModel):
    """Schema for project search parameters"""

    query: Optional[str] = None
    job_number: Optional[str] = None
    page: int = 1
    per_page: int = 10
    sort_by: str = "created_at"
    sort_order: str = "desc"

    @validator("per_page")
    def validate_per_page(cls, v):
        if v < 1 or v > 100:
            raise ValueError("per_page must be between 1 and 100")
        return v

    @validator("sort_by")
    def validate_sort_by(cls, v):
        allowed_fields = ["name", "created_at", "updated_at", "job_number"]
        if v not in allowed_fields:
            raise ValueError(f'sort_by must be one of: {", ".join(allowed_fields)}')
        return v

    @validator("sort_order")
    def validate_sort_order(cls, v):
        if v.lower() not in ["asc", "desc"]:
            raise ValueError('sort_order must be "asc" or "desc"')
        return v.lower()
