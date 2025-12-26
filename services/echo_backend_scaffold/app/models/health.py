"""Health check models."""

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Health check response."""

    ok: bool
    service: str
    time: str  # ISO8601 timestamp
