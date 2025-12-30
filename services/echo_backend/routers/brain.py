"""Brain API router for conversational intelligence endpoints."""
import json
from typing import AsyncGenerator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from models.brain import BrainHealthResponse, ChatRequest, ChatResponse
from utils.brain.provider import get_brain_provider, get_provider_name


router = APIRouter()


@router.get("/health", response_model=BrainHealthResponse)
async def brain_health():
    """Health check for Brain API.
    
    Returns:
        BrainHealthResponse with status, time, version, and active provider.
    """
    provider_name = get_provider_name()
    return BrainHealthResponse(provider=provider_name)


@router.post("/chat", response_model=ChatResponse)
async def brain_chat(request: ChatRequest):
    """Generate a chat completion (non-streaming).
    
    Args:
        request: ChatRequest with messages, optional session_id, and metadata.
        
    Returns:
        ChatResponse with assistant's message, usage info, and metadata.
        
    Raises:
        HTTPException: If chat generation fails.
    """
    try:
        provider = get_brain_provider()
        response = await provider.chat(request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat generation failed: {str(e)}")


@router.post("/chat/stream")
async def brain_chat_stream(request: ChatRequest):
    """Generate a streaming chat completion (SSE).
    
    Args:
        request: ChatRequest with messages, optional session_id, and metadata.
        
    Returns:
        StreamingResponse with text/event-stream content type.
        SSE format: "event: <type>\\ndata: <json>\\n\\n"
        
    Events:
        - token: partial response tokens
        - final: complete response with metadata
        - error: error information
    """
    
    async def event_generator() -> AsyncGenerator[str, None]:
        """Generate SSE-formatted events."""
        try:
            provider = get_brain_provider()
            async for event_dict in provider.stream(request):
                event_type = event_dict.get("event", "token")
                event_data = event_dict.get("data", {})
                
                # Format as SSE: event line, data line, blank line
                sse_event = f"event: {event_type}\n"
                sse_event += f"data: {json.dumps(event_data)}\n\n"
                
                yield sse_event
        except Exception as e:
            # Send error event
            error_event = {
                "event": "error",
                "data": {"error": str(e)}
            }
            yield f"event: error\ndata: {json.dumps(error_event['data'])}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )
