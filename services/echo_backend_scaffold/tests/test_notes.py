"""Notes endpoint tests."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_note(client: AsyncClient) -> None:
    """Test creating a note."""
    response = await client.post(
        "/notes",
        json={
            "title": "Test Note",
            "content": "This is a test note.",
            "tags": ["test", "example"],
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Note"
    assert data["content"] == "This is a test note."
    assert data["tags"] == ["test", "example"]
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


@pytest.mark.asyncio
async def test_list_notes(client: AsyncClient) -> None:
    """Test listing notes."""
    # Create a note first
    await client.post("/notes", json={"title": "List Test Note"})

    response = await client.get("/notes")

    assert response.status_code == 200
    data = response.json()
    assert "notes" in data
    assert "count" in data
    assert isinstance(data["notes"], list)


@pytest.mark.asyncio
async def test_get_note(client: AsyncClient) -> None:
    """Test getting a note by ID."""
    # Create a note first
    create_response = await client.post("/notes", json={"title": "Get Test Note"})
    note_id = create_response.json()["id"]

    response = await client.get(f"/notes/{note_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == note_id
    assert data["title"] == "Get Test Note"


@pytest.mark.asyncio
async def test_get_note_not_found(client: AsyncClient) -> None:
    """Test getting a non-existent note returns 404."""
    response = await client.get("/notes/non-existent-id")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_note(client: AsyncClient) -> None:
    """Test deleting a note."""
    # Create a note first
    create_response = await client.post("/notes", json={"title": "Delete Test Note"})
    note_id = create_response.json()["id"]

    # Delete the note
    response = await client.delete(f"/notes/{note_id}")
    assert response.status_code == 204

    # Verify it's gone
    get_response = await client.get(f"/notes/{note_id}")
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_delete_note_not_found(client: AsyncClient) -> None:
    """Test deleting a non-existent note returns 404."""
    response = await client.delete("/notes/non-existent-id")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_note_validation(client: AsyncClient) -> None:
    """Test note creation validates required fields."""
    response = await client.post("/notes", json={})

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_note_minimal(client: AsyncClient) -> None:
    """Test creating a note with only required fields."""
    response = await client.post("/notes", json={"title": "Minimal Note"})

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Minimal Note"
    assert data["content"] == ""
    assert data["tags"] == []
