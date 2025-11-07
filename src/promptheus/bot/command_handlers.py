"""Command handlers for Telegram bot."""

from loguru import logger
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes


class CommandHandlersMixin:
    """Mixin for basic bot commands."""

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /start command."""
        if not update.effective_user or not update.message:
            logger.warning("Invalid /start command: missing user or message")
            return

        user_id = update.effective_user.id
        username = update.effective_user.username
        logger.info("User started bot", user_id=user_id, username=username)

        # Get user from database
        user = await self.learning_orchestrator.user_repo.find_by_telegram_id(user_id)

        if user:
            # Returning user - check session context for resume
            logger.info(
                "Returning user detected", user_id=user_id, skill_level=user.skill_level.value
            )

            # Load session context to determine resume state
            session_context = await self.learning_orchestrator.get_session_context(user_id)
            current_lesson_id = session_context.get("current_lesson_id")
            lesson_step = session_context.get("lesson_step")

            if current_lesson_id and lesson_step:
                # User has active session, show resume options
                lesson = await self.learning_orchestrator.lesson_repo.find_by_id(current_lesson_id)

                if lesson:
                    resume_text = f"👋 Welcome back!\n\nYou were learning:\n**{lesson.title}**\n\n"
                    resume_text += f"Current step: {lesson_step.title()}"

                    if lesson_step == "theory":
                        theory_chunk = session_context.get("theory_chunk", 0)
                        resume_text += f" (Chunk {theory_chunk + 1})"

                    keyboard = [
                        [InlineKeyboardButton("▶️ Continue", callback_data="continue")],
                        [InlineKeyboardButton("📚 Menu", callback_data="menu")],
                    ]

                    await update.message.reply_text(
                        resume_text,
                        reply_markup=InlineKeyboardMarkup(keyboard),
                        parse_mode="Markdown",
                    )
                    return

            # No active session, show basic welcome back
            keyboard = [
                [InlineKeyboardButton("▶️ Continue", callback_data="continue")],
                [InlineKeyboardButton("📚 Menu", callback_data="menu")],
            ]
            await update.message.reply_text(
                "👋 Welcome back!", reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            # New user
            logger.info("New user detected, showing welcome", user_id=user_id)
            keyboard = [[InlineKeyboardButton("▶️ Start Learning", callback_data="start_learning")]]
            await update.message.reply_text(
                self.formatter.format_welcome(),
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown",
            )

    async def menu_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /menu command."""
        if not update.effective_user or not update.message:
            return

        keyboard = [
            [InlineKeyboardButton("📖 Continue Learning", callback_data="continue")],
            [InlineKeyboardButton("📋 All Lessons", callback_data="lesson_list")],
            [InlineKeyboardButton("📊 My Progress", callback_data="progress")],
        ]

        await update.message.reply_text(
            "📚 *Main Menu*",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
        )

    async def menu_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle menu callback."""
        if not update.effective_user or not update.callback_query:
            return

        await update.callback_query.answer()

        keyboard = [
            [InlineKeyboardButton("📖 Continue Learning", callback_data="continue")],
            [InlineKeyboardButton("📋 All Lessons", callback_data="lesson_list")],
            [InlineKeyboardButton("📊 My Progress", callback_data="progress")],
        ]

        try:
            await update.callback_query.edit_message_text(
                "📚 *Main Menu*",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown",
            )
        except Exception as e:
            if "Message is not modified" not in str(e):
                raise
