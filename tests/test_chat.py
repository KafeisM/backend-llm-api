"""
Tests for the POST /chat/ endpoint.

Covers:
- Request validation (missing/empty/too-long messages)
- Successful chat flow with OpenRouter mocked
- Error handling for upstream failures (timeout, API error, bad response)

All tests mock OpenRouter so they run without a real API key.
"""

from unittest.mock import AsyncMock, patch

import httpx

from app.services.openrouter_service import OpenRouterError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_openrouter_response(content: str = "This is a test response.") -> dict:
    """Build a fake OpenRouter response matching the real API shape."""
    return {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": content,
                }
            }
        ]
    }


# ---------------------------------------------------------------------------
# Request validation
# ---------------------------------------------------------------------------

class TestChatValidation:
    """POST /chat/ should reject invalid payloads with 422."""

    def test_missing_body_returns_422(self, client):
        response = client.post("/chat/")
        assert response.status_code == 422

    def test_empty_message_returns_422(self, client):
        response = client.post("/chat/", json={"message": ""})
        assert response.status_code == 422

    def test_missing_message_field_returns_422(self, client):
        response = client.post("/chat/", json={"text": "hello"})
        assert response.status_code == 422

    def test_message_too_long_returns_422(self, client):
        long_message = "x" * 2001  # max_length is 2000
        response = client.post("/chat/", json={"message": long_message})
        assert response.status_code == 422

    def test_422_response_has_error_structure(self, client):
        """Validation errors should use our consistent error format."""
        response = client.post("/chat/", json={"message": ""})
        data = response.json()
        assert "error" in data
        assert data["error"] == "VALIDATION_ERROR"
        assert "detail" in data


# ---------------------------------------------------------------------------
# Successful chat flow (OpenRouter mocked)
# ---------------------------------------------------------------------------

class TestChatSuccess:
    """POST /chat/ with valid input and mocked OpenRouter."""

    @patch("app.services.chat_service.call_openrouter", new_callable=AsyncMock)
    def test_returns_200_with_valid_message(self, mock_call, client):
        mock_call.return_value = _mock_openrouter_response()
        response = client.post(
            "/chat/", json={"message": "How many partners does the company have?"}
        )
        assert response.status_code == 200

    @patch("app.services.chat_service.call_openrouter", new_callable=AsyncMock)
    def test_response_has_required_fields(self, mock_call, client):
        mock_call.return_value = _mock_openrouter_response("The company has 5 partners.")
        response = client.post(
            "/chat/", json={"message": "How many partners does the company have?"}
        )
        data = response.json()
        assert "message" in data
        assert data["message"] == "The company has 5 partners."
        assert "model" in data
        assert "used_context" in data
        assert "sources" in data

    @patch("app.services.chat_service.call_openrouter", new_callable=AsyncMock)
    def test_uses_context_for_known_topics(self, mock_call, client):
        """When the query matches knowledge entries, used_context should be True."""
        mock_call.return_value = _mock_openrouter_response()
        response = client.post(
            "/chat/", json={"message": "What is the vacation policy?"}
        )
        data = response.json()
        assert data["used_context"] is True
        assert len(data["sources"]) > 0

    @patch("app.services.chat_service.call_openrouter", new_callable=AsyncMock)
    def test_no_context_for_unknown_topics(self, mock_call, client):
        """When the query doesn't match anything, used_context should be False."""
        mock_call.return_value = _mock_openrouter_response()
        response = client.post(
            "/chat/", json={"message": "xyzzy foobar nonsense gibberish"}
        )
        data = response.json()
        assert data["used_context"] is False
        assert data["sources"] == []

    @patch("app.services.chat_service.call_openrouter", new_callable=AsyncMock)
    def test_openrouter_called_with_messages(self, mock_call, client):
        """Verify OpenRouter is called with a properly structured messages list."""
        mock_call.return_value = _mock_openrouter_response()
        client.post("/chat/", json={"message": "Hello"})

        mock_call.assert_called_once()
        messages = mock_call.call_args[0][0]
        assert isinstance(messages, list)
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        assert "Hello" in messages[1]["content"]


# ---------------------------------------------------------------------------
# Error handling (upstream failures)
# ---------------------------------------------------------------------------

class TestChatErrorHandling:
    """POST /chat/ should handle upstream failures gracefully."""

    @patch("app.services.chat_service.call_openrouter", new_callable=AsyncMock)
    def test_openrouter_error_returns_502(self, mock_call, client):
        """OpenRouter API error → 502 Bad Gateway."""
        mock_call.side_effect = OpenRouterError(
            status_code=429, detail="Rate limited"
        )
        response = client.post(
            "/chat/", json={"message": "Hello"}
        )
        assert response.status_code == 502
        data = response.json()
        assert data["detail"]["error"] == "UPSTREAM_LLM_ERROR"

    @patch("app.services.chat_service.call_openrouter", new_callable=AsyncMock)
    def test_timeout_returns_504(self, mock_call, client):
        """OpenRouter timeout → 504 Gateway Timeout."""
        mock_call.side_effect = httpx.ReadTimeout("read timed out")
        response = client.post(
            "/chat/", json={"message": "Hello"}
        )
        assert response.status_code == 504
        data = response.json()
        assert data["detail"]["error"] == "UPSTREAM_TIMEOUT"

    @patch("app.services.chat_service.call_openrouter", new_callable=AsyncMock)
    def test_connection_error_returns_502(self, mock_call, client):
        """OpenRouter unreachable → 502 Bad Gateway."""
        mock_call.side_effect = httpx.ConnectError("connection refused")
        response = client.post(
            "/chat/", json={"message": "Hello"}
        )
        assert response.status_code == 502
        data = response.json()
        assert data["detail"]["error"] == "UPSTREAM_UNREACHABLE"

    @patch("app.services.chat_service.call_openrouter", new_callable=AsyncMock)
    def test_invalid_response_format_returns_502(self, mock_call, client):
        """Unexpected OpenRouter response shape → 502."""
        mock_call.return_value = {"unexpected": "format"}
        response = client.post(
            "/chat/", json={"message": "Hello"}
        )
        assert response.status_code == 502
        data = response.json()
        assert data["detail"]["error"] == "UPSTREAM_INVALID_RESPONSE"
