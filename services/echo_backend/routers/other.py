import os

from fastapi import APIRouter
from fastapi.websockets import WebSocket

router = APIRouter()


@router.get("/")
async def root():
    """Root endpoint with service information.
    
    Returns helpful JSON instead of 404 for users who visit the base URL.
    """
    env = os.environ.get("ECHO_ENV", "unknown")
    return {
        "service": "echo-backend",
        "env": env,
        "status": "ok",
        "endpoints": [
            "GET /health",
            "GET /docs",
        ]
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
