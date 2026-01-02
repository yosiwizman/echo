"""CORS tests for Echo backend.

These tests validate that the CORS middleware is properly configured
to allow the Echo Web UI to make cross-origin requests.
"""

from fastapi.testclient import TestClient

from main import app


# Test origins
ALLOWED_ORIGIN = "https://echo-web-staging-zxuvsjb5qa-ew.a.run.app"
DISALLOWED_ORIGIN = "https://evil-site.example.com"


class TestCORSPreflight:
    """Test CORS preflight (OPTIONS) requests."""

    def test_preflight_health_allowed_origin(self) -> None:
        """OPTIONS /health with allowed origin should return CORS headers."""
        client = TestClient(app)
        resp = client.options(
            "/health",
            headers={
                "Origin": ALLOWED_ORIGIN,
                "Access-Control-Request-Method": "GET",
            },
        )
        # Preflight should succeed
        assert resp.status_code == 200
        # Should include CORS headers
        assert "access-control-allow-origin" in resp.headers
        assert resp.headers["access-control-allow-origin"] == ALLOWED_ORIGIN

    def test_preflight_health_disallowed_origin(self) -> None:
        """OPTIONS /health with disallowed origin should not include CORS headers for that origin."""
        client = TestClient(app)
        resp = client.options(
            "/health",
            headers={
                "Origin": DISALLOWED_ORIGIN,
                "Access-Control-Request-Method": "GET",
            },
        )
        # FastAPI's CORSMiddleware returns 400 for disallowed origins on preflight
        # This is valid CORS behavior - the browser will block the request
        assert resp.status_code in [200, 400]
        # Access-Control-Allow-Origin should NOT be present or should not match
        acao = resp.headers.get("access-control-allow-origin", "")
        assert acao != DISALLOWED_ORIGIN

    def test_preflight_brain_chat_allowed_origin(self) -> None:
        """OPTIONS /v1/brain/chat with allowed origin should return CORS headers."""
        client = TestClient(app)
        resp = client.options(
            "/v1/brain/chat",
            headers={
                "Origin": ALLOWED_ORIGIN,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type",
            },
        )
        assert resp.status_code == 200
        assert resp.headers.get("access-control-allow-origin") == ALLOWED_ORIGIN
        # Should allow the requested headers
        allowed_headers = resp.headers.get("access-control-allow-headers", "").lower()
        assert "content-type" in allowed_headers


class TestCORSActualRequests:
    """Test CORS headers on actual (non-preflight) requests."""

    def test_get_health_with_allowed_origin(self) -> None:
        """GET /health with allowed Origin header should include CORS headers."""
        client = TestClient(app)
        resp = client.get(
            "/health",
            headers={"Origin": ALLOWED_ORIGIN},
        )
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}
        # Should include CORS header and credentials support
        assert resp.headers.get("access-control-allow-origin") == ALLOWED_ORIGIN
        assert resp.headers.get("access-control-allow-credentials", "").lower() == "true"

    def test_get_health_with_disallowed_origin(self) -> None:
        """GET /health with disallowed Origin should not include CORS headers."""
        client = TestClient(app)
        resp = client.get(
            "/health",
            headers={"Origin": DISALLOWED_ORIGIN},
        )
        assert resp.status_code == 200
        # Response works, but no CORS header for disallowed origin
        acao = resp.headers.get("access-control-allow-origin", "")
        assert acao != DISALLOWED_ORIGIN

    def test_post_brain_chat_with_allowed_origin(self) -> None:
        """POST /v1/brain/chat with allowed Origin should include CORS headers."""
        client = TestClient(app)
        resp = client.post(
            "/v1/brain/chat",
            headers={
                "Origin": ALLOWED_ORIGIN,
                "Content-Type": "application/json",
            },
            json={
                "messages": [{"role": "user", "content": "hello"}],
            },
        )
        # Request should succeed (200 or at worst 500 if provider fails)
        assert resp.status_code in [200, 500]
        # Should include CORS header
        assert resp.headers.get("access-control-allow-origin") == ALLOWED_ORIGIN

    def test_localhost_origin_allowed(self) -> None:
        """Local dev origin (localhost:5173) should be allowed."""
        client = TestClient(app)
        local_origin = "http://localhost:5173"
        resp = client.get(
            "/health",
            headers={"Origin": local_origin},
        )
        assert resp.status_code == 200
        assert resp.headers.get("access-control-allow-origin") == local_origin


class TestCORSMaxAge:
    """Test CORS max-age caching."""

    def test_preflight_includes_max_age(self) -> None:
        """Preflight response should include Access-Control-Max-Age."""
        client = TestClient(app)
        resp = client.options(
            "/health",
            headers={
                "Origin": ALLOWED_ORIGIN,
                "Access-Control-Request-Method": "GET",
            },
        )
        assert resp.status_code == 200
        max_age = resp.headers.get("access-control-max-age")
        assert max_age is not None
        assert int(max_age) >= 600  # At least 10 minutes
