"""Auth router for PIN login to Brain API.

Provides:
    POST /v1/auth/login - Exchange PIN for JWT bearer token

Security features:
    - bcrypt PIN verification (timing-safe)
    - Rate limiting per IP (10 attempts / 10 min)
    - Structured error responses
"""
import logging
import os
import uuid

import bcrypt
from fastapi import APIRouter, HTTPException, Request

from models.auth import LoginRequest, LoginResponse
from models.brain import RuntimeMetadata
from utils.auth.jwt_handler import create_access_token
from utils.auth.rate_limiter import login_rate_limiter, RateLimitExceeded
from utils.auth.settings import get_auth_settings

logger = logging.getLogger(__name__)

# Runtime metadata (set via Cloud Run env vars at deploy time)
_APP_ENV = os.environ.get("APP_ENV", "unknown")
_GIT_SHA = os.environ.get("GIT_SHA", "unknown")
_BUILD_TIME = os.environ.get("BUILD_TIME", "unknown")


router = APIRouter()


def _get_client_ip(request: Request) -> str:
    """Extract client IP from request, handling proxies."""
    # Cloud Run sets X-Forwarded-For
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # First IP in the chain is the original client
        return forwarded.split(",")[0].strip()
    # Fallback to direct client
    return request.client.host if request.client else "unknown"


def _verify_pin(pin: str, pin_hash: str) -> bool:
    """Verify PIN against bcrypt hash (timing-safe).
    
    Args:
        pin: Plain text PIN from user.
        pin_hash: bcrypt hash from settings.
        
    Returns:
        True if PIN matches, False otherwise.
    """
    try:
        return bcrypt.checkpw(pin.encode("utf-8"), pin_hash.encode("utf-8"))
    except Exception:
        # Invalid hash format or other error
        return False


@router.post("/login", response_model=LoginResponse)
async def login(request: Request, body: LoginRequest):
    """Exchange PIN for JWT bearer token.
    
    Rate limited to 10 attempts per 10 minutes per IP.
    
    Args:
        request: FastAPI request (for IP extraction).
        body: LoginRequest with PIN.
        
    Returns:
        LoginResponse with JWT token and expiration.
        
    Raises:
        HTTPException 401: Invalid PIN
        HTTPException 429: Rate limit exceeded
        HTTPException 503: Auth not configured
    """
    trace_id = str(uuid.uuid4())
    client_ip = _get_client_ip(request)
    
    # Build runtime metadata
    runtime = RuntimeMetadata(
        trace_id=trace_id,
        provider="auth",
        env=_APP_ENV,
        git_sha=_GIT_SHA,
        build_time=_BUILD_TIME,
    )
    
    # Log attempt (never log PIN for security)
    logger.info(f"AUTH_LOGIN_ATTEMPT trace_id={trace_id} client_ip={client_ip}")
    
    # Check rate limit
    try:
        login_rate_limiter.check_and_increment(client_ip)
    except RateLimitExceeded as e:
        logger.warning(f"AUTH_RATE_LIMIT trace_id={trace_id} client_ip={client_ip} retry_after={e.retry_after_seconds}")
        raise HTTPException(
            status_code=429,
            detail={
                "ok": False,
                "error": {
                    "code": "rate_limit",
                    "message": "Too many login attempts. Please try again later.",
                    "retry_after": e.retry_after_seconds,
                },
                "runtime": runtime.model_dump(),
            },
            headers={"Retry-After": str(e.retry_after_seconds)},
        )
    
    # Get settings
    settings = get_auth_settings()
    
    # Check if auth is configured
    if not settings.pin_hash:
        logger.error(f"AUTH_NOT_CONFIGURED trace_id={trace_id}")
        raise HTTPException(
            status_code=503,
            detail={
                "ok": False,
                "error": {
                    "code": "auth_not_configured",
                    "message": "Authentication is not configured on this server.",
                },
                "runtime": runtime.model_dump(),
            },
        )
    
    # Verify PIN
    if not _verify_pin(body.pin, settings.pin_hash):
        logger.warning(f"AUTH_INVALID_PIN trace_id={trace_id} client_ip={client_ip}")
        raise HTTPException(
            status_code=401,
            detail={
                "ok": False,
                "error": {
                    "code": "invalid_pin",
                    "message": "Invalid PIN.",
                },
                "runtime": runtime.model_dump(),
            },
        )
    
    # PIN is valid - reset rate limit and create token
    login_rate_limiter.reset(client_ip)
    
    try:
        token, expires_at = create_access_token()
    except ValueError as e:
        logger.error(f"AUTH_TOKEN_ERROR trace_id={trace_id} error={e}")
        raise HTTPException(
            status_code=503,
            detail={
                "ok": False,
                "error": {
                    "code": "token_error",
                    "message": "Failed to create authentication token.",
                },
                "runtime": runtime.model_dump(),
            },
        )
    
    logger.info(f"AUTH_LOGIN_SUCCESS trace_id={trace_id} client_ip={client_ip}")
    
    return LoginResponse(
        ok=True,
        token=token,
        expires_at=expires_at,
        runtime=runtime,
    )
