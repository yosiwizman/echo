"""Tests for Brain API authentication (PIN + JWT)."""
import time

import bcrypt
import pytest
from fastapi.testclient import TestClient


# Test PIN and its bcrypt hash
TEST_PIN = "12345678"
TEST_PIN_HASH = bcrypt.hashpw(TEST_PIN.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
TEST_JWT_SECRET = "test-jwt-secret-that-is-at-least-32-characters-long"


@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    """Set up test environment for all auth tests."""
    monkeypatch.setenv("ECHO_BRAIN_PROVIDER", "stub")
    # Clear cached settings
    from utils.auth.settings import get_auth_settings
    get_auth_settings.cache_clear()


@pytest.fixture
def auth_enabled_env(monkeypatch):
    """Enable auth with test credentials."""
    monkeypatch.setenv("AUTH_REQUIRED", "true")
    monkeypatch.setenv("AUTH_JWT_SECRET", TEST_JWT_SECRET)
    monkeypatch.setenv("AUTH_PIN_HASH", TEST_PIN_HASH)
    from utils.auth.settings import get_auth_settings
    get_auth_settings.cache_clear()
    yield
    get_auth_settings.cache_clear()


@pytest.fixture
def auth_disabled_env(monkeypatch):
    """Disable auth (default state)."""
    monkeypatch.setenv("AUTH_REQUIRED", "false")
    monkeypatch.setenv("AUTH_JWT_SECRET", TEST_JWT_SECRET)
    monkeypatch.setenv("AUTH_PIN_HASH", TEST_PIN_HASH)
    from utils.auth.settings import get_auth_settings
    get_auth_settings.cache_clear()
    yield
    get_auth_settings.cache_clear()


@pytest.fixture
def rate_limiter_reset():
    """Reset rate limiter before each test and restore original config."""
    from utils.auth.rate_limiter import login_rate_limiter, RateLimitConfig
    # Save original config
    original_config = login_rate_limiter.config
    # Clear all rate limit data
    login_rate_limiter._attempts.clear()
    yield
    # Restore original config and clear attempts
    login_rate_limiter.config = original_config
    login_rate_limiter._attempts.clear()


class TestLogin:
    """Tests for POST /v1/auth/login."""
    
    def test_login_success(self, auth_enabled_env, rate_limiter_reset):
        """Test successful login with correct PIN."""
        from main import app
        client = TestClient(app)
        
        resp = client.post("/v1/auth/login", json={"pin": TEST_PIN})
        
        assert resp.status_code == 200
        data = resp.json()
        assert data["ok"] is True
        assert "token" in data
        assert "expires_at" in data
        assert "runtime" in data
        # Token should be a JWT (3 parts separated by dots)
        assert len(data["token"].split(".")) == 3
    
    def test_login_invalid_pin(self, auth_enabled_env, rate_limiter_reset):
        """Test login with wrong PIN returns 401."""
        from main import app
        client = TestClient(app)
        
        resp = client.post("/v1/auth/login", json={"pin": "wrongpin"})
        
        assert resp.status_code == 401
        data = resp.json()["detail"]
        assert data["ok"] is False
        assert data["error"]["code"] == "invalid_pin"
    
    def test_login_rate_limit(self, auth_enabled_env, rate_limiter_reset, monkeypatch):
        """Test rate limiting on login attempts."""
        from main import app
        from utils.auth.rate_limiter import login_rate_limiter, RateLimitConfig
        
        # Configure a very low rate limit for testing
        login_rate_limiter.config = RateLimitConfig(max_attempts=3, window_seconds=60)
        
        client = TestClient(app)
        
        # Make 3 failed attempts
        for _ in range(3):
            client.post("/v1/auth/login", json={"pin": "wrongpin"})
        
        # 4th attempt should be rate limited
        resp = client.post("/v1/auth/login", json={"pin": "wrongpin"})
        
        assert resp.status_code == 429
        data = resp.json()["detail"]
        assert data["ok"] is False
        assert data["error"]["code"] == "rate_limit"
        assert "retry_after" in data["error"]
        assert "Retry-After" in resp.headers
    
    def test_login_resets_rate_limit_on_success(self, auth_enabled_env, rate_limiter_reset, monkeypatch):
        """Test that successful login resets rate limit."""
        from main import app
        from utils.auth.rate_limiter import login_rate_limiter, RateLimitConfig
        
        # Configure low rate limit
        login_rate_limiter.config = RateLimitConfig(max_attempts=3, window_seconds=60)
        
        client = TestClient(app)
        
        # Make 2 failed attempts
        for _ in range(2):
            client.post("/v1/auth/login", json={"pin": "wrongpin"})
        
        # Successful login
        resp = client.post("/v1/auth/login", json={"pin": TEST_PIN})
        assert resp.status_code == 200
        
        # Should be able to make more attempts now (rate limit reset)
        resp = client.post("/v1/auth/login", json={"pin": "wrongpin"})
        assert resp.status_code == 401  # Not 429


class TestProtectedEndpoints:
    """Tests for protected /v1/brain/* endpoints."""
    
    def test_chat_requires_auth_when_enabled(self, auth_enabled_env, rate_limiter_reset):
        """Test that /v1/brain/chat requires auth when AUTH_REQUIRED=true."""
        from main import app
        client = TestClient(app)
        
        # No token - should fail
        resp = client.post("/v1/brain/chat", json={
            "messages": [{"role": "user", "content": "Hello"}]
        })
        
        assert resp.status_code == 401
        data = resp.json()["detail"]
        assert data["ok"] is False
        assert data["error"]["code"] == "auth_required"
    
    def test_chat_works_with_valid_token(self, auth_enabled_env, rate_limiter_reset):
        """Test that /v1/brain/chat works with valid token."""
        from main import app
        client = TestClient(app)
        
        # Get token
        login_resp = client.post("/v1/auth/login", json={"pin": TEST_PIN})
        token = login_resp.json()["token"]
        
        # Use token
        resp = client.post(
            "/v1/brain/chat",
            json={"messages": [{"role": "user", "content": "Hello"}]},
            headers={"Authorization": f"Bearer {token}"},
        )
        
        assert resp.status_code == 200
        assert resp.json()["ok"] is True
    
    def test_chat_rejects_invalid_token(self, auth_enabled_env, rate_limiter_reset):
        """Test that /v1/brain/chat rejects invalid token."""
        from main import app
        client = TestClient(app)
        
        resp = client.post(
            "/v1/brain/chat",
            json={"messages": [{"role": "user", "content": "Hello"}]},
            headers={"Authorization": "Bearer invalid.token.here"},
        )
        
        assert resp.status_code == 401
        data = resp.json()["detail"]
        assert data["error"]["code"] == "invalid_token"
    
    def test_chat_allows_unauthenticated_when_disabled(self, auth_disabled_env):
        """Test that /v1/brain/chat allows unauthenticated when AUTH_REQUIRED=false."""
        from main import app
        client = TestClient(app)
        
        resp = client.post("/v1/brain/chat", json={
            "messages": [{"role": "user", "content": "Hello"}]
        })
        
        assert resp.status_code == 200
        assert resp.json()["ok"] is True
    
    def test_stream_requires_auth_when_enabled(self, auth_enabled_env, rate_limiter_reset):
        """Test that /v1/brain/chat/stream requires auth when AUTH_REQUIRED=true."""
        from main import app
        client = TestClient(app)
        
        resp = client.post("/v1/brain/chat/stream", json={
            "messages": [{"role": "user", "content": "Hello"}]
        })
        
        assert resp.status_code == 401


class TestPublicEndpoints:
    """Tests that public endpoints remain accessible."""
    
    def test_health_is_public(self, auth_enabled_env):
        """Test that /health remains public even with auth enabled."""
        from main import app
        client = TestClient(app)
        
        resp = client.get("/health")
        
        assert resp.status_code == 200
    
    def test_version_is_public(self, auth_enabled_env):
        """Test that /version remains public even with auth enabled."""
        from main import app
        client = TestClient(app)
        
        resp = client.get("/version")
        
        assert resp.status_code == 200
    
    def test_brain_health_is_public(self, auth_enabled_env):
        """Test that /v1/brain/health remains public even with auth enabled."""
        from main import app
        client = TestClient(app)
        
        resp = client.get("/v1/brain/health")
        
        assert resp.status_code == 200


class TestJWTHandler:
    """Unit tests for JWT creation and verification."""
    
    def test_create_and_verify_token(self, auth_enabled_env):
        """Test token creation and verification roundtrip."""
        from utils.auth.jwt_handler import create_access_token, verify_access_token
        
        token, exp = create_access_token(subject="test-user")
        payload = verify_access_token(token)
        
        assert payload.sub == "test-user"
        assert payload.jti  # Should have a JTI
    
    def test_expired_token_rejected(self, auth_enabled_env):
        """Test that expired tokens are rejected."""
        from utils.auth.jwt_handler import create_access_token, verify_access_token, JWTExpiredError
        
        # Create token that expires immediately
        token, _ = create_access_token(ttl_seconds=0)
        
        # Wait a moment
        time.sleep(0.1)
        
        with pytest.raises(JWTExpiredError):
            verify_access_token(token)
    
    def test_tampered_token_rejected(self, auth_enabled_env):
        """Test that tampered tokens are rejected."""
        from utils.auth.jwt_handler import create_access_token, verify_access_token, JWTInvalidError
        
        token, _ = create_access_token()
        
        # Tamper with the token
        parts = token.split(".")
        parts[1] = parts[1] + "tampered"
        tampered = ".".join(parts)
        
        with pytest.raises(JWTInvalidError):
            verify_access_token(tampered)


class TestRateLimiter:
    """Unit tests for rate limiter."""
    
    def test_allows_within_limit(self, rate_limiter_reset):
        """Test that requests within limit are allowed."""
        from utils.auth.rate_limiter import LoginRateLimiter, RateLimitConfig
        
        limiter = LoginRateLimiter(config=RateLimitConfig(max_attempts=5, window_seconds=60))
        
        for _ in range(5):
            limiter.check_and_increment("client1")
        
        # 5 attempts should be allowed
    
    def test_blocks_over_limit(self, rate_limiter_reset):
        """Test that requests over limit are blocked."""
        from utils.auth.rate_limiter import LoginRateLimiter, RateLimitConfig, RateLimitExceeded
        
        limiter = LoginRateLimiter(config=RateLimitConfig(max_attempts=3, window_seconds=60))
        
        for _ in range(3):
            limiter.check_and_increment("client2")
        
        with pytest.raises(RateLimitExceeded) as exc_info:
            limiter.check_and_increment("client2")
        
        assert exc_info.value.retry_after_seconds > 0
    
    def test_reset_clears_attempts(self, rate_limiter_reset):
        """Test that reset clears client attempts."""
        from utils.auth.rate_limiter import LoginRateLimiter, RateLimitConfig
        
        limiter = LoginRateLimiter(config=RateLimitConfig(max_attempts=3, window_seconds=60))
        
        for _ in range(3):
            limiter.check_and_increment("client3")
        
        limiter.reset("client3")
        
        # Should be able to make requests again
        limiter.check_and_increment("client3")
