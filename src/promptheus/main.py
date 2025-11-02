"""Main application entry point."""

import asyncio

from loguru import logger
from telegram import Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

from promptheus.ai.openrouter_client import OpenRouterClient
from promptheus.bot.handlers import BotHandlers
from promptheus.config import get_settings
from promptheus.data.database import Base, engine


def init_database() -> None:
    """Initialize database tables."""
    logger.info("Initializing database...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database initialized")


async def main() -> None:
    """Run the bot."""
    settings = get_settings()

    # Initialize database
    init_database()

    # Initialize components
    ai_client = OpenRouterClient()
    handlers = BotHandlers(ai_client)

    # Create application
    application = Application.builder().token(settings.telegram_bot_token).build()

    # Add handlers
    application.add_handler(CommandHandler("start", handlers.start_command))
    application.add_handler(CommandHandler("menu", handlers.menu_command))

    # Callback handlers
    application.add_handler(
        CallbackQueryHandler(
            handlers.start_learning_callback, pattern="^start_learning$"
        )
    )
    application.add_handler(
        CallbackQueryHandler(
            handlers.start_assessment_callback, pattern="^start_assessment$"
        )
    )
    application.add_handler(
        CallbackQueryHandler(handlers.answer_callback, pattern="^answer_")
    )
    application.add_handler(
        CallbackQueryHandler(handlers.goal_callback, pattern="^goal_")
    )
    application.add_handler(
        CallbackQueryHandler(handlers.lesson_callback, pattern="^lesson_[0-9]+$")
    )
    application.add_handler(
        CallbackQueryHandler(handlers.lesson_start_callback, pattern="^lesson_start_")
    )
    application.add_handler(
        CallbackQueryHandler(handlers.theory_next_callback, pattern="^theory_next_")
    )
    application.add_handler(
        CallbackQueryHandler(handlers.examples_callback, pattern="^examples_")
    )
    application.add_handler(
        CallbackQueryHandler(handlers.practice_callback, pattern="^practice_")
    )
    application.add_handler(
        CallbackQueryHandler(handlers.lesson_list_callback, pattern="^lesson_list$")
    )
    application.add_handler(
        CallbackQueryHandler(handlers.menu_callback, pattern="^menu$")
    )
    application.add_handler(
        CallbackQueryHandler(handlers.continue_callback, pattern="^continue$")
    )

    # Message handler for text (user prompt submissions)
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.text_message_handler)
    )

    # Error handler
    application.add_error_handler(handlers.error_handler)

    # Start bot
    logger.info("Starting bot...")
    await application.initialize()
    await application.start()
    await application.updater.start_polling(allowed_updates=Update.ALL_TYPES)  # type: ignore

    logger.info("Bot is running. Press Ctrl+C to stop.")

    # Keep running
    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        logger.info("Stopping bot...")
        await application.updater.stop()  # type: ignore
        await application.stop()
        await application.shutdown()
        logger.info("Bot stopped")


if __name__ == "__main__":
    asyncio.run(main())
