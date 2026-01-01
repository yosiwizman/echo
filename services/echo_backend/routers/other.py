import os

from fastapi import APIRouter
from fastapi.websockets import WebSocket

router = APIRouter()

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
