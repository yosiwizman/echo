"""Tests for Brain API streaming endpoint using stub provider."""
import json
import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def force_stub_provider(monkeypatch):
    """Force stub provider for all brain tests."""
    monkeypatch.setenv("ECHO_BRAIN_PROVIDER", "stub")


def test_brain_stream_format() -> None:
    """Test streaming response format (SSE)."""
    from main import app
    
    client = TestClient(app)
    payload = {
        "messages": [{"role": "user", "content": "Stream test"}]
    }
    
    with client.stream("POST", "/v1/brain/chat/stream", json=payload) as resp:
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "text/event-stream; charset=utf-8"
        
        # Collect all events
        events = []
        for line in resp.iter_lines():
            if line.startswith("event:"):
                event_type = line.split(":", 1)[1].strip()
            elif line.startswith("data:"):
                data_json = line.split(":", 1)[1].strip()
                data = json.loads(data_json)
                events.append({"type": event_type, "data": data})
        
        # Should have token events + final event
        assert len(events) > 0
        
        # Last event should be 'final'
        final_event = events[-1]
        assert final_event["type"] == "final"
        assert "message" in final_event["data"]
        assert final_event["data"]["message"]["role"] == "assistant"
        
        # Final event should include runtime metadata
        assert final_event["data"]["ok"] is True
        assert "runtime" in final_event["data"]
        runtime = final_event["data"]["runtime"]
        assert "trace_id" in runtime
        assert len(runtime["trace_id"]) == 36  # UUID format
        assert runtime["provider"] == "stub"
        assert "env" in runtime
        assert "git_sha" in runtime
        assert "build_time" in runtime


def test_brain_stream_tokens() -> None:
    """Test streaming emits token events."""
    from main import app
    
    client = TestClient(app)
    payload = {
        "messages": [{"role": "user", "content": "Token test"}]
    }
    
    with client.stream("POST", "/v1/brain/chat/stream", json=payload) as resp:
        assert resp.status_code == 200
        
        token_events = []
        final_event = None
        
        current_event = None
        for line in resp.iter_lines():
            if line.startswith("event:"):
                current_event = line.split(":", 1)[1].strip()
            elif line.startswith("data:") and current_event:
                data_json = line.split(":", 1)[1].strip()
                data = json.loads(data_json)
                
                if current_event == "token":
                    token_events.append(data)
                elif current_event == "final":
                    final_event = data
        
        # Should have multiple token events
        assert len(token_events) > 1
        
        # Each token event should have token and session_id
        for token_event in token_events:
            assert "token" in token_event
            assert "session_id" in token_event
        
        # Should have final event
        assert final_event is not None
        assert "message" in final_event
        assert "session_id" in final_event


def test_brain_stream_session_id() -> None:
    """Test streaming maintains session_id."""
    from main import app
    
    client = TestClient(app)
    session_id = "stream-session-456"
    payload = {
        "messages": [{"role": "user", "content": "Session test"}],
        "session_id": session_id
    }
    
    with client.stream("POST", "/v1/brain/chat/stream", json=payload) as resp:
        assert resp.status_code == 200
        
        for line in resp.iter_lines():
            if line.startswith("data:"):
                data_json = line.split(":", 1)[1].strip()
                data = json.loads(data_json)
                
                if "session_id" in data:
                    assert data["session_id"] == session_id
