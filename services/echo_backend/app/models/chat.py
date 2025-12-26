"""Chat models."""

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Chat request payload."""

    session_id: str = Field(..., description="Unique session identifier")
    user_text: str = Field(..., description="User's message text")


class Action(BaseModel):
    """Action to be executed by the client."""

    type: str = Field(..., description="Action type (e.g., 'create_note', 'send_email')")
    payload: dict = Field(default_factory=dict, description="Action-specific data")


class ChatResponse(BaseModel):
    """Chat response payload."""

    assistant_text: str = Field(..., description="Assistant's response text")
    actions: list[Action] = Field(
        default_factory=list, description="Actions for client to execute"
    )
