"""Standardized API Response Wrappers."""

from typing import Any, Generic, Optional, TypeVar
from pydantic import BaseModel, Field

DataT = TypeVar("DataT")


class ErrorDetail(BaseModel):
    """Structured error detail representation."""

    code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable safe error message")
    details: Optional[Any] = Field(None, description="Optional safe contextual details")


class ErrorResponse(BaseModel):
    """Standardized error response body."""

    success: bool = False
    error: ErrorDetail


class SuccessResponse(BaseModel, Generic[DataT]):
    """Standardized success response body."""

    success: bool = True
    data: DataT
    message: Optional[str] = None
