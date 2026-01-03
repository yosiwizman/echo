"""Voice provider interface and implementations for STT and TTS.

Provides speech-to-text (STT) and text-to-speech (TTS) capabilities
using OpenAI Audio API or stub implementations for testing.
"""
import base64
import logging
import os
from abc import ABC, abstractmethod
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

# Configuration defaults
DEFAULT_STT_MODEL = "gpt-4o-mini-transcribe"  # OpenAI's latest transcription model
DEFAULT_TTS_MODEL = "gpt-4o-mini-tts"  # OpenAI's latest TTS model
DEFAULT_TTS_VOICE = "alloy"  # Neutral, balanced voice
DEFAULT_TTS_FORMAT = "mp3"  # Widely supported format
DEFAULT_TIMEOUT = 60  # seconds

# Format to MIME type mapping
FORMAT_MIME_TYPES = {
    "mp3": "audio/mpeg",
    "opus": "audio/opus",
    "aac": "audio/aac",
    "flac": "audio/flac",
    "wav": "audio/wav",
    "pcm": "audio/pcm",
}


class VoiceProviderError(Exception):
    """Base exception for voice provider errors."""
    
    def __init__(self, code: str, message: str, upstream_request_id: Optional[str] = None):
        self.code = code
        self.message = message
        self.upstream_request_id = upstream_request_id
        super().__init__(message)


class VoiceProvider(ABC):
    """Abstract interface for voice providers (STT + TTS)."""

    @abstractmethod
    async def transcribe(
        self, 
        audio_data: bytes, 
        filename: str,
        content_type: str,
        trace_id: Optional[str] = None
    ) -> Tuple[str, Optional[float]]:
        """Transcribe audio to text.
        
        Args:
            audio_data: Raw audio bytes.
            filename: Original filename (for format detection).
            content_type: MIME type of the audio.
            trace_id: Optional trace ID for request correlation.
            
        Returns:
            Tuple of (transcribed_text, duration_seconds).
            
        Raises:
            VoiceProviderError: If transcription fails.
        """
        pass

    @abstractmethod
    async def synthesize(
        self,
        text: str,
        voice: Optional[str] = None,
        format: Optional[str] = None,
        trace_id: Optional[str] = None
    ) -> Tuple[bytes, str]:
        """Synthesize text to speech.
        
        Args:
            text: Text to convert to speech.
            voice: Voice to use (provider-specific).
            format: Output audio format.
            trace_id: Optional trace ID for request correlation.
            
        Returns:
            Tuple of (audio_bytes, mime_type).
            
        Raises:
            VoiceProviderError: If synthesis fails.
        """
        pass


class StubVoiceProvider(VoiceProvider):
    """Stub provider for testing without external dependencies."""

    async def transcribe(
        self, 
        audio_data: bytes, 
        filename: str,
        content_type: str,
        trace_id: Optional[str] = None
    ) -> Tuple[str, Optional[float]]:
        """Return deterministic transcription for testing."""
        # Log metadata only (never log audio content)
        logger.debug(
            f"STUB_STT_REQUEST trace_id={trace_id} "
            f"audio_size={len(audio_data)} filename={filename}"
        )
        
        # Return deterministic response based on audio size
        text = f"Echo Voice (stub): transcribed {len(audio_data)} bytes of audio."
        duration = len(audio_data) / 16000.0  # Assume 16kHz mono
        
        return text, duration

    async def synthesize(
        self,
        text: str,
        voice: Optional[str] = None,
        format: Optional[str] = None,
        trace_id: Optional[str] = None
    ) -> Tuple[bytes, str]:
        """Return deterministic audio for testing."""
        # Log metadata only (never log text content)
        logger.debug(
            f"STUB_TTS_REQUEST trace_id={trace_id} "
            f"text_length={len(text)} voice={voice} format={format}"
        )
        
        # Return minimal valid audio placeholder (silence)
        # This is a tiny valid MP3 frame representing silence
        stub_audio = base64.b64decode(
            "//uQxAAAAAANIAAAAAExBTUUzLjEwMFVVVVVVVVVVVVVVVVVV"
            "VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV"
        )
        
        output_format = format or DEFAULT_TTS_FORMAT
        mime_type = FORMAT_MIME_TYPES.get(output_format, "audio/mpeg")
        
        return stub_audio, mime_type


class OpenAIVoiceProvider(VoiceProvider):
    """OpenAI-backed voice provider using Audio API.
    
    Features:
    - STT via Whisper/gpt-4o-mini-transcribe
    - TTS via gpt-4o-mini-tts
    - Configurable models, voices, and formats via env vars
    - Privacy: never logs audio bytes or transcribed text
    """

    def __init__(self):
        """Initialize with lazy client."""
        self._client = None
        self._stt_model = os.environ.get("OPENAI_STT_MODEL", DEFAULT_STT_MODEL)
        self._tts_model = os.environ.get("OPENAI_TTS_MODEL", DEFAULT_TTS_MODEL)
        self._tts_voice = os.environ.get("OPENAI_TTS_VOICE", DEFAULT_TTS_VOICE)
        self._tts_format = os.environ.get("OPENAI_TTS_FORMAT", DEFAULT_TTS_FORMAT)
        self._timeout = float(os.environ.get("OPENAI_TIMEOUT", DEFAULT_TIMEOUT))

    def _get_client(self):
        """Lazy-init AsyncOpenAI client."""
        if self._client is not None:
            return self._client
        
        from openai import AsyncOpenAI
        
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise VoiceProviderError(
                code="auth_error",
                message="OPENAI_API_KEY not configured"
            )
        
        self._client = AsyncOpenAI(
            api_key=api_key,
            timeout=self._timeout,
            max_retries=2,
        )
        return self._client

    def _map_error(self, e: Exception, upstream_request_id: Optional[str] = None) -> VoiceProviderError:
        """Map OpenAI exceptions to VoiceProviderError."""
        from openai import (
            AuthenticationError,
            RateLimitError,
            APITimeoutError,
            APIConnectionError,
            BadRequestError,
            APIStatusError,
        )
        
        if isinstance(e, AuthenticationError):
            return VoiceProviderError(
                code="auth_error",
                message="OpenAI authentication failed. Check API key.",
                upstream_request_id=upstream_request_id
            )
        elif isinstance(e, RateLimitError):
            return VoiceProviderError(
                code="rate_limit",
                message="OpenAI rate limit exceeded. Please retry later.",
                upstream_request_id=upstream_request_id
            )
        elif isinstance(e, APITimeoutError):
            return VoiceProviderError(
                code="timeout",
                message=f"OpenAI request timed out after {self._timeout}s.",
                upstream_request_id=upstream_request_id
            )
        elif isinstance(e, APIConnectionError):
            return VoiceProviderError(
                code="connection_error",
                message="Failed to connect to OpenAI API.",
                upstream_request_id=upstream_request_id
            )
        elif isinstance(e, BadRequestError):
            return VoiceProviderError(
                code="bad_request",
                message=f"Invalid request to OpenAI: {str(e)}",
                upstream_request_id=upstream_request_id
            )
        elif isinstance(e, APIStatusError):
            return VoiceProviderError(
                code="upstream_error",
                message=f"OpenAI API error (HTTP {e.status_code}): {str(e)}",
                upstream_request_id=upstream_request_id
            )
        else:
            return VoiceProviderError(
                code="unknown_error",
                message=f"Unexpected error: {str(e)}",
                upstream_request_id=upstream_request_id
            )

    async def transcribe(
        self, 
        audio_data: bytes, 
        filename: str,
        content_type: str,
        trace_id: Optional[str] = None
    ) -> Tuple[str, Optional[float]]:
        """Transcribe audio using OpenAI Whisper/transcription API."""
        client = self._get_client()
        upstream_request_id = None
        
        # Log metadata only (never log audio content for privacy)
        logger.info(
            f"OPENAI_STT_REQUEST trace_id={trace_id} "
            f"audio_size={len(audio_data)} model={self._stt_model}"
        )
        
        try:
            # Create file-like object for upload
            from io import BytesIO
            audio_file = BytesIO(audio_data)
            audio_file.name = filename
            
            response = await client.audio.transcriptions.create(
                model=self._stt_model,
                file=audio_file,
            )
            
            # Extract text from response
            text = response.text
            duration = getattr(response, 'duration', None)
            
            logger.info(
                f"OPENAI_STT_SUCCESS trace_id={trace_id} "
                f"text_length={len(text)} duration={duration}"
            )
            
            return text, duration
            
        except VoiceProviderError:
            raise
        except Exception as e:
            logger.error(
                f"OPENAI_STT_ERROR trace_id={trace_id} "
                f"error_type={type(e).__name__}"
            )
            raise self._map_error(e, upstream_request_id)

    async def synthesize(
        self,
        text: str,
        voice: Optional[str] = None,
        format: Optional[str] = None,
        trace_id: Optional[str] = None
    ) -> Tuple[bytes, str]:
        """Synthesize speech using OpenAI TTS API."""
        client = self._get_client()
        upstream_request_id = None
        
        output_voice = voice or self._tts_voice
        output_format = format or self._tts_format
        mime_type = FORMAT_MIME_TYPES.get(output_format, "audio/mpeg")
        
        # Log metadata only (never log text content for privacy)
        logger.info(
            f"OPENAI_TTS_REQUEST trace_id={trace_id} "
            f"text_length={len(text)} voice={output_voice} format={output_format}"
        )
        
        try:
            response = await client.audio.speech.create(
                model=self._tts_model,
                voice=output_voice,
                input=text,
                response_format=output_format,
            )
            
            # Read audio bytes from response
            audio_bytes = response.content
            
            logger.info(
                f"OPENAI_TTS_SUCCESS trace_id={trace_id} "
                f"audio_size={len(audio_bytes)}"
            )
            
            return audio_bytes, mime_type
            
        except VoiceProviderError:
            raise
        except Exception as e:
            logger.error(
                f"OPENAI_TTS_ERROR trace_id={trace_id} "
                f"error_type={type(e).__name__}"
            )
            raise self._map_error(e, upstream_request_id)


# Provider registry and selection logic
_voice_provider_instance: Optional[VoiceProvider] = None


def get_voice_provider() -> VoiceProvider:
    """Get the configured voice provider instance.
    
    Selection logic:
    1. If ECHO_VOICE_PROVIDER explicitly set -> use it
    2. Else if OPENAI_API_KEY exists -> openai provider
    3. Else -> stub provider (for CI/testing)
    
    Returns:
        VoiceProvider instance (cached after first call).
    """
    global _voice_provider_instance
    
    if _voice_provider_instance is not None:
        return _voice_provider_instance
    
    # Check explicit provider override
    provider_name = os.environ.get('ECHO_VOICE_PROVIDER', '').lower()
    
    if provider_name == 'stub':
        _voice_provider_instance = StubVoiceProvider()
        return _voice_provider_instance
    
    if provider_name == 'openai':
        if not os.environ.get('OPENAI_API_KEY'):
            raise RuntimeError(
                "ECHO_VOICE_PROVIDER=openai but OPENAI_API_KEY not set. "
                "Provide the key or use ECHO_VOICE_PROVIDER=stub for testing."
            )
        _voice_provider_instance = OpenAIVoiceProvider()
        return _voice_provider_instance
    
    # Auto-selection based on OPENAI_API_KEY availability
    if os.environ.get('OPENAI_API_KEY'):
        _voice_provider_instance = OpenAIVoiceProvider()
    else:
        # Fallback to stub for CI/testing
        _voice_provider_instance = StubVoiceProvider()
    
    return _voice_provider_instance


def get_voice_provider_name() -> str:
    """Get the name of the active voice provider."""
    provider = get_voice_provider()
    if isinstance(provider, StubVoiceProvider):
        return "stub"
    elif isinstance(provider, OpenAIVoiceProvider):
        return "openai"
    return "unknown"


def reset_voice_provider() -> None:
    """Reset the cached provider instance. Used for testing."""
    global _voice_provider_instance
    _voice_provider_instance = None
