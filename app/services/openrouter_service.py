"""
OpenRouter LLM integration service.

Handles all communication with the OpenRouter API.
This module isolates the external HTTP calls so that:
- Route handlers never deal with raw LLM logic
- Timeouts, retries, and errors are handled in one place
- The service can be easily mocked in tests

OpenRouter API docs: https://openrouter.ai/docs
"""

import httpx

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# OpenRouter chat completions endpoint
CHAT_COMPLETIONS_URL = f"{settings.openrouter_base_url}/chat/completions"


class OpenRouterError(Exception):
    """Raised when OpenRouter returns a non-successful response."""

    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"OpenRouter error {status_code}: {detail}")


async def call_openrouter(
    messages: list[dict[str, str]],
) -> dict:
    """Send a chat completion request to OpenRouter.

    Args:
        messages: List of message dicts with 'role' and 'content' keys.
                  Example: [{"role": "system", "content": "..."}, 
                            {"role": "user", "content": "..."}]

    Returns:
        The full JSON response from OpenRouter.

    Raises:
        OpenRouterError: If the API returns a non-200 status.
        httpx.TimeoutException: If the request exceeds the configured timeout.
        httpx.ConnectError: If the API is unreachable.
    """
    # Build the request payload
    payload = {
        "model": settings.openrouter_model,
        "messages": messages,
    }

    # Build headers with API key
    headers = {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "Content-Type": "application/json",
        # OpenRouter recommends these for tracking
        "HTTP-Referer": "https://github.com/backend-llm-api",
        "X-Title": "Backend LLM API",
    }

    logger.info(
        "Calling OpenRouter | model=%s | messages=%d | timeout=%ds",
        settings.openrouter_model,
        len(messages),
        settings.openrouter_timeout,
    )

    # Make the async HTTP request
    async with httpx.AsyncClient() as client:
        response = await client.post(
            CHAT_COMPLETIONS_URL,
            json=payload,
            headers=headers,
            timeout=settings.openrouter_timeout,
        )

    # Handle non-200 responses
    if response.status_code != 200:
        error_detail = response.text[:500]  # Limit error detail length
        logger.error(
            "OpenRouter returned %d: %s",
            response.status_code,
            error_detail,
        )
        raise OpenRouterError(
            status_code=response.status_code,
            detail=error_detail,
        )

    result = response.json()
    logger.info("OpenRouter response received successfully")
    return result


def extract_message(response: dict) -> str:
    """Extract the assistant's message text from the OpenRouter response.

    The OpenRouter API returns a response in this format:
    {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "The actual response text..."
                }
            }
        ]
    }

    Args:
        response: The full JSON response from OpenRouter.

    Returns:
        The assistant's message content as a string.

    Raises:
        KeyError: If the response format is unexpected.
    """
    try:
        content = response["choices"][0]["message"]["content"]
        return content.strip()
    except (KeyError, IndexError, TypeError) as e:
        logger.error("Failed to extract message from response: %s", e)
        logger.error("Response structure: %s", response)
        raise KeyError(f"Unexpected OpenRouter response format: {e}") from e
