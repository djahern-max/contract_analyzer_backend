# schemas/contract.py
"""
Contract-related Pydantic schemas.
"""

from pydantic import BaseModel, validator
from typing import Dict, Any, Optional, List
from .base import BaseResponse, TimestampMixin


class ContractUpload(BaseModel):
    """Schema for contract upload metadata"""

    project_id: int
    description: Optional[str] = None


class ContractDetailResponse(BaseResponse, TimestampMixin):
    """Schema for detailed contract information"""

    id: int
    project_id: int
    file_name: str
    file_url: str
    is_processed: str
    processed_at: Optional[str] = None
    contract_data: Dict[str, Any] = {}


class ContractSummaryResponse(BaseResponse):
    """Schema for contract summary information"""

    id: int
    project_id: int
    file_name: str
    is_processed: str
    created_at: str
    file_size: Optional[int] = None
    file_type: Optional[str] = None


class ContractAnalysisResponse(BaseModel):
    """Schema for contract analysis results"""

    contract_id: int
    analysis: Dict[str, Any]
    success: bool
    message: str
    analysis_date: Optional[str] = None


class ContractQuestionRequest(BaseModel):
    """Schema for asking questions about a contract"""

    question: str
    context: Optional[str] = None

    @validator("question")
    def validate_question(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError("Question cannot be empty")
        if len(v) > 1000:
            raise ValueError("Question cannot exceed 1000 characters")
        return v.strip()


class ContractQuestionResponse(BaseModel):
    """Schema for contract question answers"""

    contract_id: int
    question: str
    answer: str
    confidence: Optional[float] = None
    sources: List[str] = []
    timestamp: str


class ContractComparisonRequest(BaseModel):
    """Schema for comparing multiple contracts"""

    contract_ids: List[int]
    comparison_type: str = "full"
    specific_fields: Optional[List[str]] = None

    @validator("contract_ids")
    def validate_contract_ids(cls, v):
        if not v or len(v) < 2:
            raise ValueError("At least 2 contracts are required for comparison")
        if len(v) > 10:
            raise ValueError("Cannot compare more than 10 contracts at once")
        return v

    @validator("comparison_type")
    def validate_comparison_type(cls, v):
        allowed_types = ["full", "pricing", "terms", "timeline", "custom"]
        if v not in allowed_types:
            raise ValueError(
                f'comparison_type must be one of: {", ".join(allowed_types)}'
            )
        return v


class ContractComparisonResponse(BaseModel):
    """Schema for contract comparison results"""

    contracts: List[ContractSummaryResponse]
    comparison_data: Dict[str, Any]
    differences: List[Dict[str, Any]]
    similarities: List[Dict[str, Any]]
    summary: str


class ContractStatusUpdate(BaseModel):
    """Schema for updating contract processing status"""

    is_processed: str
    contract_data: Optional[Dict[str, Any]] = None

    @validator("is_processed")
    def validate_status(cls, v):
        allowed_statuses = ["pending", "processing", "completed", "failed"]
        if v not in allowed_statuses:
            raise ValueError(
                f'is_processed must be one of: {", ".join(allowed_statuses)}'
            )
        return v


class ContractSearchParams(BaseModel):
    """Schema for contract search parameters"""

    query: Optional[str] = None
    project_id: Optional[int] = None
    status: Optional[str] = None
    file_type: Optional[str] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    page: int = 1
    per_page: int = 10
    sort_by: str = "created_at"
    sort_order: str = "desc"

    @validator("per_page")
    def validate_per_page(cls, v):
        if v < 1 or v > 100:
            raise ValueError("per_page must be between 1 and 100")
        return v

    @validator("status")
    def validate_status(cls, v):
        if v is not None:
            allowed_statuses = ["pending", "processing", "completed", "failed"]
            if v not in allowed_statuses:
                raise ValueError(
                    f'status must be one of: {", ".join(allowed_statuses)}'
                )
        return v

    @validator("sort_by")
    def validate_sort_by(cls, v):
        allowed_fields = ["file_name", "created_at", "updated_at", "is_processed"]
        if v not in allowed_fields:
            raise ValueError(f'sort_by must be one of: {", ".join(allowed_fields)}')
        return v

    @validator("sort_order")
    def validate_sort_order(cls, v):
        if v.lower() not in ["asc", "desc"]:
            raise ValueError('sort_order must be "asc" or "desc"')
        return v.lower()
