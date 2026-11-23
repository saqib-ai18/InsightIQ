import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, Optional
import structlog
from app.core.config import get_settings

logger = structlog.get_logger()


@dataclass
class RateLimitConfig:
    max_requests: int
    window_seconds: int


@dataclass
class UserRateLimitState:
    requests: list = field(default_factory=list)
    blocked_until: Optional[float] = None


class RateLimiter:
    def __init__(self):
        self.settings = get_settings()
        self.config = RateLimitConfig(
            max_requests=self.settings.NVIDIA_RATE_LIMIT_REQUESTS,
            window_seconds=self.settings.NVIDIA_RATE_LIMIT_WINDOW_SECONDS,
        )
        self.user_states: Dict[str, UserRateLimitState] = defaultdict(UserRateLimitState)
        self._cleanup_interval = 300  # 5 minutes
        self._last_cleanup = time.time()

    def _cleanup_expired(self):
        now = time.time()
        if now - self._last_cleanup < self._cleanup_interval:
            return

        expired_users = []
        for user_id, state in self.user_states.items():
            # Remove old requests outside the window
            state.requests = [req_time for req_time in state.requests if now - req_time < self.config.window_seconds]
            # Remove expired blocks
            if state.blocked_until and state.blocked_until < now:
                state.blocked_until = None
            # Clean up empty states
            if not state.requests and not state.blocked_until:
                expired_users.append(user_id)

        for user_id in expired_users:
            del self.user_states[user_id]

        self._last_cleanup = now

    def check_rate_limit(self, user_id: str) -> tuple[bool, Optional[str]]:
        """Check if user is within rate limits. Returns (allowed, error_message)."""
        self._cleanup_expired()

        state = self.user_states[user_id]
        now = time.time()

        # Check if user is blocked
        if state.blocked_until and state.blocked_until > now:
            remaining = int(state.blocked_until - now)
            return False, f"Rate limit exceeded. Try again in {remaining} seconds."

        # Count requests in current window
        recent_requests = [req_time for req_time in state.requests if now - req_time < self.config.window_seconds]

        if len(recent_requests) >= self.config.max_requests:
            # Block the user for the remainder of the window
            oldest_request = min(recent_requests)
            state.blocked_until = oldest_request + self.config.window_seconds
            remaining = int(state.blocked_until - now)
            logger.warning("rate_limit_exceeded", user_id=user_id, remaining_seconds=remaining)
            return False, f"Rate limit exceeded ({self.config.max_requests} requests per {self.config.window_seconds}s). Try again in {remaining} seconds."

        # Record this request
        state.requests.append(now)
        return True, None

    def get_remaining_requests(self, user_id: str) -> int:
        self._cleanup_expired()
        state = self.user_states.get(user_id)
        if not state:
            return self.config.max_requests

        now = time.time()
        recent_requests = [req_time for req_time in state.requests if now - req_time < self.config.window_seconds]
        return max(0, self.config.max_requests - len(recent_requests))

    def get_reset_time(self, user_id: str) -> Optional[float]:
        state = self.user_states.get(user_id)
        if not state or not state.requests:
            return None
        return min(state.requests) + self.config.window_seconds


import time