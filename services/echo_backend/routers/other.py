import logging
import os

from fastapi import APIRouter, Header, HTTPException
from fastapi.websockets import WebSocket

logger = logging.getLogger(__name__)

router = APIRouter()

# Alert self-test token (set via Cloud Run secret mount from Secret Manager)
_ALERT_TEST_TOKEN = os.environ.get("ALERT_TEST_TOKEN", "")

# Runtime metadata (set via Cloud Run env vars at deploy time)
_APP_ENV = os.environ.get("APP_ENV", "unknown")
_GIT_SHA = os.environ.get("GIT_SHA", "unknown")
_BUILD_TIME = os.environ.get("BUILD_TIME", "unknown")


@router.get("/")
async def root():
    """Root endpoint with service information.
    
    Returns helpful JSON instead of 404 for users who visit the base URL.
    Includes runtime metadata set at deploy time.
    """
    return {
        "service": "echo-backend",
        "env": _APP_ENV,
        "git_sha": _GIT_SHA,
        "build_time": _BUILD_TIME,
        "status": "ok",
        "endpoints": [
            "GET /health",
            "GET /version",
            "GET /docs",
        ]
    }


@router.get("/version")
async def version():
    """Version endpoint with build metadata.
    
    Returns environment, git SHA, and build timestamp.
    """
    return {
        "env": _APP_ENV,
        "git_sha": _GIT_SHA,
        "build_time": _BUILD_TIME,
    }


@router.api_route("/healthz", methods=["GET", "HEAD"])
@router.api_route("/health", methods=["GET", "HEAD"])
@router.api_route("/v1/health", methods=["GET", "HEAD"])
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


@router.websocket("/ws/health")
async def ws_health(websocket: WebSocket):
    """WebSocket health check endpoint (no auth)."""
    await websocket.accept()
    await websocket.send_json({"status": "ok"})
    await websocket.close()


@router.get("/ops/alert-test")
async def ops_alert_test(x_alert_test_token: str = Header(None)):
    """Alert self-test endpoint.
    
    Triggers a unique log line that fires a log-based metric alert.
    Protected by X-Alert-Test-Token header (must match ALERT_TEST_TOKEN env var).
    
    Used to verify end-to-end alerting pipeline without causing real downtime.
    """
    # Validate token is configured
    if not _ALERT_TEST_TOKEN:
        raise HTTPException(
            status_code=500,
            detail="ALERT_TEST_TOKEN not configured on server"
        )
    
    # Validate provided token
    if not x_alert_test_token or x_alert_test_token != _ALERT_TEST_TOKEN:
        raise HTTPException(
            status_code=403,
            detail="Invalid or missing X-Alert-Test-Token header"
        )
    
    # Log the unique string that triggers the log-based metric
    logger.error("ECHO_ALERT_TEST_TRIGGERED")
    
    return {"ok": True}
