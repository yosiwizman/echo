"""Tests for Brain API TTS endpoint using stub provider."""
import base64
import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def force_stub_provider(monkeypatch):
    """Force stub provider for all voice tests."""
    monkeypatch.setenv("ECHO_VOICE_PROVIDER", "stub")
    # Reset cached provider instance
    from utils.brain.voice_provider import reset_voice_provider
    reset_voice_provider()
    yield
    reset_voice_provider()


def test_brain_tts_simple() -> None:
    """Test simple TTS synthesis with stub provider."""
    from main import app
    
    client = TestClient(app)
    payload = {"text": "Hello, this is a test message."}
    
    resp = client.post("/v1/brain/tts", json=payload)
    
    assert resp.status_code == 200
    data = resp.json()
    
    # Core response fields
    assert data["ok"] is True
    assert "audio_base64" in data
    assert len(data["audio_base64"]) > 0
    assert "mime_type" in data
    assert data["mime_type"] == "audio/mpeg"  # Default MP3
    
    # Verify base64 is valid
    try:
        decoded = base64.b64decode(data["audio_base64"])
        assert len(decoded) > 0
    except Exception as e:
        pytest.fail(f"Invalid base64: {e}")
    
    # Runtime metadata fields
    assert "runtime" in data
    runtime = data["runtime"]
    assert "trace_id" in runtime
    assert len(runtime["trace_id"]) == 36  # UUID format
    assert runtime["provider"] == "stub"
    assert "env" in runtime
    assert "git_sha" in runtime
    assert "build_time" in runtime


def test_brain_tts_with_voice() -> None:
    """Test TTS with custom voice parameter."""
    from main import app
    
    client = TestClient(app)
    payload = {
        "text": "Testing with custom voice.",
        "voice": "echo"
    }
    
    resp = client.post("/v1/brain/tts", json=payload)
    
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True


def test_brain_tts_with_format() -> None:
    """Test TTS with custom format parameter."""
    from main import app
    
    client = TestClient(app)
    payload = {
        "text": "Testing with opus format.",
        "format": "opus"
    }
    
    resp = client.post("/v1/brain/tts", json=payload)
    
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert data["mime_type"] == "audio/opus"


def test_brain_tts_with_all_options() -> None:
    """Test TTS with all optional parameters."""
    from main import app
    
    client = TestClient(app)
    payload = {
        "text": "Full options test.",
        "voice": "nova",
        "format": "wav"
    }
    
    resp = client.post("/v1/brain/tts", json=payload)
    
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert data["mime_type"] == "audio/wav"


def test_brain_tts_empty_text() -> None:
    """Test TTS rejects empty text."""
    from main import app
    
    client = TestClient(app)
    payload = {"text": ""}
    
    resp = client.post("/v1/brain/tts", json=payload)
    
    # Pydantic validation should reject this (min_length=1)
    assert resp.status_code == 422


def test_brain_tts_missing_text() -> None:
    """Test TTS requires text parameter."""
    from main import app
    
    client = TestClient(app)
    payload = {}
    
    resp = client.post("/v1/brain/tts", json=payload)
    
    assert resp.status_code == 422  # Validation error


def test_brain_tts_long_text() -> None:
    """Test TTS handles reasonably long text."""
    from main import app
    
    client = TestClient(app)
    # Create text near the limit (but under 4096)
    long_text = "Hello world. " * 300  # ~3900 chars
    payload = {"text": long_text}
    
    resp = client.post("/v1/brain/tts", json=payload)
    
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True


def test_brain_tts_text_too_long() -> None:
    """Test TTS rejects text exceeding max length."""
    from main import app
    
    client = TestClient(app)
    # Create text over the limit (>4096)
    too_long_text = "A" * 5000
    payload = {"text": too_long_text}
    
    resp = client.post("/v1/brain/tts", json=payload)
    
    # Pydantic validation should reject this (max_length=4096)
    assert resp.status_code == 422


def test_brain_tts_auth_required(monkeypatch) -> None:
    """Test TTS requires authentication when AUTH_REQUIRED=true."""
    monkeypatch.setenv("AUTH_REQUIRED", "true")
    monkeypatch.setenv("AUTH_JWT_SECRET", "test-secret-key-minimum-32-chars!")
    monkeypatch.setenv("AUTH_PIN_HASH", "$2b$12$test")
    
    from main import app
    
    client = TestClient(app)
    payload = {"text": "Test authentication."}
    
    resp = client.post("/v1/brain/tts", json=payload)
    
    assert resp.status_code == 401
    data = resp.json()
    detail = data["detail"]
    assert detail["ok"] is False
    assert detail["error"]["code"] == "auth_required"
