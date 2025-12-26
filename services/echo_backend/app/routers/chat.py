"""Chat endpoint with deterministic stub response."""

import logging

from fastapi import APIRouter

from app.models.chat import ChatRequest, ChatResponse

router = APIRouter(tags=["chat"])
logger = logging.getLogger(__name__)


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """Process a chat message.

    Currently returns a deterministic stub response.
    Will be connected to LLM in future phases.
    """
    logger.info(
        "Chat request received",
        extra={"session_id": request.session_id, "text_length": len(request.user_text)},
    )

    # Deterministic stub response
    # In future: integrate with OpenAI/LLM service
    assistant_text = f"Echo received: '{request.user_text}'. This is a stub response. LLM integration coming in Phase 1."

    return ChatResponse(
        assistant_text=assistant_text,
        actions=[],  # Actions will be populated by LLM in future phases
    )
