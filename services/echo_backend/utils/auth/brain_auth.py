"""FastAPI dependency for Brain API authentication.

Provides JWT bearer token validation for /v1/brain/* routes.

Behavior:
    - If AUTH_REQUIRED=true: Require valid JWT, return 401 on missing/invalid
    - If AUTH_REQUIRED=false: Allow unauthenticated, but validate if token present
"""
import logging
from typing import Optional

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .jwt_handler import verify_access_token, JWTPayload, JWTExpiredError, JWTInvalidError
from .settings import get_auth_settings

logger = logging.getLogger(__name__)

# HTTPBearer with auto_error=False so we can handle missing auth gracefully
_bearer_scheme = HTTPBearer(auto_error=False)


class BrainAuthResult:
    """Result of brain auth validation.
    
    Attributes:
        authenticated: Whether a valid token was provided.
        payload: Decoded JWT payload if authenticated.
        subject: Subject from JWT (e.g., "mrw") if authenticated.
    """
    
    def __init__(self, authenticated: bool, payload: Optional[JWTPayload] = None):
        self.authenticated = authenticated
        self.payload = payload
        self.subject = payload.sub if payload else None


async def require_brain_auth(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_scheme),
) -> BrainAuthResult:
    """Validate JWT for Brain API routes.
    
    This dependency checks AUTH_REQUIRED setting:
    - If true: Valid JWT required, 401 on missing/invalid
    - If false: Allows unauthenticated but validates tokens if present
    
    Args:
        request: FastAPI request object.
        credentials: Bearer token from Authorization header.
        
    Returns:
        BrainAuthResult with authentication status.
        
    Raises:
        HTTPException 401: If auth required and token missing/invalid.
    """
    settings = get_auth_settings()
    
    # No credentials provided
    if not credentials:
        if settings.auth_required:
            logger.warning("BRAIN_AUTH_MISSING_TOKEN")
            raise HTTPException(
                status_code=401,
                detail={
                    "ok": False,
                    "error": {
                        "code": "auth_required",
                        "message": "Authentication required. Please provide a valid bearer token.",
                    },
                },
                headers={"WWW-Authenticate": "Bearer"},
            )
        # Auth not required, allow unauthenticated
        return BrainAuthResult(authenticated=False)
    
    # Credentials provided - validate token
    token = credentials.credentials
    
    try:
        payload = verify_access_token(token)
        logger.debug(f"BRAIN_AUTH_SUCCESS sub={payload.sub} jti={payload.jti}")
        return BrainAuthResult(authenticated=True, payload=payload)
    except JWTExpiredError:
        logger.warning("BRAIN_AUTH_TOKEN_EXPIRED")
        raise HTTPException(
            status_code=401,
            detail={
                "ok": False,
                "error": {
                    "code": "token_expired",
                    "message": "Token has expired. Please login again.",
                },
            },
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTInvalidError as e:
        logger.warning(f"BRAIN_AUTH_INVALID_TOKEN error={e}")
        raise HTTPException(
            status_code=401,
            detail={
                "ok": False,
                "error": {
                    "code": "invalid_token",
                    "message": "Invalid authentication token.",
                },
            },
            headers={"WWW-Authenticate": "Bearer"},
        )


async def optional_brain_auth(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_scheme),
) -> BrainAuthResult:
    """Optional JWT validation - never raises, just reports status.
    
    Useful for endpoints that want to know auth status but don't require it.
    
    Args:
        credentials: Bearer token from Authorization header.
        
    Returns:
        BrainAuthResult with authentication status (never raises).
    """
    if not credentials:
        return BrainAuthResult(authenticated=False)
    
    token = credentials.credentials
    
    try:
        payload = verify_access_token(token)
        return BrainAuthResult(authenticated=True, payload=payload)
    except (JWTExpiredError, JWTInvalidError):
        return BrainAuthResult(authenticated=False)
