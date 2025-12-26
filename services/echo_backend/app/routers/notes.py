"""Notes CRUD endpoints."""

import logging

from fastapi import APIRouter, HTTPException, Request

from app.models.notes import Note, NoteCreate, NoteList
from app.services.notes_store import NotesStore

router = APIRouter(prefix="/notes", tags=["notes"])
logger = logging.getLogger(__name__)


def get_notes_store(request: Request) -> NotesStore:
    """Get notes store from app state."""
    return request.app.state.notes_store


@router.post("", response_model=Note, status_code=201)
async def create_note(note: NoteCreate, request: Request) -> Note:
    """Create a new note."""
    store = get_notes_store(request)
    created = await store.create(note)
    logger.info("Note created", extra={"note_id": created.id})
    return created


@router.get("", response_model=NoteList)
async def list_notes(request: Request) -> NoteList:
    """List all notes."""
    store = get_notes_store(request)
    notes = await store.list_all()
    return NoteList(notes=notes, count=len(notes))


@router.get("/{note_id}", response_model=Note)
async def get_note(note_id: str, request: Request) -> Note:
    """Get a note by ID."""
    store = get_notes_store(request)
    note = await store.get(note_id)
    if note is None:
        raise HTTPException(status_code=404, detail="Note not found")
    return note


@router.delete("/{note_id}", status_code=204)
async def delete_note(note_id: str, request: Request) -> None:
    """Delete a note by ID."""
    store = get_notes_store(request)
    deleted = await store.delete(note_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Note not found")
    logger.info("Note deleted", extra={"note_id": note_id})
