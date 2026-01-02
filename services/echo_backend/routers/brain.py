"""Brain API router for conversational intelligence endpoints."""
import json
import logging
import os
import uuid
from typing import AsyncGenerator

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse

from models.brain import (
    BrainHealthResponse,
    ChatRequest,
    ChatResponse,
    ErrorInfo,
    ErrorResponse,
    RuntimeMetadata,
)
from utils.brain.provider import BrainProviderError, get_brain_provider, get_provider_name

logger = logging.getLogger(__name__)

# Runtime metadata (set via Cloud Run env vars at deploy time)
_APP_ENV = os.environ.get("APP_ENV", "unknown")
_GIT_SHA = os.environ.get("GIT_SHA", "unknown")
_BUILD_TIME = os.environ.get("BUILD_TIME", "unknown")


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
        ChatResponse with assistant's message, usage info, runtime metadata, and trace_id.
        
    Raises:
        HTTPException: With structured error details on failure.
    """
    trace_id = str(uuid.uuid4())
    provider_name = get_provider_name()
    msg_count = len(request.messages)
    
    # Build runtime metadata
    runtime = RuntimeMetadata(
        trace_id=trace_id,
        provider=provider_name,
        env=_APP_ENV,
        git_sha=_GIT_SHA,
        build_time=_BUILD_TIME,
    )
    
    # Log request (never log message contents for privacy)
    logger.info(f"ECHO_CHAT_REQUEST trace_id={trace_id} provider={provider_name} msg_count={msg_count}")
    
    try:
        provider = get_brain_provider()
        response = await provider.chat(request, trace_id=trace_id)
        
        # Add runtime metadata to response
        response.runtime = runtime
        
        return response
    except BrainProviderError as e:
        logger.error(f"ECHO_CHAT_ERROR trace_id={trace_id} code={e.code} error={e.message}")
        status_code = _error_code_to_status(e.code)
        # Return structured error response as HTTPException detail
        error_detail = {
            "ok": False,
            "error": {
                "code": e.code,
                "message": e.message,
                "upstream_request_id": e.upstream_request_id,
            },
            "runtime": runtime.model_dump(),
        }
        raise HTTPException(status_code=status_code, detail=error_detail)
    except Exception as e:
        logger.error(f"ECHO_CHAT_ERROR trace_id={trace_id} error={str(e)}")
        error_detail = {
            "ok": False,
            "error": {
                "code": "internal_error",
                "message": f"Chat generation failed: {str(e)}",
            },
            "runtime": runtime.model_dump(),
        }
        raise HTTPException(status_code=500, detail=error_detail)


def _error_code_to_status(code: str) -> int:
    """Map error codes to HTTP status codes."""
    mapping = {
        "auth_error": 401,
        "rate_limit": 429,
        "timeout": 504,
        "connection_error": 502,
        "bad_request": 400,
        "upstream_error": 502,
    }
    return mapping.get(code, 500)


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
        - final: complete response with metadata and runtime info
        - error: error information with ok=false and error code
    """
    trace_id = str(uuid.uuid4())
    provider_name = get_provider_name()
    msg_count = len(request.messages)
    
    # Log request (never log message contents for privacy)
    logger.info(f"ECHO_CHAT_STREAM_REQUEST trace_id={trace_id} provider={provider_name} msg_count={msg_count}")
    
    # Build runtime metadata dict for inclusion in final event
    runtime_metadata = {
        "trace_id": trace_id,
        "provider": provider_name,
        "env": _APP_ENV,
        "git_sha": _GIT_SHA,
        "build_time": _BUILD_TIME,
    }
    
    async def event_generator() -> AsyncGenerator[str, None]:
        """Generate SSE-formatted events."""
        try:
            provider = get_brain_provider()
            async for event_dict in provider.stream(request, trace_id=trace_id):
                event_type = event_dict.get("event", "token")
                event_data = event_dict.get("data", {})
                
                # Inject runtime metadata into final event
                # Avoid mutating provider-supplied data in-place
                if event_type == "final":
                    event_data = dict(event_data)
                    event_data["runtime"] = runtime_metadata
                    event_data["ok"] = True
                
                # Format as SSE: event line, data line, blank line
                sse_event = f"event: {event_type}\n"
                sse_event += f"data: {json.dumps(event_data)}\n\n"
                
                yield sse_event
        except BrainProviderError as e:
            logger.error(f"ECHO_CHAT_STREAM_ERROR trace_id={trace_id} code={e.code} error={e.message}")
            error_data = {
                "ok": False,
                "error": {
                    "code": e.code,
                    "message": e.message,
                    "upstream_request_id": e.upstream_request_id,
                },
                "runtime": runtime_metadata,
            }
            yield f"event: error\ndata: {json.dumps(error_data)}\n\n"
        except Exception as e:
            logger.error(f"ECHO_CHAT_STREAM_ERROR trace_id={trace_id} error={str(e)}")
            # Send error event with runtime metadata
            error_data = {
                "ok": False,
                "error": {
                    "code": "internal_error",
                    "message": str(e),
                },
                "runtime": runtime_metadata,
            }
            yield f"event: error\ndata: {json.dumps(error_data)}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )
