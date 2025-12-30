import os
from typing import Any, Callable, Dict, List

from langchain_core.output_parsers import PydanticOutputParser
import tiktoken

from models.conversation import Structured

# ---------------------------------------------------------------------------
# Strict-mode flags: when set, missing API keys raise at init time.
# Default (CI/dev): secrets are optional; errors only when functionality is used.
# ---------------------------------------------------------------------------
_REQUIRE_SECRETS = os.environ.get('ECHO_REQUIRE_SECRETS', '').lower() in ('1', 'true')
_REQUIRE_OPENAI = os.environ.get('ECHO_REQUIRE_OPENAI', '').lower() in ('1', 'true') or _REQUIRE_SECRETS


def _check_openai_key() -> None:
    """Raise if OPENAI_API_KEY is missing and strict mode is enabled."""
    if _REQUIRE_OPENAI and not os.environ.get('OPENAI_API_KEY'):
        raise RuntimeError(
            "OPENAI_API_KEY is required but not set. "
            "Set the env var or disable ECHO_REQUIRE_OPENAI / ECHO_REQUIRE_SECRETS."
        )


# ---------------------------------------------------------------------------
# Lazy client cache
# ---------------------------------------------------------------------------
_llm_cache: Dict[str, Any] = {}


def _get_or_create(name: str, factory: Callable[[], Any]) -> Any:
    """Return cached LLM client, creating lazily on first access."""
    if name not in _llm_cache:
        _check_openai_key()  # validate before creating client
        _llm_cache[name] = factory()
    return _llm_cache[name]


# ---------------------------------------------------------------------------
# Lazy proxy: allows `from utils.llm.clients import llm_mini` to keep working
# ---------------------------------------------------------------------------
class _LazyLLM:
    """Proxy that defers LLM client creation until first attribute access."""

    def __init__(self, name: str, factory: Callable[[], Any]):
        object.__setattr__(self, '_name', name)
        object.__setattr__(self, '_factory', factory)

    def _get_client(self) -> Any:
        return _get_or_create(self._name, self._factory)

    def __getattr__(self, attr: str) -> Any:
        return getattr(self._get_client(), attr)

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        return self._get_client()(*args, **kwargs)

    def __or__(self, other: Any) -> Any:
        """Support pipe operator for LangChain chains (llm | parser)."""
        return self._get_client() | other

    def __ror__(self, other: Any) -> Any:
        """Support reverse pipe operator."""
        return other | self._get_client()


# ---------------------------------------------------------------------------
# Factory functions (import lazily to avoid import-time OpenAI validation)
# ---------------------------------------------------------------------------
def _make_llm_mini():
    from langchain_openai import ChatOpenAI
    return ChatOpenAI(model='gpt-4.1-mini')


def _make_llm_mini_stream():
    from langchain_openai import ChatOpenAI
    return ChatOpenAI(model='gpt-4.1-mini', streaming=True)


def _make_llm_large():
    from langchain_openai import ChatOpenAI
    return ChatOpenAI(model='o1-preview')


def _make_llm_large_stream():
    from langchain_openai import ChatOpenAI
    return ChatOpenAI(model='o1-preview', streaming=True, temperature=1)


def _make_llm_high():
    from langchain_openai import ChatOpenAI
    return ChatOpenAI(model='o4-mini')


def _make_llm_high_stream():
    from langchain_openai import ChatOpenAI
    return ChatOpenAI(model='o4-mini', streaming=True, temperature=1)


def _make_llm_medium():
    from langchain_openai import ChatOpenAI
    return ChatOpenAI(model='gpt-4.1')


def _make_llm_medium_stream():
    from langchain_openai import ChatOpenAI
    return ChatOpenAI(model='gpt-4.1', streaming=True)


def _make_llm_medium_experiment():
    from langchain_openai import ChatOpenAI
    return ChatOpenAI(model='gpt-5.1')


def _make_llm_agent():
    from langchain_openai import ChatOpenAI
    return ChatOpenAI(model='gpt-5.1')


def _make_llm_agent_stream():
    from langchain_openai import ChatOpenAI
    return ChatOpenAI(model='gpt-5.1', streaming=True)


def _make_llm_persona_mini_stream():
    from langchain_openai import ChatOpenAI
    return ChatOpenAI(
        temperature=0.8,
        model="google/gemini-flash-1.5-8b",
        api_key=os.environ.get('OPENROUTER_API_KEY'),
        base_url="https://openrouter.ai/api/v1",
        default_headers={"X-Title": "Omi Chat"},
        streaming=True,
    )


def _make_llm_persona_medium_stream():
    from langchain_openai import ChatOpenAI
    return ChatOpenAI(
        temperature=0.8,
        model="anthropic/claude-3.5-sonnet",
        api_key=os.environ.get('OPENROUTER_API_KEY'),
        base_url="https://openrouter.ai/api/v1",
        default_headers={"X-Title": "Omi Chat"},
        streaming=True,
    )


def _make_llm_gemini_flash():
    from langchain_openai import ChatOpenAI
    return ChatOpenAI(
        temperature=0.7,
        model="google/gemini-3-flash-preview",
        api_key=os.environ.get('OPENROUTER_API_KEY'),
        base_url="https://openrouter.ai/api/v1",
        default_headers={"X-Title": "Omi Wrapped"},
    )


def _make_embeddings():
    from langchain_openai import OpenAIEmbeddings
    return OpenAIEmbeddings(model="text-embedding-3-large")


# ---------------------------------------------------------------------------
# Public lazy-initialized clients (backward-compatible exports)
# ---------------------------------------------------------------------------
# Base models for general use
llm_mini = _LazyLLM('llm_mini', _make_llm_mini)
llm_mini_stream = _LazyLLM('llm_mini_stream', _make_llm_mini_stream)
llm_large = _LazyLLM('llm_large', _make_llm_large)
llm_large_stream = _LazyLLM('llm_large_stream', _make_llm_large_stream)
llm_high = _LazyLLM('llm_high', _make_llm_high)
llm_high_stream = _LazyLLM('llm_high_stream', _make_llm_high_stream)
llm_medium = _LazyLLM('llm_medium', _make_llm_medium)
llm_medium_stream = _LazyLLM('llm_medium_stream', _make_llm_medium_stream)
llm_medium_experiment = _LazyLLM('llm_medium_experiment', _make_llm_medium_experiment)

# Specialized models for agentic workflows
llm_agent = _LazyLLM('llm_agent', _make_llm_agent)
llm_agent_stream = _LazyLLM('llm_agent_stream', _make_llm_agent_stream)
llm_persona_mini_stream = _LazyLLM('llm_persona_mini_stream', _make_llm_persona_mini_stream)
llm_persona_medium_stream = _LazyLLM('llm_persona_medium_stream', _make_llm_persona_medium_stream)

# Gemini models for large context analysis
llm_gemini_flash = _LazyLLM('llm_gemini_flash', _make_llm_gemini_flash)

# Embeddings (also lazy)
embeddings = _LazyLLM('embeddings', _make_embeddings)

# Parser and encoding (no secrets needed)
parser = PydanticOutputParser(pydantic_object=Structured)
encoding = tiktoken.encoding_for_model('gpt-4')


def num_tokens_from_string(string: str) -> int:
    """Returns the number of tokens in a text string."""
    num_tokens = len(encoding.encode(string))
    return num_tokens


def generate_embedding(content: str) -> List[float]:
    return embeddings.embed_documents([content])[0]
