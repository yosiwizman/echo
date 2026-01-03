"""Tests for Brain API STT endpoint using stub provider."""
import io
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


def test_brain_stt_simple() -> None:
    """Test simple STT transcription with stub provider."""
    from main import app
    
    client = TestClient(app)
    
    # Create a fake audio file
    audio_content = b"fake audio content for testing"
    files = {"file": ("test.webm", io.BytesIO(audio_content), "audio/webm")}
    
    resp = client.post("/v1/brain/stt", files=files)
    
    assert resp.status_code == 200
    data = resp.json()
    
    # Core response fields
    assert data["ok"] is True
    assert "text" in data
    assert "stub" in data["text"].lower()
    assert str(len(audio_content)) in data["text"]  # Should mention byte count
    
    # Duration should be present
    assert "duration_seconds" in data
    assert data["duration_seconds"] is not None
    
    # Runtime metadata fields
    assert "runtime" in data
    runtime = data["runtime"]
    assert "trace_id" in runtime
    assert len(runtime["trace_id"]) == 36  # UUID format
    assert runtime["provider"] == "stub"
    assert "env" in runtime
    assert "git_sha" in runtime
    assert "build_time" in runtime


def test_brain_stt_wav_format() -> None:
    """Test STT with WAV audio format."""
    from main import app
    
    client = TestClient(app)
    
    audio_content = b"RIFF" + b"\x00" * 100  # Fake WAV header
    files = {"file": ("recording.wav", io.BytesIO(audio_content), "audio/wav")}
    
    resp = client.post("/v1/brain/stt", files=files)
    
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True
    assert "text" in data


def test_brain_stt_mp3_format() -> None:
    """Test STT with MP3 audio format."""
    from main import app
    
    client = TestClient(app)
    
    audio_content = b"\xff\xfb\x90\x00" + b"\x00" * 100  # Fake MP3 header
    files = {"file": ("recording.mp3", io.BytesIO(audio_content), "audio/mpeg")}
    
    resp = client.post("/v1/brain/stt", files=files)
    
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True


def test_brain_stt_invalid_format() -> None:
    """Test STT rejects invalid audio format."""
    from main import app
    
    client = TestClient(app)
    
    files = {"file": ("test.txt", io.BytesIO(b"not audio"), "text/plain")}
    
    resp = client.post("/v1/brain/stt", files=files)
    
    assert resp.status_code == 400
    data = resp.json()
    detail = data["detail"]
    assert detail["ok"] is False
    assert detail["error"]["code"] == "invalid_audio_format"
    assert "runtime" in detail


def test_brain_stt_empty_file() -> None:
    """Test STT rejects empty audio file."""
    from main import app
    
    client = TestClient(app)
    
    files = {"file": ("empty.webm", io.BytesIO(b""), "audio/webm")}
    
    resp = client.post("/v1/brain/stt", files=files)
    
    assert resp.status_code == 400
    data = resp.json()
    detail = data["detail"]
    assert detail["ok"] is False
    assert detail["error"]["code"] == "empty_file"


def test_brain_stt_missing_file() -> None:
    """Test STT requires file parameter."""
    from main import app
    
    client = TestClient(app)
    
    resp = client.post("/v1/brain/stt")
    
    assert resp.status_code == 422  # Validation error


def test_brain_stt_auth_required(monkeypatch) -> None:
    """Test STT requires authentication when AUTH_REQUIRED=true."""
    # Clear settings cache before setting new values
    from utils.auth.settings import get_auth_settings
    get_auth_settings.cache_clear()
    
    monkeypatch.setenv("AUTH_REQUIRED", "true")
    monkeypatch.setenv("AUTH_JWT_SECRET", "test-secret-key-minimum-32-chars!")
    monkeypatch.setenv("AUTH_PIN_HASH", "$2b$12$test")
    
    # Clear again after setting new values to force reload
    get_auth_settings.cache_clear()
    
    from main import app
    
    client = TestClient(app)
    
    audio_content = b"test audio"
    files = {"file": ("test.webm", io.BytesIO(audio_content), "audio/webm")}
    
    resp = client.post("/v1/brain/stt", files=files)
    
    # Restore settings cache
    get_auth_settings.cache_clear()
    
    assert resp.status_code == 401
    data = resp.json()
    detail = data["detail"]
    assert detail["ok"] is False
    assert detail["error"]["code"] == "auth_required"
