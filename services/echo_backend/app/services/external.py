"""External service integration placeholders.

These modules provide timeout-safe patterns for future external API calls
(web search, email, weather, calendar, etc.).
"""

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

# Default timeout for external calls (seconds)
DEFAULT_TIMEOUT = 10.0


class ExternalServiceError(Exception):
    """Raised when an external service call fails."""

    pass


async def call_external_api(
    url: str,
    method: str = "GET",
    *,
    timeout: float = DEFAULT_TIMEOUT,
    headers: dict[str, str] | None = None,
    json_body: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Make a timeout-safe external API call.

    Args:
        url: The URL to call.
        method: HTTP method (GET, POST, etc.).
        timeout: Request timeout in seconds.
        headers: Optional request headers.
        json_body: Optional JSON body for POST/PUT requests.

    Returns:
        JSON response as dictionary.

    Raises:
        ExternalServiceError: If the call fails or times out.
    """
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.request(
                method=method,
                url=url,
                headers=headers,
                json=json_body,
            )
            response.raise_for_status()
            return response.json()
    except httpx.TimeoutException as e:
        logger.error("External API timeout", extra={"url": url, "timeout": timeout})
        raise ExternalServiceError(f"Request timed out after {timeout}s") from e
    except httpx.HTTPStatusError as e:
        logger.error(
            "External API error",
            extra={"url": url, "status": e.response.status_code},
        )
        raise ExternalServiceError(f"HTTP {e.response.status_code}") from e
    except Exception as e:
        logger.error("External API unexpected error", extra={"url": url, "error": str(e)})
        raise ExternalServiceError(str(e)) from e


# Placeholder tool functions for future LLM integration
# These will be called by the LLM to perform actions


async def web_search(query: str) -> dict[str, Any]:
    """Search the web (placeholder).

    Will be integrated with a search API in future phases.
    """
    logger.info("Web search placeholder called", extra={"query": query})
    return {
        "status": "placeholder",
        "message": "Web search not yet implemented",
        "query": query,
    }


async def send_email(to: str, subject: str, body: str) -> dict[str, Any]:
    """Send an email (placeholder).

    Will be integrated with an email service in future phases.
    """
    logger.info(
        "Send email placeholder called",
        extra={"to": to, "subject": subject, "body_length": len(body)},
    )
    return {
        "status": "placeholder",
        "message": "Email sending not yet implemented",
        "to": to,
        "subject": subject,
    }


async def get_weather(location: str) -> dict[str, Any]:
    """Get weather information (placeholder).

    Will be integrated with a weather API in future phases.
    """
    logger.info("Weather placeholder called", extra={"location": location})
    return {
        "status": "placeholder",
        "message": "Weather API not yet implemented",
        "location": location,
    }
