from fastapi import APIRouter
from fastapi.websockets import WebSocket

router = APIRouter()


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
