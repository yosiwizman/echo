"""Chat endpoint tests."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_chat_stub_response(client: AsyncClient) -> None:
    """Test chat endpoint returns deterministic stub response."""
    response = await client.post(
        "/chat",
        json={
            "session_id": "test-session-123",
            "user_text": "Hello, Echo!",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert "assistant_text" in data
    assert "Hello, Echo!" in data["assistant_text"]
    assert data["actions"] == []


@pytest.mark.asyncio
async def test_chat_missing_fields(client: AsyncClient) -> None:
    """Test chat endpoint validates required fields."""
    response = await client.post("/chat", json={})

    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_chat_empty_text(client: AsyncClient) -> None:
    """Test chat endpoint accepts empty text."""
    response = await client.post(
        "/chat",
        json={
            "session_id": "test-session",
            "user_text": "",
        },
    )

    assert response.status_code == 200
