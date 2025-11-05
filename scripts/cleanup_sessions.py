#!/usr/bin/env python3
"""Session cleanup script to remove old user sessions."""

import asyncio
import sys
from datetime import UTC, datetime

from loguru import logger

from promptheus.data.async_repositories import AsyncSessionRepository
from promptheus.data.database import get_async_db


async def cleanup_sessions(days_old: int = 30):
    """Clean up sessions older than specified days."""
    logger.info("Starting session cleanup process", days_old=days_old)

    async with get_async_db() as db:
        session_repo = AsyncSessionRepository(db)

        try:
            deleted_count = await session_repo.cleanup_old_sessions(days_old)
            logger.success(f"Session cleanup completed. Deleted {deleted_count} old sessions.")
        except Exception as e:
            logger.error(f"Session cleanup failed: {e}")
            raise


async def main():
    """Run session cleanup."""
    # Parse command line arguments
    days_old = 30
    if len(sys.argv) > 1:
        try:
            days_old = int(sys.argv[1])
        except ValueError:
            logger.error("Invalid number of days. Using default: 30")
            days_old = 30

    logger.info("=" * 60)
    logger.info("Promptheus Session Cleanup")
    logger.info("=" * 60)
    logger.info(f"Cleaning sessions older than {days_old} days")
    logger.info(f"Current time: {datetime.now(UTC)}")
    logger.info("=" * 60)

    await cleanup_sessions(days_old)

    logger.info("=" * 60)
    logger.success("Session cleanup completed successfully!")
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
