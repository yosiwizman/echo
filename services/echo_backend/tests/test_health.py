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


# --------------------------------------------------------------------------
# Alert Self-Test Endpoint Tests
# --------------------------------------------------------------------------

def test_ops_alert_test_missing_header_returns_403() -> None:
    """Test that GET /ops/alert-test returns 403 when X-Alert-Test-Token header is missing."""
    import routers.other as other_module
    
    # Temporarily set the token so we can test auth
    original_token = other_module._ALERT_TEST_TOKEN
    other_module._ALERT_TEST_TOKEN = "test-secret-token"
    
    try:
        client = TestClient(app)
        resp = client.get("/ops/alert-test")
        assert resp.status_code == 403
        assert "Invalid or missing" in resp.json()["detail"]
    finally:
        other_module._ALERT_TEST_TOKEN = original_token


def test_ops_alert_test_wrong_token_returns_403() -> None:
    """Test that GET /ops/alert-test returns 403 when X-Alert-Test-Token is wrong."""
    import routers.other as other_module
    
    original_token = other_module._ALERT_TEST_TOKEN
    other_module._ALERT_TEST_TOKEN = "correct-token"
    
    try:
        client = TestClient(app)
        resp = client.get("/ops/alert-test", headers={"X-Alert-Test-Token": "wrong-token"})
        assert resp.status_code == 403
        assert "Invalid or missing" in resp.json()["detail"]
    finally:
        other_module._ALERT_TEST_TOKEN = original_token


def test_ops_alert_test_correct_token_returns_200() -> None:
    """Test that GET /ops/alert-test returns 200 with correct token and logs message."""
    import routers.other as other_module
    
    original_token = other_module._ALERT_TEST_TOKEN
    other_module._ALERT_TEST_TOKEN = "correct-token"
    
    try:
        client = TestClient(app)
        resp = client.get("/ops/alert-test", headers={"X-Alert-Test-Token": "correct-token"})
        assert resp.status_code == 200
        assert resp.json() == {"ok": True}
    finally:
        other_module._ALERT_TEST_TOKEN = original_token


def test_ops_alert_test_unconfigured_token_returns_500() -> None:
    """Test that GET /ops/alert-test returns 500 when ALERT_TEST_TOKEN is not configured."""
    import routers.other as other_module
    
    original_token = other_module._ALERT_TEST_TOKEN
    other_module._ALERT_TEST_TOKEN = ""  # Simulate unconfigured
    
    try:
        client = TestClient(app)
        resp = client.get("/ops/alert-test", headers={"X-Alert-Test-Token": "any-token"})
        assert resp.status_code == 500
        assert "not configured" in resp.json()["detail"]
    finally:
        other_module._ALERT_TEST_TOKEN = original_token
