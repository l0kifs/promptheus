"""Rate limiting service for controlling request frequency per user."""

import asyncio
import time
from collections import defaultdict

from loguru import logger

from promptheus.config import get_settings


class RateLimitService:
    """Service for managing rate limits using sliding window algorithm."""

    def __init__(self, requests_per_minute: int | None = None) -> None:
        """Initialize rate limit service.

        Args:
            requests_per_minute: Maximum requests allowed per user per minute.
                               If None, uses setting from configuration.
        """
        settings = get_settings()
        self.requests_per_minute = requests_per_minute or settings.rate_limit_requests
        self.window_seconds = 60  # 1 minute window

        # In-memory storage: user_id -> list of timestamps
        # In production, this should be Redis or similar persistent storage
        self._request_history: dict[int, list[float]] = defaultdict(list)

        # Lock for thread-safe operations
        self._lock = asyncio.Lock()

        logger.info(
            "Rate limit service initialized",
            requests_per_minute=self.requests_per_minute,
            window_seconds=self.window_seconds,
        )

    async def check_limit(self, user_id: int) -> bool:
        """Check if user is within rate limit.

        Args:
            user_id: Telegram user ID

        Returns:
            True if request is allowed, False if rate limit exceeded
        """
        async with self._lock:
            current_time = time.time()

            # Get user's request history
            user_requests = self._request_history[user_id]

            # Remove requests outside the sliding window
            cutoff_time = current_time - self.window_seconds
            user_requests[:] = [timestamp for timestamp in user_requests if timestamp > cutoff_time]

            # Check if user has exceeded the limit
            if len(user_requests) >= self.requests_per_minute:
                logger.warning(
                    "Rate limit exceeded",
                    user_id=user_id,
                    request_count=len(user_requests),
                    limit=self.requests_per_minute,
                )
                return False

            # Add current request timestamp
            user_requests.append(current_time)

            logger.debug(
                "Rate limit check passed",
                user_id=user_id,
                request_count=len(user_requests),
                limit=self.requests_per_minute,
            )
            return True

    async def get_remaining_time(self, user_id: int) -> float:
        """Get remaining time until rate limit resets for user.

        Args:
            user_id: Telegram user ID

        Returns:
            Seconds until oldest request expires (rate limit resets)
        """
        async with self._lock:
            user_requests = self._request_history[user_id]

            if not user_requests:
                return 0.0

            # Find oldest request in current window
            current_time = time.time()
            cutoff_time = current_time - self.window_seconds

            # Clean up old requests first
            user_requests[:] = [timestamp for timestamp in user_requests if timestamp > cutoff_time]

            if not user_requests:
                return 0.0

            oldest_request = min(user_requests)
            reset_time = oldest_request + self.window_seconds
            remaining = max(0.0, reset_time - current_time)

            return remaining

    async def get_request_count(self, user_id: int) -> int:
        """Get current request count for user in sliding window.

        Args:
            user_id: Telegram user ID

        Returns:
            Number of requests in current window
        """
        async with self._lock:
            current_time = time.time()
            cutoff_time = current_time - self.window_seconds

            user_requests = self._request_history[user_id]
            # Clean up old requests
            user_requests[:] = [timestamp for timestamp in user_requests if timestamp > cutoff_time]

            return len(user_requests)

    async def reset_user(self, user_id: int) -> None:
        """Reset rate limit for a specific user (for testing/admin purposes).

        Args:
            user_id: Telegram user ID
        """
        async with self._lock:
            if user_id in self._request_history:
                del self._request_history[user_id]
                logger.info("Rate limit reset for user", user_id=user_id)

    async def cleanup_inactive_users(self, max_age_seconds: int = 3600) -> int:
        """Clean up inactive users to prevent memory leaks.

        Args:
            max_age_seconds: Maximum age of last request before cleanup

        Returns:
            Number of users cleaned up
        """
        async with self._lock:
            current_time = time.time()
            cutoff_time = current_time - max_age_seconds

            users_to_remove = []
            for user_id, requests in self._request_history.items():
                if requests and max(requests) < cutoff_time:
                    users_to_remove.append(user_id)

            for user_id in users_to_remove:
                del self._request_history[user_id]

            if users_to_remove:
                logger.info("Cleaned up inactive users", count=len(users_to_remove))

            return len(users_to_remove)
