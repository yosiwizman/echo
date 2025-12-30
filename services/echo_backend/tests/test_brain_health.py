"""Tests for Brain API health endpoint."""
import os
import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def force_stub_provider(monkeypatch):
    """Force stub provider for all brain tests."""
    monkeypatch.setenv("ECHO_BRAIN_PROVIDER", "stub")


def test_brain_health_ok() -> None:
    """Test brain health endpoint returns ok status."""
    # Import after env var is set
    from main import app
    
    client = TestClient(app)
    resp = client.get("/v1/brain/health")
    
    assert resp.status_code == 200
    data = resp.json()
    
    assert data["ok"] is True
    assert "time" in data
    assert data["version"] == "1.0.0"
    assert data["provider"] == "stub"


def test_brain_health_provider_name() -> None:
    """Test health endpoint reflects active provider."""
    from main import app
    
    client = TestClient(app)
    resp = client.get("/v1/brain/health")
    
    assert resp.status_code == 200
    data = resp.json()
    assert data["provider"] in ["stub", "openai"]
