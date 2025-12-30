"""Tests for Brain API chat endpoint using stub provider."""
import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def force_stub_provider(monkeypatch):
    """Force stub provider for all brain tests."""
    monkeypatch.setenv("ECHO_BRAIN_PROVIDER", "stub")


def test_brain_chat_simple() -> None:
    """Test simple chat completion with stub provider."""
    from main import app
    
    client = TestClient(app)
    payload = {
        "messages": [
            {"role": "user", "content": "Hello, Brain!"}
        ]
    }
    
    resp = client.post("/v1/brain/chat", json=payload)
    
    assert resp.status_code == 200
    data = resp.json()
    
    assert "session_id" in data
    assert "message" in data
    assert data["message"]["role"] == "assistant"
    assert "stub" in data["message"]["content"].lower()
    assert "usage" in data
    assert data["usage"]["total_tokens"] == 25


def test_brain_chat_with_session_id() -> None:
    """Test chat with explicit session_id."""
    from main import app
    
    client = TestClient(app)
    session_id = "test-session-123"
    payload = {
        "messages": [
            {"role": "user", "content": "Test message"}
        ],
        "session_id": session_id
    }
    
    resp = client.post("/v1/brain/chat", json=payload)
    
    assert resp.status_code == 200
    data = resp.json()
    assert data["session_id"] == session_id


def test_brain_chat_multiple_messages() -> None:
    """Test chat with conversation history."""
    from main import app
    
    client = TestClient(app)
    payload = {
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hi"},
            {"role": "assistant", "content": "Hello!"},
            {"role": "user", "content": "How are you?"}
        ]
    }
    
    resp = client.post("/v1/brain/chat", json=payload)
    
    assert resp.status_code == 200
    data = resp.json()
    assert "4 messages" in data["message"]["content"]


def test_brain_chat_with_metadata() -> None:
    """Test chat with custom metadata."""
    from main import app
    
    client = TestClient(app)
    payload = {
        "messages": [{"role": "user", "content": "Test"}],
        "metadata": {"user_id": "test-user", "source": "api-test"}
    }
    
    resp = client.post("/v1/brain/chat", json=payload)
    
    assert resp.status_code == 200
    data = resp.json()
    assert data["metadata"]["provider"] == "stub"
