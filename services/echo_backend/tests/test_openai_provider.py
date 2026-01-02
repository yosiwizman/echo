"""Tests for OpenAI brain provider with mocked client."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.fixture(autouse=True)
def reset_provider_instance():
    """Reset provider singleton between tests."""
    from utils.brain import provider
    provider._provider_instance = None
    yield
    provider._provider_instance = None


@pytest.fixture
def mock_env_stub(monkeypatch):
    """Configure stub provider."""
    monkeypatch.setenv("ECHO_BRAIN_PROVIDER", "stub")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)


@pytest.fixture
def mock_env_openai(monkeypatch):
    """Configure OpenAI provider with test key."""
    monkeypatch.setenv("ECHO_BRAIN_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key-12345")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-4.1-mini")


@pytest.fixture
def mock_env_openai_no_key(monkeypatch):
    """Configure OpenAI provider WITHOUT API key."""
    monkeypatch.setenv("ECHO_BRAIN_PROVIDER", "openai")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)


class TestProviderSelection:
    """Tests for provider selection logic."""

    def test_explicit_stub_provider(self, mock_env_stub):
        """ECHO_BRAIN_PROVIDER=stub uses StubBrainProvider."""
        from utils.brain.provider import get_brain_provider, StubBrainProvider
        
        provider = get_brain_provider()
        assert isinstance(provider, StubBrainProvider)

    def test_explicit_openai_provider(self, mock_env_openai):
        """ECHO_BRAIN_PROVIDER=openai uses OpenAIBrainProvider."""
        from utils.brain.provider import get_brain_provider, OpenAIBrainProvider
        
        provider = get_brain_provider()
        assert isinstance(provider, OpenAIBrainProvider)

    def test_openai_provider_requires_key(self, mock_env_openai_no_key):
        """ECHO_BRAIN_PROVIDER=openai without key raises RuntimeError."""
        from utils.brain.provider import get_brain_provider
        
        with pytest.raises(RuntimeError) as exc_info:
            get_brain_provider()
        
        assert "OPENAI_API_KEY" in str(exc_info.value)

    def test_auto_select_stub_without_key(self, monkeypatch):
        """Without explicit provider or key, falls back to stub."""
        monkeypatch.delenv("ECHO_BRAIN_PROVIDER", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        
        from utils.brain.provider import get_brain_provider, StubBrainProvider
        
        provider = get_brain_provider()
        assert isinstance(provider, StubBrainProvider)

    def test_get_provider_name(self, mock_env_stub):
        """get_provider_name returns correct name."""
        from utils.brain.provider import get_provider_name
        
        assert get_provider_name() == "stub"


class TestOpenAIProviderChat:
    """Tests for OpenAI provider chat method."""

    @pytest.mark.asyncio
    async def test_chat_success(self, mock_env_openai):
        """Test successful chat completion."""
        from utils.brain.provider import OpenAIBrainProvider
        from models.brain import ChatRequest, Message, MessageRole
        
        provider = OpenAIBrainProvider()
        
        # Mock the OpenAI client
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Hello from OpenAI!"
        mock_response.usage = MagicMock()
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5
        mock_response.usage.total_tokens = 15
        mock_response._request_id = "req-12345"
        
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        
        with patch.object(provider, '_get_client', return_value=mock_client):
            request = ChatRequest(
                messages=[Message(role=MessageRole.user, content="Hello")]
            )
            response = await provider.chat(request, trace_id="trace-abc")
        
        assert response.ok is True
        assert response.message.content == "Hello from OpenAI!"
        assert response.message.role == MessageRole.assistant
        assert response.usage.total_tokens == 15
        assert response.metadata["provider"] == "openai"
        assert response.metadata["model"] == "gpt-4.1-mini"
        
        # Verify OpenAI was called with correct params
        mock_client.chat.completions.create.assert_called_once()
        call_kwargs = mock_client.chat.completions.create.call_args.kwargs
        assert call_kwargs["model"] == "gpt-4.1-mini"
        assert call_kwargs["messages"] == [{"role": "user", "content": "Hello"}]
        assert call_kwargs["extra_headers"]["X-Client-Request-Id"] == "trace-abc"

    @pytest.mark.asyncio
    async def test_chat_auth_error(self, mock_env_openai):
        """Test authentication error mapping."""
        from utils.brain.provider import OpenAIBrainProvider, BrainProviderError
        from models.brain import ChatRequest, Message, MessageRole
        from openai import AuthenticationError
        
        provider = OpenAIBrainProvider()
        
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(
            side_effect=AuthenticationError(
                message="Invalid API key",
                response=MagicMock(status_code=401),
                body={"error": {"message": "Invalid API key"}}
            )
        )
        
        with patch.object(provider, '_get_client', return_value=mock_client):
            request = ChatRequest(
                messages=[Message(role=MessageRole.user, content="Hello")]
            )
            
            with pytest.raises(BrainProviderError) as exc_info:
                await provider.chat(request)
        
        assert exc_info.value.code == "auth_error"
        assert "authentication" in exc_info.value.message.lower()

    @pytest.mark.asyncio
    async def test_chat_rate_limit_error(self, mock_env_openai):
        """Test rate limit error mapping."""
        from utils.brain.provider import OpenAIBrainProvider, BrainProviderError
        from models.brain import ChatRequest, Message, MessageRole
        from openai import RateLimitError
        
        provider = OpenAIBrainProvider()
        
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(
            side_effect=RateLimitError(
                message="Rate limit exceeded",
                response=MagicMock(status_code=429),
                body={"error": {"message": "Rate limit exceeded"}}
            )
        )
        
        with patch.object(provider, '_get_client', return_value=mock_client):
            request = ChatRequest(
                messages=[Message(role=MessageRole.user, content="Hello")]
            )
            
            with pytest.raises(BrainProviderError) as exc_info:
                await provider.chat(request)
        
        assert exc_info.value.code == "rate_limit"

    @pytest.mark.asyncio
    async def test_chat_timeout_error(self, mock_env_openai):
        """Test timeout error mapping."""
        from utils.brain.provider import OpenAIBrainProvider, BrainProviderError
        from models.brain import ChatRequest, Message, MessageRole
        from openai import APITimeoutError
        
        provider = OpenAIBrainProvider()
        
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(
            side_effect=APITimeoutError(request=MagicMock())
        )
        
        with patch.object(provider, '_get_client', return_value=mock_client):
            request = ChatRequest(
                messages=[Message(role=MessageRole.user, content="Hello")]
            )
            
            with pytest.raises(BrainProviderError) as exc_info:
                await provider.chat(request)
        
        assert exc_info.value.code == "timeout"


class TestOpenAIProviderStream:
    """Tests for OpenAI provider streaming."""

    @pytest.mark.asyncio
    async def test_stream_success(self, mock_env_openai):
        """Test successful streaming response."""
        from utils.brain.provider import OpenAIBrainProvider
        from models.brain import ChatRequest, Message, MessageRole
        
        provider = OpenAIBrainProvider()
        
        # Create mock stream chunks
        chunks = []
        for token in ["Hello", " from", " OpenAI", "!"]:
            chunk = MagicMock()
            chunk.choices = [MagicMock()]
            chunk.choices[0].delta.content = token
            chunk.usage = None
            chunk._request_id = "req-stream-123"
            chunks.append(chunk)
        
        # Final chunk with usage
        final_chunk = MagicMock()
        final_chunk.choices = [MagicMock()]
        final_chunk.choices[0].delta.content = None
        final_chunk.usage = MagicMock()
        final_chunk.usage.prompt_tokens = 5
        final_chunk.usage.completion_tokens = 4
        final_chunk.usage.total_tokens = 9
        chunks.append(final_chunk)
        
        async def mock_stream():
            for chunk in chunks:
                yield chunk
        
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_stream())
        
        with patch.object(provider, '_get_client', return_value=mock_client):
            request = ChatRequest(
                messages=[Message(role=MessageRole.user, content="Hi")]
            )
            
            events = []
            async for event in provider.stream(request, trace_id="trace-stream"):
                events.append(event)
        
        # Should have 4 token events + 1 final event
        token_events = [e for e in events if e["event"] == "token"]
        final_events = [e for e in events if e["event"] == "final"]
        
        assert len(token_events) == 4
        assert len(final_events) == 1
        
        # Verify tokens
        tokens = [e["data"]["token"] for e in token_events]
        assert tokens == ["Hello", " from", " OpenAI", "!"]
        
        # Verify final event
        final = final_events[0]["data"]
        assert final["message"]["content"] == "Hello from OpenAI!"
        assert final["message"]["role"] == "assistant"
        assert final["metadata"]["provider"] == "openai"

    @pytest.mark.asyncio
    async def test_stream_error(self, mock_env_openai):
        """Test streaming error handling."""
        from utils.brain.provider import OpenAIBrainProvider, BrainProviderError
        from models.brain import ChatRequest, Message, MessageRole
        from openai import APIConnectionError
        
        provider = OpenAIBrainProvider()
        
        mock_client = AsyncMock()
        mock_client.chat.completions.create = AsyncMock(
            side_effect=APIConnectionError(request=MagicMock())
        )
        
        with patch.object(provider, '_get_client', return_value=mock_client):
            request = ChatRequest(
                messages=[Message(role=MessageRole.user, content="Hello")]
            )
            
            with pytest.raises(BrainProviderError) as exc_info:
                async for _ in provider.stream(request):
                    pass
        
        assert exc_info.value.code == "connection_error"


class TestErrorCodeMapping:
    """Tests for HTTP status code mapping."""

    def test_error_code_to_status(self):
        """Test error code to HTTP status mapping."""
        from routers.brain import _error_code_to_status
        
        assert _error_code_to_status("auth_error") == 401
        assert _error_code_to_status("rate_limit") == 429
        assert _error_code_to_status("timeout") == 504
        assert _error_code_to_status("connection_error") == 502
        assert _error_code_to_status("bad_request") == 400
        assert _error_code_to_status("upstream_error") == 502
        assert _error_code_to_status("unknown_code") == 500


class TestIntegrationWithRouter:
    """Integration tests with the router."""

    def test_chat_endpoint_returns_error_response(self, mock_env_openai):
        """Test that chat endpoint returns proper error response."""
        from main import app
        from fastapi.testclient import TestClient
        from unittest.mock import patch
        from utils.brain.provider import BrainProviderError
        
        # Reset provider
        from utils.brain import provider as provider_module
        provider_module._provider_instance = None
        
        client = TestClient(app)
        
        # Mock the provider to raise an error
        mock_provider = MagicMock()
        mock_provider.chat = AsyncMock(
            side_effect=BrainProviderError(
                code="rate_limit",
                message="Rate limit exceeded",
                upstream_request_id="req-xyz"
            )
        )
        
        with patch('routers.brain.get_brain_provider', return_value=mock_provider):
            resp = client.post("/v1/brain/chat", json={
                "messages": [{"role": "user", "content": "Hello"}]
            })
        
        assert resp.status_code == 429
        data = resp.json()
        # Error info is in the 'detail' field (FastAPI HTTPException format)
        detail = data["detail"]
        assert detail["ok"] is False
        assert detail["error"]["code"] == "rate_limit"
        assert "runtime" in detail
        assert "trace_id" in detail["runtime"]
