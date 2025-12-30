import math
import os
from datetime import datetime
from typing import Dict, Optional

# ---------------------------------------------------------------------------
# Strict-mode flags: when set, missing Typesense config raises at init time.
# Default (CI/dev): Typesense is optional; errors only when search is used.
# ---------------------------------------------------------------------------
_REQUIRE_SECRETS = os.environ.get('ECHO_REQUIRE_SECRETS', '').lower() in ('1', 'true')
_REQUIRE_TYPESENSE = os.environ.get('ECHO_REQUIRE_TYPESENSE', '').lower() in ('1', 'true') or _REQUIRE_SECRETS

# Lazy-initialized Typesense client
_client: Optional[object] = None
_client_loaded: bool = False


def _get_typesense_client():
    """Return the Typesense client, creating it lazily on first call.

    Returns:
        Typesense client instance, or None if not configured and not in strict mode.

    Raises:
        RuntimeError: If Typesense is not configured and strict mode is enabled.
    """
    global _client, _client_loaded

    if not _client_loaded:
        api_key = os.getenv('TYPESENSE_API_KEY')
        host = os.getenv('TYPESENSE_HOST')
        port = os.getenv('TYPESENSE_HOST_PORT')

        if not api_key:
            _client_loaded = True
            if _REQUIRE_TYPESENSE:
                raise RuntimeError(
                    "TYPESENSE_API_KEY is required but not set. "
                    "Set the env var or disable ECHO_REQUIRE_TYPESENSE / ECHO_REQUIRE_SECRETS."
                )
            _client = None
        else:
            # Import lazily to avoid import-time validation
            import typesense
            _client = typesense.Client(
                {
                    'nodes': [{'host': host, 'port': port, 'protocol': 'https'}],
                    'api_key': api_key,
                    'connection_timeout_seconds': 2,
                }
            )
            _client_loaded = True

    return _client


# Backward-compat: `client` is now a lazy proxy
class _LazyTypesenseClient:
    """Proxy that defers Typesense client creation until first attribute access."""

    def __getattr__(self, name):
        c = _get_typesense_client()
        if c is None:
            raise RuntimeError(
                "Typesense client not available. TYPESENSE_API_KEY is not configured. "
                "Search functionality is disabled."
            )
        return getattr(c, name)


client = _LazyTypesenseClient()


def search_conversations(
    uid: str,
    query: str,
    page: int = 1,
    per_page: int = 10,
    include_discarded: bool = True,
    start_date: int = None,
    end_date: int = None,
) -> Dict:
    try:

        filter_by = f'userId:={uid}'
        if not include_discarded:
            filter_by = filter_by + ' && discarded:=false'

        # Add date range filters if provided
        if start_date is not None:
            filter_by = filter_by + f' && created_at:>={start_date}'
        if end_date is not None:
            filter_by = filter_by + f' && created_at:<={end_date}'

        search_parameters = {
            'q': query,
            'query_by': 'structured.overview, structured.title',
            'filter_by': filter_by,
            'sort_by': 'created_at:desc',
            'per_page': per_page,
            'page': page,
        }

        results = client.collections['conversations'].documents.search(search_parameters)
        memories = []
        for item in results['hits']:
            item['document']['created_at'] = datetime.utcfromtimestamp(item['document']['created_at']).isoformat()
            item['document']['started_at'] = datetime.utcfromtimestamp(item['document']['started_at']).isoformat()
            item['document']['finished_at'] = datetime.utcfromtimestamp(item['document']['finished_at']).isoformat()
            memories.append(item['document'])
        return {
            'items': memories,
            'total_pages': math.ceil(results['found'] / per_page),
            'current_page': page,
            'per_page': per_page,
        }
    except Exception as e:
        raise Exception(f"Failed to search conversations: {str(e)}")
