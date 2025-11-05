"""Telegram bot handlers."""

from promptheus.bot.assessment_handlers import AssessmentHandlersMixin
from promptheus.bot.base_handlers import BaseBotHandlers
from promptheus.bot.command_handlers import CommandHandlersMixin
from promptheus.bot.lesson_handlers import LessonHandlersMixin
from promptheus.bot.practice_handlers import PracticeHandlersMixin
from promptheus.bot.progress_handlers import ProgressHandlersMixin


class BotHandlers(
    BaseBotHandlers,
    CommandHandlersMixin,
    AssessmentHandlersMixin,
    LessonHandlersMixin,
    PracticeHandlersMixin,
    ProgressHandlersMixin,
):
    """Handlers for Telegram bot commands and callbacks."""

    pass
