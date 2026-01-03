"""Auth settings for PIN/JWT authentication.

Settings are loaded from environment variables, typically sourced from
Secret Manager via Cloud Run secret mounts.

Environment Variables:
    AUTH_REQUIRED: If "true", require auth for /v1/brain/* routes. Default: "false"
    AUTH_JWT_SECRET: Secret key for HS256 JWT signing (required if AUTH_REQUIRED=true)
    AUTH_PIN_HASH: bcrypt hash of the PIN (required if AUTH_REQUIRED=true)
    AUTH_TOKEN_TTL_SECONDS: JWT token lifetime in seconds. Default: 43200 (12 hours)
"""
import os
from dataclasses import dataclass
from functools import lru_cache


@dataclass(frozen=True)
class AuthSettings:
    """Authentication configuration."""
    
    auth_required: bool
    jwt_secret: str | None
    pin_hash: str | None
    token_ttl_seconds: int
    
    def validate(self) -> None:
        """Validate settings consistency.
        
        Raises:
            ValueError: If auth is required but secrets are missing.
        """
        if self.auth_required:
            if not self.jwt_secret:
                raise ValueError(
                    "AUTH_JWT_SECRET is required when AUTH_REQUIRED=true. "
                    "Mount the secret from Secret Manager."
                )
            if not self.pin_hash:
                raise ValueError(
                    "AUTH_PIN_HASH is required when AUTH_REQUIRED=true. "
                    "Mount the secret from Secret Manager."
                )
            if len(self.jwt_secret) < 32:
                raise ValueError(
                    "AUTH_JWT_SECRET must be at least 32 characters for security."
                )


@lru_cache(maxsize=1)
def get_auth_settings() -> AuthSettings:
    """Load and cache auth settings from environment.
    
    Returns:
        AuthSettings instance with current configuration.
    """
    auth_required_str = os.environ.get("AUTH_REQUIRED", "false").lower()
    auth_required = auth_required_str in ("true", "1", "yes")
    
    return AuthSettings(
        auth_required=auth_required,
        jwt_secret=os.environ.get("AUTH_JWT_SECRET"),
        pin_hash=os.environ.get("AUTH_PIN_HASH"),
        token_ttl_seconds=int(os.environ.get("AUTH_TOKEN_TTL_SECONDS", "43200")),
    )


# Module-level convenience accessor
auth_settings = get_auth_settings()
