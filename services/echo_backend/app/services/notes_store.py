"""Notes storage service."""

import uuid
from datetime import datetime, timezone

from app.models.notes import Note, NoteCreate


class NotesStore:
    """In-memory notes storage.

    For Phase 0, we use simple in-memory storage.
    Can be upgraded to SQLite or PostgreSQL in future phases.
    """

    def __init__(self) -> None:
        self._notes: dict[str, Note] = {}

    async def initialize(self) -> None:
        """Initialize the store."""
        # In future: initialize database connection
        pass

    async def create(self, note_create: NoteCreate) -> Note:
        """Create a new note."""
        now = datetime.now(timezone.utc)
        note = Note(
            id=str(uuid.uuid4()),
            title=note_create.title,
            content=note_create.content,
            tags=note_create.tags,
            created_at=now,
            updated_at=now,
        )
        self._notes[note.id] = note
        return note

    async def get(self, note_id: str) -> Note | None:
        """Get a note by ID."""
        return self._notes.get(note_id)

    async def list_all(self) -> list[Note]:
        """List all notes, sorted by creation time (newest first)."""
        return sorted(
            self._notes.values(),
            key=lambda n: n.created_at,
            reverse=True,
        )

    async def delete(self, note_id: str) -> bool:
        """Delete a note. Returns True if deleted, False if not found."""
        if note_id in self._notes:
            del self._notes[note_id]
            return True
        return False
