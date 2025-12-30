from fastapi.testclient import TestClient

from main import app


def test_healthz_ok() -> None:
    client = TestClient(app)
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_ws_health_ok() -> None:
    client = TestClient(app)
    with client.websocket_connect("/ws/health") as ws:
        payload = ws.receive_json()
        assert payload == {"status": "ok"}
