"""Base handlers for Telegram bot."""

import math
import traceback

import httpx
from loguru import logger
from telegram import Update
from telegram.error import NetworkError, TimedOut
from telegram.ext import ContextTypes

from promptheus.ai.openrouter_client import OpenRouterClient
from promptheus.bot.message_formatter import MessageFormatter
from promptheus.core.assessment_engine import AssessmentEngine
from promptheus.core.exceptions import BusinessError, SystemError, ValidationError
from promptheus.core.learning_flow_orchestrator import LearningFlowOrchestrator
from promptheus.core.progress_tracker import ProgressTracker
from promptheus.core.rate_limit_service import RateLimitService


class BaseBotHandlers:
    """Base class for bot handlers with common initialization and utilities."""

    def __init__(
        self,
        ai_client: OpenRouterClient,
        assessment_engine: AssessmentEngine,
        learning_orchestrator: LearningFlowOrchestrator,
        progress_tracker: ProgressTracker,
        rate_limit_service: RateLimitService,
    ) -> None:
        """Initialize base handlers."""
        self.ai_client = ai_client
        self.assessment_engine = assessment_engine
        self.learning_orchestrator = learning_orchestrator
        self.progress_tracker = progress_tracker
        self.rate_limit_service = rate_limit_service
        self.formatter = MessageFormatter()

    async def check_rate_limit(self, update: Update) -> bool:
        """Check if user is within rate limits.

        Args:
            update: Telegram update

        Returns:
            True if request is allowed, False if rate limited
        """
        if not update.effective_user:
            return True  # Allow system messages

        user_id = update.effective_user.id
        allowed = await self.rate_limit_service.check_limit(user_id)

        if not allowed:
            # Send rate limit message
            remaining_time = await self.rate_limit_service.get_remaining_time(user_id)
            minutes_remaining = math.ceil(remaining_time / 60)

            message = f"⏸️ Слишком много запросов. Попробуйте через {minutes_remaining} мин."

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

        return allowed

    def _classify_error(self, error: Exception) -> str:
        """Classify error into categories for appropriate handling.

        Args:
            error: The exception that occurred

        Returns:
            Error category: 'user_error', 'api_error', 'system_error'
        """
        # Import SQLAlchemy exceptions
        from sqlalchemy.exc import SQLAlchemyError

        # Network and API related errors
        if isinstance(error, (NetworkError, TimedOut, httpx.TimeoutException, httpx.ConnectError)):
            return "api_error"

        # Database errors
        elif isinstance(error, SQLAlchemyError):
            return "system_error"

        # User input validation errors and business logic errors
        elif isinstance(error, (ValueError, KeyError, TypeError, ValidationError, BusinessError)):
            return "user_error"

        # System/internal errors
        elif isinstance(error, SystemError):
            return "system_error"

        # Default fallback
        else:
            return "system_error"

    async def _handle_api_error(self, update: Update, error: Exception) -> None:
        """Handle API-related errors (network, timeout, etc.).

        Args:
            update: Telegram update
            error: The API error
        """
        user_id = update.effective_user.id if update.effective_user else "unknown"

        logger.warning(
            "API error occurred",
            user_id=user_id,
            error_type=type(error).__name__,
            error_message=str(error),
        )

        message = "⏱️ Request took too long. Try simplifying your request or try again later."

        try:
            await update.effective_message.reply_text(message)
        except Exception as reply_error:
            logger.error(
                "Failed to send API error message",
                user_id=user_id,
                reply_error=str(reply_error),
            )

    async def _handle_user_error(self, update: Update, error: Exception) -> None:
        """Handle user input errors (validation, invalid data, etc.).

        Args:
            update: Telegram update
            error: The user error
        """
        user_id = update.effective_user.id if update.effective_user else "unknown"

        logger.info(
            "User error occurred",
            user_id=user_id,
            error_type=type(error).__name__,
            error_message=str(error),
        )

        message = "🔄 Something went wrong. Try returning to the main menu and starting over."

        try:
            await update.effective_message.reply_text(message)
        except Exception as reply_error:
            logger.error(
                "Failed to send user error message",
                user_id=user_id,
                reply_error=str(reply_error),
            )

    async def _handle_system_error(self, update: Update, error: Exception) -> None:
        """Handle system/internal errors.

        Args:
            update: Telegram update
            error: The system error
        """
        user_id = update.effective_user.id if update.effective_user else "unknown"

        logger.error(
            "System error occurred",
            user_id=user_id,
            error_type=type(error).__name__,
            error_message=str(error),
            traceback=traceback.format_exc(),
        )

        message = "🔧 An internal error occurred. We're already working on fixing it."

        try:
            await update.effective_message.reply_text(message)
        except Exception as reply_error:
            logger.error(
                "Failed to send system error message",
                user_id=user_id,
                reply_error=str(reply_error),
            )

    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle errors with classification and user-friendly messaging.

        Args:
            update: Telegram update object
            context: Telegram context containing error information
        """
        error = context.error
        if error is None:
            logger.warning("Error handler called without error")
            return

        # Ensure we have an Update object
        if not isinstance(update, Update) or update.effective_user is None:
            logger.error(
                "Error handler received invalid update",
                update_type=type(update).__name__,
                error=str(error),
            )
            return

        user_id = update.effective_user.id

        # Classify and handle the error
        error_category = self._classify_error(error)

        logger.info(
            "Handling error",
            user_id=user_id,
            error_category=error_category,
            error_type=type(error).__name__,
        )

        if error_category == "api_error":
            await self._handle_api_error(update, error)
        elif error_category == "user_error":
            await self._handle_user_error(update, error)
        else:  # system_error
            await self._handle_system_error(update, error)
