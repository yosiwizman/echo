"""JWT token creation and verification.

Uses HS256 with strict algorithm validation to prevent algorithm confusion attacks.
Tokens include:
    - sub: Subject identifier ("mrw" for PIN auth)
    - iat: Issued at timestamp
    - exp: Expiration timestamp
    - jti: Unique token ID for auditing
"""
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

import jwt

from .settings import get_auth_settings


class JWTError(Exception):
    """Base exception for JWT errors."""
    pass


class JWTExpiredError(JWTError):
    """Token has expired."""
    pass


class JWTInvalidError(JWTError):
    """Token is invalid (bad signature, malformed, etc.)."""
    pass


@dataclass
class JWTPayload:
    """Decoded JWT payload."""
    sub: str
    iat: datetime
    exp: datetime
    jti: str


def create_access_token(
    subject: str = "mrw",
    ttl_seconds: Optional[int] = None,
) -> tuple[str, datetime]:
    """Create a new JWT access token.
    
    Args:
        subject: Token subject identifier. Default: "mrw"
        ttl_seconds: Token lifetime in seconds. Uses settings default if not provided.
        
    Returns:
        Tuple of (token_string, expiration_datetime)
        
    Raises:
        ValueError: If JWT secret is not configured.
    """
    settings = get_auth_settings()
    
    if not settings.jwt_secret:
        raise ValueError("AUTH_JWT_SECRET not configured")
    
    if ttl_seconds is None:
        ttl_seconds = settings.token_ttl_seconds
    
    now = datetime.now(timezone.utc)
    exp = datetime.fromtimestamp(now.timestamp() + ttl_seconds, tz=timezone.utc)
    jti = str(uuid.uuid4())
    
    payload = {
        "sub": subject,
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
        "jti": jti,
    }
    
    token = jwt.encode(payload, settings.jwt_secret, algorithm="HS256")
    return token, exp


def verify_access_token(token: str) -> JWTPayload:
    """Verify and decode a JWT access token.
    
    Args:
        token: The JWT token string.
        
    Returns:
        JWTPayload with decoded claims.
        
    Raises:
        JWTExpiredError: If the token has expired.
        JWTInvalidError: If the token is invalid (bad signature, malformed, wrong algorithm).
    """
    settings = get_auth_settings()
    
    if not settings.jwt_secret:
        raise JWTInvalidError("AUTH_JWT_SECRET not configured")
    
    try:
        # Strictly specify allowed algorithms to prevent algorithm confusion
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=["HS256"],
            options={
                "require": ["sub", "iat", "exp", "jti"],
                "verify_exp": True,
                "verify_iat": True,
            }
        )
        
        return JWTPayload(
            sub=payload["sub"],
            iat=datetime.fromtimestamp(payload["iat"], tz=timezone.utc),
            exp=datetime.fromtimestamp(payload["exp"], tz=timezone.utc),
            jti=payload["jti"],
        )
    except jwt.ExpiredSignatureError:
        raise JWTExpiredError("Token has expired")
    except jwt.InvalidTokenError as e:
        raise JWTInvalidError(f"Invalid token: {e}")
