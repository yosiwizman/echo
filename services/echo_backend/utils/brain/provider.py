"""Brain provider interface and implementations for conversational AI."""
import logging
import os
import uuid
from abc import ABC, abstractmethod
from typing import AsyncGenerator, Dict, Optional

from models.brain import ChatRequest, ChatResponse, Message, MessageRole, UsageInfo

logger = logging.getLogger(__name__)

# Configuration defaults
DEFAULT_MODEL = "gpt-4o-mini"  # Cost-efficient, strong baseline
DEFAULT_TIMEOUT = 60  # seconds
DEFAULT_MAX_TOKENS = 4096


class BrainProviderError(Exception):
    """Base exception for brain provider errors."""
    
    def __init__(self, code: str, message: str, upstream_request_id: Optional[str] = None):
        self.code = code
        self.message = message
        self.upstream_request_id = upstream_request_id
        super().__init__(message)


class BrainProvider(ABC):
    """Abstract interface for brain providers."""

    @abstractmethod
    async def chat(self, request: ChatRequest, trace_id: Optional[str] = None) -> ChatResponse:
        """Generate a chat completion.
        
        Args:
            request: The chat request with messages and metadata.
            trace_id: Optional trace ID for request correlation.
            
        Returns:
            ChatResponse with the assistant's message.
            
        Raises:
            BrainProviderError: If the provider encounters an error.
        """
        pass

    @abstractmethod
    async def stream(self, request: ChatRequest, trace_id: Optional[str] = None) -> AsyncGenerator[Dict, None]:
        """Stream a chat completion as SSE events.
        
        Args:
            request: The chat request with messages and metadata.
            trace_id: Optional trace ID for request correlation.
            
        Yields:
            Dict events with 'event' and 'data' keys for SSE formatting.
            
        Raises:
            BrainProviderError: If the provider encounters an error.
        """
        pass


class StubBrainProvider(BrainProvider):
    """Stub provider for testing without external dependencies."""

    async def chat(self, request: ChatRequest, trace_id: Optional[str] = None) -> ChatResponse:
        """Return a deterministic canned response."""
        session_id = request.session_id or str(uuid.uuid4())
        message_count = len(request.messages)
        
        content = f"Echo Brain (stub): received {message_count} message{'s' if message_count != 1 else ''}."
        
        return ChatResponse(
            session_id=session_id,
            message=Message(role=MessageRole.assistant, content=content),
            usage=UsageInfo(prompt_tokens=10, completion_tokens=15, total_tokens=25),
            metadata={"provider": "stub"}
        )

    async def stream(self, request: ChatRequest, trace_id: Optional[str] = None) -> AsyncGenerator[Dict, None]:
        """Stream deterministic token events."""
        session_id = request.session_id or str(uuid.uuid4())
        
        # Emit token events
        tokens = ["Echo", " Brain", " (stub)", ":", " streaming", " response", "."]
        for token in tokens:
            yield {
                "event": "token",
                "data": {"token": token, "session_id": session_id}
            }
        
        # Emit final event
        full_content = "".join(tokens)
        yield {
            "event": "final",
            "data": {
                "session_id": session_id,
                "message": {"role": "assistant", "content": full_content},
                "usage": {"prompt_tokens": 10, "completion_tokens": 15, "total_tokens": 25}
            }
        }


class OpenAIBrainProvider(BrainProvider):
    """OpenAI-backed brain provider using official OpenAI SDK.
    
    Features:
    - Direct OpenAI API calls (no langchain dependency)
    - Configurable model via OPENAI_MODEL env var
    - Request timeout and max tokens limits
    - Trace ID propagation via X-Client-Request-Id header
    - Structured error handling with upstream request ID capture
    - Privacy: never logs message contents
    """

    def __init__(self):
        """Initialize with lazy client."""
        self._client = None
        self._model = os.environ.get("OPENAI_MODEL", DEFAULT_MODEL)
        self._timeout = float(os.environ.get("OPENAI_TIMEOUT", DEFAULT_TIMEOUT))
        self._max_tokens = int(os.environ.get("OPENAI_MAX_TOKENS", DEFAULT_MAX_TOKENS))

    def _get_client(self):
        """Lazy-init AsyncOpenAI client."""
        if self._client is not None:
            return self._client
        
        # Import here to allow module import without OPENAI_API_KEY
        from openai import AsyncOpenAI
        
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise BrainProviderError(
                code="auth_error",
                message="OPENAI_API_KEY not configured"
            )
        
        self._client = AsyncOpenAI(
            api_key=api_key,
            timeout=self._timeout,
            max_retries=2,
        )
        return self._client

    def _convert_messages(self, messages):
        """Convert ChatRequest messages to OpenAI format."""
        return [
            {"role": msg.role.value, "content": msg.content}
            for msg in messages
        ]

    def _map_error(self, e: Exception, upstream_request_id: Optional[str] = None) -> BrainProviderError:
        """Map OpenAI exceptions to BrainProviderError."""
        from openai import (
            AuthenticationError,
            RateLimitError,
            APITimeoutError,
            APIConnectionError,
            BadRequestError,
            APIStatusError,
        )
        
        if isinstance(e, AuthenticationError):
            return BrainProviderError(
                code="auth_error",
                message="OpenAI authentication failed. Check API key.",
                upstream_request_id=upstream_request_id
            )
        elif isinstance(e, RateLimitError):
            return BrainProviderError(
                code="rate_limit",
                message="OpenAI rate limit exceeded. Please retry later.",
                upstream_request_id=upstream_request_id
            )
        elif isinstance(e, APITimeoutError):
            return BrainProviderError(
                code="timeout",
                message=f"OpenAI request timed out after {self._timeout}s.",
                upstream_request_id=upstream_request_id
            )
        elif isinstance(e, APIConnectionError):
            return BrainProviderError(
                code="connection_error",
                message="Failed to connect to OpenAI API.",
                upstream_request_id=upstream_request_id
            )
        elif isinstance(e, BadRequestError):
            return BrainProviderError(
                code="bad_request",
                message=f"Invalid request to OpenAI: {str(e)}",
                upstream_request_id=upstream_request_id
            )
        elif isinstance(e, APIStatusError):
            return BrainProviderError(
                code="upstream_error",
                message=f"OpenAI API error (HTTP {e.status_code}): {str(e)}",
                upstream_request_id=upstream_request_id
            )
        else:
            return BrainProviderError(
                code="unknown_error",
                message=f"Unexpected error: {str(e)}",
                upstream_request_id=upstream_request_id
            )

    async def chat(self, request: ChatRequest, trace_id: Optional[str] = None) -> ChatResponse:
        """Generate chat completion using OpenAI.
        
        Args:
            request: Chat request with messages.
            trace_id: Optional trace ID for correlation (sent to OpenAI as X-Client-Request-Id).
            
        Returns:
            ChatResponse with assistant message and usage info.
            
        Raises:
            BrainProviderError: On API errors.
        """
        session_id = request.session_id or str(uuid.uuid4())
        client = self._get_client()
        messages = self._convert_messages(request.messages)
        upstream_request_id = None
        
        try:
            # Build extra headers for trace propagation
            extra_headers = {}
            if trace_id:
                extra_headers["X-Client-Request-Id"] = trace_id
            
            response = await client.chat.completions.create(
                model=self._model,
                messages=messages,
                max_tokens=self._max_tokens,
                extra_headers=extra_headers if extra_headers else None,
            )
            
            # Capture upstream request ID for logging
            # OpenAI returns this in response headers, but SDK exposes it on response object
            if hasattr(response, '_request_id'):
                upstream_request_id = response._request_id
            
            # Log success (no message content for privacy)
            logger.info(
                f"OPENAI_CHAT_SUCCESS trace_id={trace_id} model={self._model} "
                f"openai_request_id={upstream_request_id}"
            )
            
            # Extract response
            choice = response.choices[0]
            content = choice.message.content or ""
            
            # Extract usage
            usage = None
            if response.usage:
                usage = UsageInfo(
                    prompt_tokens=response.usage.prompt_tokens,
                    completion_tokens=response.usage.completion_tokens,
                    total_tokens=response.usage.total_tokens,
                )
            
            return ChatResponse(
                session_id=session_id,
                message=Message(role=MessageRole.assistant, content=content),
                usage=usage,
                metadata={
                    "provider": "openai",
                    "model": self._model,
                    "openai_request_id": upstream_request_id,
                }
            )
            
        except BrainProviderError:
            raise
        except Exception as e:
            logger.error(
                f"OPENAI_CHAT_ERROR trace_id={trace_id} error_type={type(e).__name__} "
                f"openai_request_id={upstream_request_id}"
            )
            raise self._map_error(e, upstream_request_id)

    async def stream(self, request: ChatRequest, trace_id: Optional[str] = None) -> AsyncGenerator[Dict, None]:
        """Stream chat completion using OpenAI.
        
        Args:
            request: Chat request with messages.
            trace_id: Optional trace ID for correlation.
            
        Yields:
            SSE event dicts with 'event' and 'data' keys.
            
        Raises:
            BrainProviderError: On API errors.
        """
        session_id = request.session_id or str(uuid.uuid4())
        client = self._get_client()
        messages = self._convert_messages(request.messages)
        upstream_request_id = None
        
        try:
            # Build extra headers for trace propagation
            extra_headers = {}
            if trace_id:
                extra_headers["X-Client-Request-Id"] = trace_id
            
            stream = await client.chat.completions.create(
                model=self._model,
                messages=messages,
                max_tokens=self._max_tokens,
                stream=True,
                extra_headers=extra_headers if extra_headers else None,
            )
            
            full_content = ""
            usage_info = None
            
            async for chunk in stream:
                # Capture request ID from first chunk if available
                if upstream_request_id is None and hasattr(chunk, '_request_id'):
                    upstream_request_id = chunk._request_id
                
                # Extract token from chunk
                if chunk.choices and chunk.choices[0].delta.content:
                    token = chunk.choices[0].delta.content
                    full_content += token
                    yield {
                        "event": "token",
                        "data": {"token": token, "session_id": session_id}
                    }
                
                # Check for usage in final chunk (if stream_options.include_usage was set)
                if hasattr(chunk, 'usage') and chunk.usage:
                    usage_info = {
                        "prompt_tokens": chunk.usage.prompt_tokens,
                        "completion_tokens": chunk.usage.completion_tokens,
                        "total_tokens": chunk.usage.total_tokens,
                    }
            
            # Log success
            logger.info(
                f"OPENAI_STREAM_SUCCESS trace_id={trace_id} model={self._model} "
                f"openai_request_id={upstream_request_id}"
            )
            
            # Emit final event
            yield {
                "event": "final",
                "data": {
                    "session_id": session_id,
                    "message": {"role": "assistant", "content": full_content},
                    "usage": usage_info,
                    "metadata": {
                        "provider": "openai",
                        "model": self._model,
                        "openai_request_id": upstream_request_id,
                    }
                }
            }
            
        except BrainProviderError:
            raise
        except Exception as e:
            logger.error(
                f"OPENAI_STREAM_ERROR trace_id={trace_id} error_type={type(e).__name__} "
                f"openai_request_id={upstream_request_id}"
            )
            raise self._map_error(e, upstream_request_id)


# Provider registry and selection logic
_provider_instance: Optional[BrainProvider] = None
_REQUIRE_OPENAI = os.environ.get('ECHO_REQUIRE_OPENAI', '').lower() in ('1', 'true')


def get_brain_provider() -> BrainProvider:
    """Get the configured brain provider instance.
    
    Selection logic:
    1. If ECHO_BRAIN_PROVIDER explicitly set -> use it
    2. Else if OPENAI_API_KEY exists -> openai provider
    3. Else -> stub provider (for CI/testing)
    
    Returns:
        BrainProvider instance (cached after first call).
        
    Raises:
        RuntimeError: If OpenAI provider required but API key missing (strict mode).
    """
    global _provider_instance
    
    if _provider_instance is not None:
        return _provider_instance
    
    # Check explicit provider override
    provider_name = os.environ.get('ECHO_BRAIN_PROVIDER', '').lower()
    
    if provider_name == 'stub':
        _provider_instance = StubBrainProvider()
        return _provider_instance
    
    if provider_name == 'openai':
        if not os.environ.get('OPENAI_API_KEY'):
            raise RuntimeError(
                "ECHO_BRAIN_PROVIDER=openai but OPENAI_API_KEY not set. "
                "Provide the key or use ECHO_BRAIN_PROVIDER=stub for testing."
            )
        _provider_instance = OpenAIBrainProvider()
        return _provider_instance
    
    # Auto-selection based on OPENAI_API_KEY availability
    if os.environ.get('OPENAI_API_KEY'):
        _provider_instance = OpenAIBrainProvider()
    elif _REQUIRE_OPENAI:
        raise RuntimeError(
            "ECHO_REQUIRE_OPENAI=1 but OPENAI_API_KEY not set. "
            "Provide the key or disable strict mode for testing."
        )
    else:
        # Fallback to stub for CI/testing
        _provider_instance = StubBrainProvider()
    
    return _provider_instance


def get_provider_name() -> str:
    """Get the name of the active provider."""
    provider = get_brain_provider()
    if isinstance(provider, StubBrainProvider):
        return "stub"
    elif isinstance(provider, OpenAIBrainProvider):
        return "openai"
    return "unknown"
