"""Common response models for consistent API responses."""

from typing import Any, Dict, Generic, Optional, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")

class BaseResponse(BaseModel, Generic[T]):
    """Base response model with optional data and metadata."""

    success: bool = Field(True, description="Whether the operation was successful")
    message: Optional[str] = Field(None, description="Optional message")
    data: Optional[T] = Field(None, description="Response data")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Optional metadata")

class SuccessResponse(BaseResponse[T]):
    """Success response model."""

    success: bool = Field(True, description="Operation was successful")

class ErrorResponse(BaseModel):
    """Error response model."""

    success: bool = Field(False, description="Operation failed")
    error: str = Field(description="Error message")
    error_type: Optional[str] = Field(None, description="Error type")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")

class MessageResponse(BaseModel):
    """Simple message response."""

    message: str = Field(description="Response message")

class CreatedResponse(BaseResponse[T]):
    """Response for successful creation operations."""

    success: bool = Field(True, description="Resource created successfully")
    message: str = Field("Resource created successfully", description="Success message")

class UpdatedResponse(BaseResponse[T]):
    """Response for successful update operations."""

    success: bool = Field(True, description="Resource updated successfully")
    message: str = Field("Resource updated successfully", description="Success message")

class DeletedResponse(BaseModel):
    """Response for successful delete operations."""

    success: bool = Field(True, description="Resource deleted successfully")
    message: str = Field("Resource deleted successfully", description="Success message")
