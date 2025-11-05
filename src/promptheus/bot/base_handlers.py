"""Base handlers for Telegram bot."""

from loguru import logger
from telegram.ext import ContextTypes

from promptheus.ai.openrouter_client import OpenRouterClient
from promptheus.bot.message_formatter import MessageFormatter
from promptheus.core.assessment_engine import AssessmentEngine
from promptheus.core.learning_flow_orchestrator import LearningFlowOrchestrator
from promptheus.core.progress_tracker import ProgressTracker


class BaseBotHandlers:
    """Base class for bot handlers with common initialization and utilities."""

    def __init__(
        self,
        ai_client: OpenRouterClient,
        assessment_engine: AssessmentEngine,
        learning_orchestrator: LearningFlowOrchestrator,
        progress_tracker: ProgressTracker,
    ) -> None:
        """Initialize base handlers."""
        self.ai_client = ai_client
        self.assessment_engine = assessment_engine
        self.learning_orchestrator = learning_orchestrator
        self.progress_tracker = progress_tracker
        self.formatter = MessageFormatter()

    async def error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle errors."""
        logger.error(f"Exception while handling an update: {context.error}")
