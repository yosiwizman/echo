"""Notes models."""

from datetime import datetime

from pydantic import BaseModel, Field


class NoteCreate(BaseModel):
    """Note creation payload."""

    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(default="")
    tags: list[str] = Field(default_factory=list)


class Note(BaseModel):
    """Note response model."""

    id: str
    title: str
    content: str
    tags: list[str]
    created_at: datetime
    updated_at: datetime


class NoteList(BaseModel):
    """List of notes response."""

    notes: list[Note]
    count: int
