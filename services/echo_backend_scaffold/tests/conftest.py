"""Pytest configuration and fixtures."""

from collections.abc import AsyncGenerator
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.services.notes_store import NotesStore


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Create async test client with fresh state."""
    # Reset app state for test isolation
    app.state.notes_store = NotesStore()
    await app.state.notes_store.initialize()

    transport: Any = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
