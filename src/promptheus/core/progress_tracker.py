"""Progress tracking for user learning."""

from datetime import UTC, datetime

from loguru import logger

from promptheus.data.async_repositories import AsyncProgressRepository
from promptheus.data.models import LessonStatus


class ProgressTracker:
    """Tracker for user progress."""

    def __init__(self, progress_repo: AsyncProgressRepository) -> None:
        """Initialize progress tracker."""
        self.progress_repo = progress_repo

    async def start_lesson(self, user_id: int, lesson_id: int) -> None:
        """Start a lesson for user - creates progress record as NOT_STARTED."""
        logger.info("Starting lesson", user_id=user_id, lesson_id=lesson_id)
        progress = await self.progress_repo.find_by_user_and_lesson(user_id, lesson_id)
        if not progress:
            await self.progress_repo.create(user_id, lesson_id)
            logger.info("Lesson progress initialized", user_id=user_id, lesson_id=lesson_id)
        else:
            logger.debug("Lesson already has progress record", user_id=user_id, lesson_id=lesson_id)

    async def mark_completed(self, user_id: int, lesson_id: int, score: int) -> None:
        """Mark lesson as completed."""
        logger.info(
            "Marking lesson as completed", user_id=user_id, lesson_id=lesson_id, score=score
        )
        await self.progress_repo.update_status(user_id, lesson_id, LessonStatus.COMPLETED)
        await self.progress_repo.update_score(user_id, lesson_id, score)
        logger.info("Lesson marked as completed", user_id=user_id, lesson_id=lesson_id)

    async def record_attempt(self, user_id: int, lesson_id: int, score: int) -> None:
        """Record exercise attempt."""
        logger.info("Recording attempt", user_id=user_id, lesson_id=lesson_id, score=score)
        await self.progress_repo.increment_attempts(user_id, lesson_id)
        await self.progress_repo.update_score(user_id, lesson_id, score)

    async def increment_attempts(self, user_id: int, lesson_id: int) -> None:
        """Increment attempt counter for a lesson."""
        logger.debug("Incrementing attempts", user_id=user_id, lesson_id=lesson_id)
        await self.progress_repo.increment_attempts(user_id, lesson_id)

    async def complete_lesson(self, user_id: int, lesson_id: int, score: int) -> None:
        """Mark lesson as completed with final score."""
        logger.info("Completing lesson", user_id=user_id, lesson_id=lesson_id, score=score)
        await self.progress_repo.update_status(user_id, lesson_id, LessonStatus.COMPLETED)
        await self.progress_repo.update_score(user_id, lesson_id, score)
        await self.progress_repo.update_completed_at(user_id, lesson_id, datetime.now(UTC))
        logger.info(
            "Lesson completed successfully", user_id=user_id, lesson_id=lesson_id, score=score
        )

    async def get_progress_summary(self, user_id: int) -> dict[str, int | float]:
        """Get progress summary for user."""
        logger.debug("Getting progress summary", user_id=user_id)
        progress_records = await self.progress_repo.find_by_user(user_id)

        completed = sum(
            1
            for p in progress_records
            if p.status == LessonStatus.COMPLETED  # type: ignore
        )
        total = len(progress_records)

        scores = [int(p.last_score) for p in progress_records if p.last_score is not None]  # type: ignore
        avg_score = sum(scores) / len(scores) if scores else 0.0

        summary = {
            "completed": completed,
            "total": total,
            "average_score": round(avg_score, 1),
        }

        logger.info(
            "Progress summary generated",
            user_id=user_id,
            completed=completed,
            total=total,
            avg_score=avg_score,
        )

        return summary

    async def mark_in_progress(self, user_id: int, lesson_id: int) -> None:
        """Mark lesson as in progress when user starts reading theory."""
        logger.info("Marking lesson as in progress", user_id=user_id, lesson_id=lesson_id)
        await self.progress_repo.update_status(user_id, lesson_id, LessonStatus.IN_PROGRESS)
        logger.info("Lesson marked as in progress", user_id=user_id, lesson_id=lesson_id)
