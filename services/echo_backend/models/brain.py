"""Brain API models for conversational intelligence endpoints."""
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class MessageRole(str, Enum):
    """Role of a message in a conversation."""
    system = "system"
    user = "user"
    assistant = "assistant"


class Message(BaseModel):
    """A single message in a conversation."""
    role: MessageRole = Field(description="Role of the message sender")
    content: str = Field(description="The message content")


class ChatRequest(BaseModel):
    """Request for a chat completion."""
    messages: List[Message] = Field(description="List of messages in the conversation")
    session_id: Optional[str] = Field(default=None, description="Optional session identifier for continuity")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Optional metadata for the request")


class UsageInfo(BaseModel):
    """Token usage information."""
    prompt_tokens: int = Field(default=0, description="Number of tokens in the prompt")
    completion_tokens: int = Field(default=0, description="Number of tokens in the completion")
    total_tokens: int = Field(default=0, description="Total tokens used")


class RuntimeMetadata(BaseModel):
    """Runtime metadata included in responses for observability."""
    trace_id: str = Field(description="Unique trace ID for this request")
    provider: str = Field(description="Active brain provider (stub/openai)")
    env: str = Field(default="unknown", description="Deployment environment (staging/production/unknown)")
    git_sha: str = Field(default="unknown", description="Git commit SHA of the deployed version")
    build_time: str = Field(default="unknown", description="Build timestamp of the deployed version")


class ChatResponse(BaseModel):
    """Response from a chat completion."""
    ok: bool = Field(default=True, description="Request success status")
    session_id: str = Field(description="Session identifier")
    message: Message = Field(description="The assistant's response message")
    usage: Optional[UsageInfo] = Field(default=None, description="Token usage information")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Optional response metadata")
    runtime: Optional[RuntimeMetadata] = Field(default=None, description="Runtime metadata for observability")


class StreamEventType(str, Enum):
    """Type of streaming event."""
    token = "token"
    final = "final"
    error = "error"
    meta = "meta"


class StreamEvent(BaseModel):
    """A single event in a streaming response."""
    event: StreamEventType = Field(description="Type of the streaming event")
    data: Dict[str, Any] = Field(description="Event data payload")


class BrainHealthResponse(BaseModel):
    """Health check response for Brain API."""
    ok: bool = Field(default=True, description="Health status")
    time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Server time")
    version: str = Field(default="1.0.0", description="API version")
    provider: str = Field(description="Active brain provider")
