"""Progress tracking for user learning."""

from datetime import datetime

from sqlalchemy.orm import Session

from promptheus.data.models import LessonStatus
from promptheus.data.repositories import ProgressRepository


class ProgressTracker:
    """Tracker for user progress."""

    def __init__(self, db: Session) -> None:
        """Initialize progress tracker."""
        self.progress_repo = ProgressRepository(db)

    def start_lesson(self, user_id: int, lesson_id: int) -> None:
        """Start a lesson for user."""
        progress = self.progress_repo.find_by_user_and_lesson(user_id, lesson_id)
        if not progress:
            self.progress_repo.create(user_id, lesson_id)

    def mark_completed(self, user_id: int, lesson_id: int, score: int) -> None:
        """Mark lesson as completed."""
        progress = self.progress_repo.find_by_user_and_lesson(user_id, lesson_id)
        if progress:
            progress.status = LessonStatus.COMPLETED  # type: ignore
            progress.last_score = score  # type: ignore
            progress.completed_at = datetime.utcnow()  # type: ignore

    def record_attempt(self, user_id: int, lesson_id: int, score: int) -> None:
        """Record exercise attempt."""
        self.progress_repo.increment_attempts(user_id, lesson_id)
        self.progress_repo.update_score(user_id, lesson_id, score)

    def increment_attempts(self, user_id: int, lesson_id: int) -> None:
        """Increment attempt counter for a lesson."""
        self.progress_repo.increment_attempts(user_id, lesson_id)

    def complete_lesson(self, user_id: int, lesson_id: int, score: int) -> None:
        """Mark lesson as completed with final score."""
        progress = self.progress_repo.find_by_user_and_lesson(user_id, lesson_id)
        if progress:
            progress.status = LessonStatus.COMPLETED  # type: ignore
            progress.last_score = score  # type: ignore
            progress.completed_at = datetime.utcnow()  # type: ignore

    def get_progress_summary(self, user_id: int) -> dict[str, int | float]:
        """Get progress summary for user."""
        progress_records = self.progress_repo.find_by_user(user_id)

        completed = sum(
            1 for p in progress_records if p.status == LessonStatus.COMPLETED
        )
        total = len(progress_records)

        scores = [p.last_score for p in progress_records if p.last_score is not None]
        avg_score = sum(scores) / len(scores) if scores else 0

        return {
            "completed": completed,
            "total": total,
            "average_score": round(avg_score, 1),
        }
