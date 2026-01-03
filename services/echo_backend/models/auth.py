"""Auth models for PIN login and JWT authentication."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from models.brain import RuntimeMetadata


class LoginRequest(BaseModel):
    """Request for PIN login."""
    pin: str = Field(description="The PIN to authenticate with", min_length=1)


class LoginResponse(BaseModel):
    """Successful login response with JWT token."""
    ok: bool = Field(default=True, description="Request success status")
    token: str = Field(description="JWT bearer token")
    expires_at: datetime = Field(description="Token expiration time (ISO 8601)")
    runtime: Optional[RuntimeMetadata] = Field(default=None, description="Runtime metadata for observability")


class AuthErrorInfo(BaseModel):
    """Structured auth error information."""
    code: str = Field(description="Error code (e.g. 'invalid_pin', 'rate_limit')")
    message: str = Field(description="Human-readable error message")
    retry_after: Optional[int] = Field(default=None, description="Seconds until retry (for rate limit)")


class AuthErrorResponse(BaseModel):
    """Error response from auth endpoints."""
    ok: bool = Field(default=False, description="Always false for errors")
    error: AuthErrorInfo = Field(description="Error details")
    runtime: Optional[RuntimeMetadata] = Field(default=None, description="Runtime metadata for observability")
