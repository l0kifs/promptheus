import asyncio
import contextlib
import sys

from loguru import logger
from telegram import Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

from promptheus.config import get_settings
from promptheus.core.dependency_container import DependencyContainer
from promptheus.data.database import Base, engine


async def session_cleanup_worker(container: DependencyContainer) -> None:
    """Background worker for periodic session cleanup."""
    logger.info("Session cleanup worker started")
    while True:
        try:
            # Wait 24 hours between cleanups
            await asyncio.sleep(24 * 60 * 60)  # 24 hours in seconds

            logger.info("Running scheduled session cleanup")
            # Use proper session management
            async with container._async_session_maker() as session:
                from promptheus.data.async_repositories import AsyncSessionRepository

                session_repo = AsyncSessionRepository(session)
                deleted_count = await session_repo.cleanup_old_sessions(days_old=30)

                if deleted_count > 0:
                    logger.info("Background cleanup completed", deleted_sessions=deleted_count)
                else:
                    logger.debug("Background cleanup completed: no old sessions found")

        except asyncio.CancelledError:
            logger.info("Session cleanup worker cancelled")
            break
        except Exception as e:
            logger.error("Error in session cleanup worker", error=str(e))
            # Continue running despite errors


def configure_logging() -> None:
    """Configure loguru logging with proper format and levels."""
    settings = get_settings()

    # Remove default handler
    logger.remove()

    # Add console handler with colored output for development
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=settings.log_level,
        colorize=True,
    )

    # Add file handler with rotation
    logger.add(
        "logs/promptheus_{time:YYYY-MM-DD}.log",
        rotation="00:00",  # Rotate at midnight
        retention="30 days",
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        serialize=False,
    )

    logger.info("Logging configured", log_level=settings.log_level)


def init_database() -> None:
    """Initialize database tables."""
    logger.info("Initializing database...")
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.critical("Failed to initialize database", error=str(e))
        raise


async def main() -> None:
    """Run the bot."""
    # Configure logging first
    configure_logging()
    logger.info("Starting Promptheus bot application")

    settings = get_settings()
    logger.debug("Settings loaded", environment=settings.environment)

    # Initialize database
    try:
        init_database()
    except Exception as e:
        logger.critical("Failed to initialize database, exiting", error=str(e))
        return

    # Initialize components
    logger.info("Initializing dependency container and components")
    try:
        container = DependencyContainer.get_instance()
        await container.initialize()
        handlers = await container.get_bot_handlers()
        logger.info("Components initialized successfully")
    except Exception as e:
        logger.critical("Failed to initialize components", error=str(e))
        return

    # Create application
    logger.info("Creating Telegram application")
    try:
        application = Application.builder().token(settings.telegram_bot_token).build()
        logger.debug("Telegram application created")
    except Exception as e:
        logger.critical("Failed to create Telegram application", error=str(e))
        return

    # Add handlers
    logger.info("Registering bot handlers")
    application.add_handler(CommandHandler("start", handlers.start_command))
    application.add_handler(CommandHandler("menu", handlers.menu_command))

    # Callback handlers
    application.add_handler(
        CallbackQueryHandler(handlers.start_learning_callback, pattern="^start_learning$")
    )
    application.add_handler(
        CallbackQueryHandler(handlers.start_assessment_callback, pattern="^start_assessment$")
    )
    application.add_handler(CallbackQueryHandler(handlers.answer_callback, pattern="^answer_"))
    application.add_handler(CallbackQueryHandler(handlers.goal_callback, pattern="^goal_"))
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
        CallbackQueryHandler(handlers.theory_prev_callback, pattern="^theory_prev_")
    )
    application.add_handler(CallbackQueryHandler(handlers.examples_callback, pattern="^examples_"))
    application.add_handler(CallbackQueryHandler(handlers.practice_callback, pattern="^practice_"))
    application.add_handler(
        CallbackQueryHandler(handlers.lesson_list_callback, pattern="^lesson_list$")
    )
    application.add_handler(CallbackQueryHandler(handlers.menu_callback, pattern="^menu$"))
    application.add_handler(CallbackQueryHandler(handlers.continue_callback, pattern="^continue$"))
    application.add_handler(CallbackQueryHandler(handlers.progress_callback, pattern="^progress$"))
    application.add_handler(CallbackQueryHandler(handlers.hint_callback, pattern="^hint_"))
    application.add_handler(CallbackQueryHandler(handlers.skip_callback, pattern="^skip_"))
    application.add_handler(
        CallbackQueryHandler(handlers.lesson_complete_callback, pattern="^lesson_complete_")
    )

    # Message handler for text (user prompt submissions)
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.text_message_handler)
    )

    # Error handler
    application.add_error_handler(handlers.error_handler)
    logger.info("All handlers registered successfully")

    # Start background cleanup task
    logger.info("Starting background session cleanup task")
    cleanup_task = asyncio.create_task(session_cleanup_worker(container))
    logger.info("Background cleanup task started")

    # Start bot
    logger.info("Starting bot...")
    try:
        await application.initialize()
        await application.start()
        await application.updater.start_polling(allowed_updates=Update.ALL_TYPES)  # type: ignore
        logger.info("Bot is running. Press Ctrl+C to stop.")
    except Exception as e:
        logger.critical("Failed to start bot", error=str(e))
        return

    # Keep running
    try:
        await asyncio.Event().wait()
    except (KeyboardInterrupt, asyncio.CancelledError):
        pass
    finally:
        logger.info("Received shutdown signal, stopping bot...")
        try:
            # Cancel background tasks
            cleanup_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await cleanup_task

            # Stop telegram bot
            await application.updater.stop()  # type: ignore
            await application.stop()
            await application.shutdown()

            # Cleanup database connections
            await container.cleanup()

            logger.info("Bot stopped gracefully")
        except Exception as e:
            logger.error("Error during shutdown", error=str(e))


if __name__ == "__main__":
    asyncio.run(main())
