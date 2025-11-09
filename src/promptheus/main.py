import asyncio
import contextlib
import sys

import uvicorn
from fastapi import FastAPI
from loguru import logger
from telegram import Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

from promptheus.api.admin import router as admin_router
from promptheus.api.health import router as health_router
from promptheus.config import get_settings
from promptheus.config.settings import Settings
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
            # Use proper session management via container
            session_repo = await container.get_session_repository()
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


async def start_api_server(settings: Settings) -> None:
    """Start FastAPI server for health checks and future API endpoints."""
    if not settings.api_server_enabled:
        logger.info("API server disabled, skipping startup")
        return

    logger.info("Starting API server", host=settings.api_server_host, port=settings.api_server_port)

    # Get dependency container for file watcher access
    container = DependencyContainer.get_instance()

    @contextlib.asynccontextmanager
    async def lifespan(app: FastAPI):
        """Lifespan context manager for FastAPI app."""
        # Startup: Start file watcher
        try:
            file_watcher = await container.get_file_watcher()
            await file_watcher.start()
            logger.info("File watcher started successfully")
        except Exception as e:
            logger.error("Failed to start file watcher", error=str(e))
            # Don't fail startup if file watcher fails, just log

        yield

        # Shutdown: Stop file watcher
        try:
            file_watcher = await container.get_file_watcher()
            await file_watcher.stop()
            logger.info("File watcher stopped successfully")
        except Exception as e:
            logger.error("Error stopping file watcher", error=str(e))

    # Create FastAPI app with lifespan
    app = FastAPI(
        title="Promptheus API",
        description="API server for Promptheus bot health checks and management endpoints",
        version="0.1.0",
        lifespan=lifespan,
    )

    # Include routers
    app.include_router(health_router)
    app.include_router(admin_router, prefix="/admin", tags=["admin"])

    # Configure uvicorn server
    config = uvicorn.Config(
        app=app,
        host=settings.api_server_host,
        port=settings.api_server_port,
        log_level=settings.log_level.lower(),
    )
    server = uvicorn.Server(config)

    try:
        await server.serve()
    except asyncio.CancelledError:
        logger.info("API server cancelled")
        await server.shutdown()
    except Exception as e:
        logger.error("Error in API server", error=str(e))
        raise


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
        level=settings.log_level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        serialize=True,
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


async def start_bot_polling(application: Application, settings: Settings) -> None:
    """Start bot in polling mode (for development)."""
    logger.info("Starting bot in polling mode")

    # Remove any existing webhook to ensure clean state
    try:
        await application.bot.delete_webhook()
        logger.debug("Removed existing webhook (if any)")
    except Exception as e:
        logger.debug("No existing webhook to remove or removal failed", error=str(e))

    # Start polling
    try:
        await application.updater.start_polling(allowed_updates=Update.ALL_TYPES)
    except asyncio.CancelledError:
        logger.info("Bot polling cancelled")
        raise
    except Exception as e:
        logger.error("Error in bot polling", error=str(e))
        raise

    logger.info("Bot is running in polling mode. Press Ctrl+C to stop.")


async def start_bot_webhook(application: Application, settings: Settings) -> None:
    """Start bot in webhook mode (for production)."""
    logger.info("Starting bot in webhook mode", webhook_url=settings.webhook_url)

    if not settings.webhook_url:
        raise ValueError("webhook_url is required for webhook mode")

    # Register webhook with Telegram
    try:
        await application.bot.set_webhook(
            url=settings.webhook_url,
            secret_token=settings.webhook_secret,
        )
        logger.info("Webhook registered successfully with Telegram")
    except Exception as e:
        logger.error("Failed to register webhook with Telegram", error=str(e))
        raise

    # Start webhook server
    try:
        application.run_webhook(
            listen="0.0.0.0",
            port=settings.webhook_port,
            url_path=settings.webhook_path,
            webhook_url=settings.webhook_url,
            secret_token=settings.webhook_secret,
        )
        logger.info(
            "Webhook server started", port=settings.webhook_port, path=settings.webhook_path
        )
    except Exception as e:
        logger.error("Failed to start webhook server", error=str(e))
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
        logger.info("Components initialized successfully")
    except Exception as e:
        logger.critical("Failed to initialize components", error=str(e))
        return

    # Load lessons from content directory
    logger.info("Loading lessons from content directory")
    try:
        lesson_loader = await container.get_lesson_loader_service()
        loaded_count = await lesson_loader.batch_load_all()
        logger.info("Lessons loaded successfully", count=loaded_count)
    except Exception as e:
        logger.critical("Failed to load lessons, exiting", error=str(e))
        return

    # Get bot handlers
    try:
        handlers = await container.get_bot_handlers()
    except Exception as e:
        logger.critical("Failed to initialize bot handlers", error=str(e))
        return

    # Create application
    logger.info("Creating Telegram application")
    try:
        application = Application.builder().token(settings.telegram_bot_token).build()
        logger.debug("Telegram application created")
    except Exception as e:
        logger.critical("Failed to create Telegram application", error=str(e))
        return

    # Initialize rate limiting middleware
    logger.info("Setting up rate limiting middleware")
    try:
        # Rate limiting is implemented in handlers via check_rate_limit method
        logger.info("Rate limiting service initialized")
    except Exception as e:
        logger.critical("Failed to setup rate limiting middleware", error=str(e))
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

    # Initialize tasks
    api_task = None
    bot_task = None

    try:
        # Start API server and bot concurrently
        logger.info("Starting API server and bot...")
        await application.initialize()
        await application.start()

        # Create tasks for API server and bot
        api_task = asyncio.create_task(start_api_server(settings))
        bot_task = asyncio.create_task(
            start_bot_webhook(application, settings)
            if settings.bot_mode == "webhook"
            else start_bot_polling(application, settings)
        )

        # Run both concurrently
        await asyncio.gather(api_task, bot_task, cleanup_task, return_exceptions=True)

    except (KeyboardInterrupt, asyncio.CancelledError):
        logger.info("Shutdown signal received")
    except Exception as e:
        logger.critical("Error during operation", error=str(e))
    finally:
        logger.info("Shutting down services...")

        # Cancel background cleanup task
        if cleanup_task and not cleanup_task.done():
            cleanup_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await cleanup_task
            logger.info("Background session cleanup task stopped")

        # Cancel API task
        if api_task and not api_task.done():
            api_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await api_task
            logger.info("API server task cancelled")

        # Cancel bot task
        if bot_task and not bot_task.done():
            bot_task.cancel()
            with contextlib.suppress(Exception):  # Suppress all exceptions during shutdown
                await bot_task
            logger.info("Bot task cancelled")

        # Stop telegram bot (safe for both polling and webhook modes)
        try:
            # Stop updater first to prevent network errors during shutdown
            if hasattr(application, "updater") and application.updater:
                await application.updater.stop()
                logger.info("Telegram updater stopped")

            await application.stop()
            await application.shutdown()
            logger.info("Telegram application stopped")
        except Exception as e:
            logger.error(f"Error stopping Telegram application: {e}")

        # Cleanup database connections
        try:
            await container.cleanup()
            logger.info("Dependency container cleaned up")
        except Exception as e:
            logger.error(f"Error cleaning up container: {e}")

        logger.info("All services stopped gracefully")


if __name__ == "__main__":
    asyncio.run(main())
