"""
Data models for event-router.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, validator


class RequestModel(BaseModel):
    """Request model for incoming data."""
    
    id: Optional[str] = Field(None, description="Request ID")
    data: Dict[str, Any] = Field(..., description="Request data")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    @validator('data')
    def validate_data(cls, v):
        """Validate request data."""
        if not v:
            raise ValueError("Data cannot be empty")
        return v


class ResponseModel(BaseModel):
    """Response model for outgoing data."""
    
    success: bool = Field(..., description="Operation success status")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data")
    message: Optional[str] = Field(None, description="Response message")
    errors: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ValidationResult(BaseModel):
    """Validation result model."""
    
    is_valid: bool = Field(..., description="Validation status")
    error: Optional[str] = Field(None, description="Validation error message")
    warnings: List[str] = Field(default_factory=list)


class StateModel(BaseModel):
    """State model for tracking."""
    
    id: str = Field(..., description="State ID")
    status: str = Field(..., description="Current status")
    data: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    def update(self, **kwargs):
        """Update state with new data."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.utcnow()
