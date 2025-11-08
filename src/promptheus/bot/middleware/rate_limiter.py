"""Rate limiting middleware for Telegram bot."""

import math
from collections.abc import Awaitable, Callable
from typing import Any

from loguru import logger
from telegram import Update
from telegram.ext import ContextTypes

from promptheus.core.rate_limit_service import RateLimitService


class RateLimitMiddleware:
    """Middleware for rate limiting Telegram bot requests."""

    def __init__(self, rate_limit_service: RateLimitService) -> None:
        """Initialize rate limit middleware.

        Args:
            rate_limit_service: Service for managing rate limits
        """
        self.rate_limit_service = rate_limit_service
        logger.info("Rate limit middleware initialized")

    async def __call__(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
        callback: Callable[[Update, ContextTypes.DEFAULT_TYPE], Awaitable[Any]],
    ) -> Any:
        """Process update through rate limiting middleware.

        Args:
            update: Telegram update object
            context: Telegram context
            callback: Next handler in chain

        Returns:
            Result of callback if allowed, None if rate limited
        """
        # Only rate limit messages from users (not system messages)
        if not update.effective_user:
            logger.debug("No effective user, skipping rate limit check")
            return await callback(update, context)

        user_id = update.effective_user.id

        # Check rate limit
        allowed = await self.rate_limit_service.check_limit(user_id)

        if not allowed:
            # Send rate limit message to user
            remaining_time = await self.rate_limit_service.get_remaining_time(user_id)
            minutes_remaining = math.ceil(remaining_time / 60)

            message = f"⏸️ Too many requests. Try again in {minutes_remaining} min."

            try:
                await update.effective_message.reply_text(message)
                logger.info(
                    "Rate limit message sent",
                    user_id=user_id,
                    remaining_minutes=minutes_remaining,
                )
            except Exception as e:
                logger.error(
                    "Failed to send rate limit message",
                    user_id=user_id,
                    error=str(e),
                )

            # Don't call the handler - request is blocked
            return None

        # Rate limit passed, continue to handler
        logger.debug("Rate limit passed, proceeding to handler", user_id=user_id)
        return await callback(update, context)
