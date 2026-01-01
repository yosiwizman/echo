from fastapi.testclient import TestClient

from main import app


def test_root_returns_service_info() -> None:
    """Test that GET / returns 200 and service info JSON with metadata."""
    client = TestClient(app)
    resp = client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["service"] == "echo-backend"
    assert data["status"] == "ok"
    assert "env" in data
    assert "git_sha" in data
    assert "build_time" in data
    assert "endpoints" in data
    assert isinstance(data["endpoints"], list)


def test_version_returns_metadata() -> None:
    """Test that GET /version returns 200 with build metadata."""
    client = TestClient(app)
    resp = client.get("/version")
    assert resp.status_code == 200
    data = resp.json()
    assert "env" in data
    assert "git_sha" in data
    assert "build_time" in data


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
