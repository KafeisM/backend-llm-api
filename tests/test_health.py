"""
Tests for the GET /health endpoint.

Verifies that the health check returns the expected
status payload and HTTP 200.
"""


class TestHealthEndpoint:
    """Health endpoint should always respond quickly with status ok."""

    def test_health_returns_200(self, client):
        """GET /health returns HTTP 200."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_returns_status_ok(self, client):
        """GET /health response body contains {"status": "ok"}."""
        response = client.get("/health")
        data = response.json()
        assert data == {"status": "ok"}

    def test_health_content_type_is_json(self, client):
        """GET /health returns application/json content type."""
        response = client.get("/health")
        assert "application/json" in response.headers["content-type"]
