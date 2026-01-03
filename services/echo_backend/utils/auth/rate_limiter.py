"""In-memory sliding window rate limiter for login attempts.

Provides basic protection against brute-force PIN attacks.
Uses a simple sliding window algorithm with per-IP tracking.

Note: This is an in-memory implementation suitable for single-instance
deployments. For multi-instance deployments, consider using Redis.
"""
import time
from collections import defaultdict
from dataclasses import dataclass, field
from threading import Lock
from typing import Dict, List


class RateLimitExceeded(Exception):
    """Raised when rate limit is exceeded."""
    
    def __init__(self, retry_after_seconds: int):
        self.retry_after_seconds = retry_after_seconds
        super().__init__(f"Rate limit exceeded. Retry after {retry_after_seconds} seconds.")


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""
    max_attempts: int = 10  # Maximum attempts allowed
    window_seconds: int = 600  # Time window (10 minutes)


@dataclass
class LoginRateLimiter:
    """Sliding window rate limiter for login attempts.
    
    Thread-safe implementation using a simple lock.
    
    Usage:
        limiter = LoginRateLimiter()
        try:
            limiter.check_and_increment("192.168.1.1")
            # Process login attempt
        except RateLimitExceeded as e:
            # Return 429 with retry_after_seconds
    """
    config: RateLimitConfig = field(default_factory=RateLimitConfig)
    _attempts: Dict[str, List[float]] = field(default_factory=lambda: defaultdict(list))
    _lock: Lock = field(default_factory=Lock)
    
    def check_and_increment(self, client_id: str) -> None:
        """Check rate limit and record attempt.
        
        Args:
            client_id: Identifier for the client (typically IP address).
            
        Raises:
            RateLimitExceeded: If the client has exceeded the rate limit.
        """
        now = time.time()
        window_start = now - self.config.window_seconds
        
        with self._lock:
            # Clean up old attempts outside the window
            self._attempts[client_id] = [
                ts for ts in self._attempts[client_id] if ts > window_start
            ]
            
            # Check if limit exceeded
            if len(self._attempts[client_id]) >= self.config.max_attempts:
                # Calculate retry time based on oldest attempt in window
                oldest = min(self._attempts[client_id])
                retry_after = int(oldest + self.config.window_seconds - now) + 1
                raise RateLimitExceeded(retry_after_seconds=max(1, retry_after))
            
            # Record this attempt
            self._attempts[client_id].append(now)
    
    def get_remaining_attempts(self, client_id: str) -> int:
        """Get remaining attempts for a client.
        
        Args:
            client_id: Identifier for the client.
            
        Returns:
            Number of remaining attempts in the current window.
        """
        now = time.time()
        window_start = now - self.config.window_seconds
        
        with self._lock:
            recent_attempts = [
                ts for ts in self._attempts[client_id] if ts > window_start
            ]
            return max(0, self.config.max_attempts - len(recent_attempts))
    
    def reset(self, client_id: str) -> None:
        """Reset rate limit for a client (e.g., after successful login).
        
        Args:
            client_id: Identifier for the client.
        """
        with self._lock:
            self._attempts.pop(client_id, None)
    
    def cleanup_old_entries(self, max_age_seconds: int = 3600) -> int:
        """Clean up stale entries to prevent memory growth.
        
        Args:
            max_age_seconds: Remove entries older than this. Default: 1 hour.
            
        Returns:
            Number of entries removed.
        """
        now = time.time()
        cutoff = now - max_age_seconds
        removed = 0
        
        with self._lock:
            stale_keys = [
                key for key, timestamps in self._attempts.items()
                if not timestamps or max(timestamps) < cutoff
            ]
            for key in stale_keys:
                del self._attempts[key]
                removed += 1
        
        return removed


# Global rate limiter instance for login attempts
login_rate_limiter = LoginRateLimiter()
