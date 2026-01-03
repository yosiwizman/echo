"""Auth utilities package for PIN/JWT authentication."""
from .settings import auth_settings, get_auth_settings
from .jwt_handler import create_access_token, verify_access_token, JWTPayload
from .rate_limiter import LoginRateLimiter, RateLimitExceeded
from .brain_auth import require_brain_auth, optional_brain_auth, BrainAuthResult

__all__ = [
    "auth_settings",
    "get_auth_settings",
    "create_access_token",
    "verify_access_token",
    "JWTPayload",
    "LoginRateLimiter",
    "RateLimitExceeded",
    "require_brain_auth",
    "optional_brain_auth",
    "BrainAuthResult",
]
