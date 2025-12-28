"""Health check endpoint."""

from datetime import UTC, datetime

from fastapi import APIRouter

from app.models.health import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/healthz", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint.

    Returns service status and current time in ISO8601 format.
    """
    return HealthResponse(
        ok=True,
        service="echo-backend",
        time=datetime.now(UTC).isoformat(),
    )
