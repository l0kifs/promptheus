#!/usr/bin/env python3
"""Quick validation script to test bot configuration and database."""

import asyncio

from loguru import logger

from promptheus.ai.openrouter_client import OpenRouterClient
from promptheus.config import get_settings
from promptheus.data.database import get_db
from promptheus.data.models import SkillLevel
from promptheus.data.repositories import LessonRepository


async def validate_configuration():
    """Validate configuration and connections."""
    logger.info("Validating configuration...")

    settings = get_settings()

    # Check required settings
    assert settings.telegram_bot_token, "TELEGRAM_BOT_TOKEN is required"
    assert settings.openrouter_api_key, "OPENROUTER_API_KEY is required"
    assert settings.database_url, "DATABASE_URL is required"

    logger.success("✓ Configuration validated")


async def validate_database():
    """Validate database and lessons."""
    logger.info("Validating database...")

    with get_db() as db:
        lesson_repo = LessonRepository(db)
        lessons = lesson_repo.find_by_skill_level(SkillLevel.BEGINNER)

        assert len(lessons) == 5, f"Expected 5 lessons, found {len(lessons)}"

        logger.info(f"Found {len(lessons)} beginner lessons:")
        for lesson in lessons:
            logger.info(f"  {lesson.order_index}. {lesson.title}")

    logger.success("✓ Database validated")


async def validate_ai_client():
    """Validate AI client configuration."""
    logger.info("Validating AI client...")

    ai_client = OpenRouterClient()

    # Just check that the client is properly configured
    assert ai_client.settings.openrouter_api_key, "OpenRouter API key not configured"
    assert ai_client.base_url == "https://openrouter.ai/api/v1"

    logger.success("✓ AI client configured")


async def main():
    """Run all validations."""
    logger.info("=" * 60)
    logger.info("Starting Promptheus MVP Validation")
    logger.info("=" * 60)

    try:
        await validate_configuration()
        await validate_database()
        await validate_ai_client()

        logger.info("=" * 60)
        logger.success("✓ All validations passed!")
        logger.info("=" * 60)
        logger.info("")
        logger.info("Next steps:")
        logger.info("1. Start the bot: uv run python -m promptheus.main")
        logger.info("2. Open Telegram and find your bot")
        logger.info("3. Send /start to begin")
        logger.info("")
        logger.info("The bot is ready for testing! 🚀")

    except Exception as e:
        logger.error(f"Validation failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
