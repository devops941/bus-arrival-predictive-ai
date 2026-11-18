"""
BusArrival AI - API Pydantic Schemas
Defines request/response models and standardized error formats.
Errors adhere to: { "detail": str, "code": str, "fields": Optional[dict] }
"""

from datetime import datetime
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, EmailStr, Field, AliasChoices


# Standard Error Model
class ErrorResponse(BaseModel):
    detail: str
    code: str = "VALIDATION_ERROR"
    fields: Optional[Dict[str, Any]] = None


# Health Schemas
class HealthResponse(BaseModel):
    status: str
    database: str
    app_env: str
    version: str = "1.0.0"
    timestamp: datetime


# Authentication & User Schemas
RoleType = Literal["passenger", "analyst", "admin"]


class UserRegisterRequest(BaseModel):
    email: str = Field(..., pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$", description="Valid email address")
    password: str = Field(..., min_length=8, description="Minimum 8 characters")
    full_name: Optional[str] = None
    role: RoleType = "passenger"


class UserLoginRequest(BaseModel):
    email: str = Field(..., validation_alias=AliasChoices("email", "username"), pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$", description="Valid email address")
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in_minutes: int
    user_id: str
    email: str
    role: str
    full_name: Optional[str] = None


class TokenRefreshRequest(BaseModel):
    refresh_token: str


class TokenRefreshResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_minutes: int


class UserResponse(BaseModel):
    id: str
    email: str
    role: str
    full_name: Optional[str] = None
    is_active: bool
    failed_login_attempts: int = 0
    locked_until: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class PasswordChangeRequest(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=8)


class AdminResetPasswordRequest(BaseModel):
    user_id: str
    new_password: str = Field(..., min_length=8)


# Audit Log Schemas
class AuditLogResponse(BaseModel):
    id: str
    timestamp: datetime
    action: str
    entity_type: str
    entity_id: Optional[str] = None
    user_id: Optional[str] = None
    user_email: str
    details: Dict[str, Any] = {}
    ip_address: Optional[str] = None
