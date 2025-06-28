# schemas/__init__.py
"""
Pydantic schemas for the contract analyzer application.
"""

# Import all schemas to make them available at package level
from .base import BaseResponse, SuccessResponse, ErrorResponse, TimestampMixin
from .auth import UserCreate, UserResponse, UserLogin, Token, TokenData
from .project import ProjectCreate, ProjectUpdate, ProjectResponse, ContractSummary
from .contract import (
    ContractDetailResponse,
    ContractAnalysisResponse,
    ContractSummaryResponse,
    ContractQuestionRequest,
    ContractQuestionResponse,
    ContractSearchParams,
    ContractStatusUpdate,
)

__all__ = [
    # Base schemas
    "BaseResponse",
    "SuccessResponse",
    "ErrorResponse",
    "TimestampMixin",
    # Auth schemas
    "UserCreate",
    "UserResponse",
    "UserLogin",
    "Token",
    "TokenData",
    # Project schemas
    "ProjectCreate",
    "ProjectUpdate",
    "ProjectResponse",
    "ContractSummary",
    # Contract schemas
    "ContractDetailResponse",
    "ContractAnalysisResponse",
    "ContractSummaryResponse",
    "ContractQuestionRequest",
    "ContractQuestionResponse",
    "ContractSearchParams",
    "ContractStatusUpdate",
]
