"""Brain provider interface and implementations for conversational AI."""
import os
import uuid
from abc import ABC, abstractmethod
from typing import AsyncGenerator, Dict, List, Optional

from models.brain import ChatRequest, ChatResponse, Message, MessageRole, UsageInfo


class BrainProvider(ABC):
    """Abstract interface for brain providers."""

    @abstractmethod
    async def chat(self, request: ChatRequest) -> ChatResponse:
        """Generate a chat completion.
        
        Args:
            request: The chat request with messages and metadata.
            
        Returns:
            ChatResponse with the assistant's message.
        """
        pass

    @abstractmethod
    async def stream(self, request: ChatRequest) -> AsyncGenerator[Dict, None]:
        """Stream a chat completion as SSE events.
        
        Args:
            request: The chat request with messages and metadata.
            
        Yields:
            Dict events with 'event' and 'data' keys for SSE formatting.
        """
        pass


class StubBrainProvider(BrainProvider):
    """Stub provider for testing without external dependencies."""

    async def chat(self, request: ChatRequest) -> ChatResponse:
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

    async def stream(self, request: ChatRequest) -> AsyncGenerator[Dict, None]:
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
    """OpenAI-backed brain provider using langchain ChatOpenAI."""

    def __init__(self):
        """Initialize with lazy LLM client."""
        self._llm = None

    def _get_llm(self):
        """Lazy-init ChatOpenAI client."""
        if self._llm is not None:
            return self._llm
        
        # Import here to allow module import without OPENAI_API_KEY
        from utils.llm.clients import get_llm_fast
        
        self._llm = get_llm_fast()
        return self._llm

    async def chat(self, request: ChatRequest) -> ChatResponse:
        """Generate chat completion using OpenAI."""
        session_id = request.session_id or str(uuid.uuid4())
        llm = self._get_llm()
        
        # Convert messages to langchain format
        from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
        
        lc_messages = []
        for msg in request.messages:
            if msg.role == MessageRole.system:
                lc_messages.append(SystemMessage(content=msg.content))
            elif msg.role == MessageRole.user:
                lc_messages.append(HumanMessage(content=msg.content))
            elif msg.role == MessageRole.assistant:
                lc_messages.append(AIMessage(content=msg.content))
        
        # Invoke LLM
        response = await llm.ainvoke(lc_messages)
        
        # Extract usage if available
        usage = None
        if hasattr(response, 'usage_metadata') and response.usage_metadata:
            usage = UsageInfo(
                prompt_tokens=response.usage_metadata.get('input_tokens', 0),
                completion_tokens=response.usage_metadata.get('output_tokens', 0),
                total_tokens=response.usage_metadata.get('total_tokens', 0)
            )
        
        return ChatResponse(
            session_id=session_id,
            message=Message(role=MessageRole.assistant, content=response.content),
            usage=usage,
            metadata={"provider": "openai"}
        )

    async def stream(self, request: ChatRequest) -> AsyncGenerator[Dict, None]:
        """Stream chat completion using OpenAI."""
        session_id = request.session_id or str(uuid.uuid4())
        llm = self._get_llm()
        
        # Convert messages to langchain format
        from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
        
        lc_messages = []
        for msg in request.messages:
            if msg.role == MessageRole.system:
                lc_messages.append(SystemMessage(content=msg.content))
            elif msg.role == MessageRole.user:
                lc_messages.append(HumanMessage(content=msg.content))
            elif msg.role == MessageRole.assistant:
                lc_messages.append(AIMessage(content=msg.content))
        
        # Stream tokens
        full_content = ""
        async for chunk in llm.astream(lc_messages):
            if chunk.content:
                full_content += chunk.content
                yield {
                    "event": "token",
                    "data": {"token": chunk.content, "session_id": session_id}
                }
        
        # Emit final event
        yield {
            "event": "final",
            "data": {
                "session_id": session_id,
                "message": {"role": "assistant", "content": full_content},
                "metadata": {"provider": "openai"}
            }
        }


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
