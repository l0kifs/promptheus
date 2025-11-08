"""Tests for ProgressTracker."""

from datetime import datetime

import pytest

from promptheus.core.progress_tracker import ProgressTracker
from promptheus.data.models import LessonStatus


class TestProgressTracker:
    """Tests for ProgressTracker."""

    @pytest.fixture
    def tracker(self, mocker):
        """Create progress tracker with mocked repo."""
        mock_repo = mocker.AsyncMock()
        return ProgressTracker(mock_repo)

    @pytest.mark.asyncio
    async def test_start_lesson_when_no_existing_progress_creates_new_progress(self, tracker):
        """Test starting a lesson when no existing progress exists."""
        user_id = 123
        lesson_id = 456

        # Mock the repo to return None (no existing progress)
        tracker.progress_repo.find_by_user_and_lesson.return_value = None
        tracker.progress_repo.create.return_value = None

        await tracker.start_lesson(user_id, lesson_id)

        # Verify the repo methods were called correctly
        tracker.progress_repo.find_by_user_and_lesson.assert_called_once_with(user_id, lesson_id)
        tracker.progress_repo.create.assert_called_once_with(user_id, lesson_id)

    @pytest.mark.asyncio
    async def test_mark_completed_updates_status_and_score(self, tracker):
        """Test marking lesson as completed."""
        user_id = 123
        lesson_id = 456
        score = 85

        # Create a mock progress object
        mock_progress = type(
            "MockProgress", (), {"status": None, "last_score": None, "completed_at": None}
        )()

        tracker.progress_repo.find_by_user_and_lesson.return_value = mock_progress

        await tracker.mark_completed(user_id, lesson_id, score)

        # Verify the repo methods were called
        tracker.progress_repo.update_status.assert_called_once_with(
            user_id, lesson_id, LessonStatus.COMPLETED
        )
        tracker.progress_repo.update_score.assert_called_once_with(user_id, lesson_id, score)

    @pytest.mark.asyncio
    async def test_record_attempt_increments_attempts_and_updates_score(self, tracker):
        """Test recording exercise attempt."""
        user_id = 123
        lesson_id = 456
        score = 75

        # Create a mock progress object
        mock_progress = type("MockProgress", (), {"attempts": 0, "last_score": None})()

        tracker.progress_repo.find_by_user_and_lesson.return_value = mock_progress

        await tracker.record_attempt(user_id, lesson_id, score)

        # Verify the repo methods were called
        tracker.progress_repo.increment_attempts.assert_called_once_with(user_id, lesson_id)
        tracker.progress_repo.update_score.assert_called_once_with(user_id, lesson_id, score)

    @pytest.mark.asyncio
    async def test_get_progress_summary_calculates_completed_total_and_average_score(self, tracker):
        """Test getting progress summary."""
        user_id = 123

        # Create mock progress records
        mock_progresses = [
            type("MockProgress", (), {"status": LessonStatus.COMPLETED, "last_score": 80})(),
            type("MockProgress", (), {"status": LessonStatus.COMPLETED, "last_score": 90})(),
            type("MockProgress", (), {"status": LessonStatus.IN_PROGRESS, "last_score": None})(),
        ]

        tracker.progress_repo.find_by_user.return_value = mock_progresses

        summary = await tracker.get_progress_summary(user_id)

        assert summary["completed"] == 2
        assert summary["total"] == 3
        assert summary["average_score"] == 85.0

    @pytest.mark.asyncio
    async def test_get_progress_summary_with_no_scores_returns_zero_average(self, tracker):
        """Test getting progress summary when no scores are available."""
        user_id = 123

        # Create mock progress records with no scores
        mock_progresses = [
            type("MockProgress", (), {"status": LessonStatus.COMPLETED, "last_score": None})(),
            type("MockProgress", (), {"status": LessonStatus.IN_PROGRESS, "last_score": None})(),
        ]

        tracker.progress_repo.find_by_user.return_value = mock_progresses

        summary = await tracker.get_progress_summary(user_id)

        assert summary["completed"] == 1
        assert summary["total"] == 2
        assert summary["average_score"] == 0.0

    @pytest.mark.asyncio
    async def test_increment_attempts_calls_repository_method(self, tracker):
        """Test incrementing attempt counter."""
        user_id = 123
        lesson_id = 456

        await tracker.increment_attempts(user_id, lesson_id)

        # Verify the repo method was called
        tracker.progress_repo.increment_attempts.assert_called_once_with(user_id, lesson_id)

    @pytest.mark.asyncio
    async def test_complete_lesson_updates_status_score_and_timestamp(self, tracker):
        """Test completing a lesson with final score and timestamp."""
        user_id = 123
        lesson_id = 456
        score = 90

        await tracker.complete_lesson(user_id, lesson_id, score)

        # Verify the repo methods were called
        tracker.progress_repo.update_status.assert_called_once_with(
            user_id, lesson_id, LessonStatus.COMPLETED
        )
        tracker.progress_repo.update_score.assert_called_once_with(user_id, lesson_id, score)
        tracker.progress_repo.update_completed_at.assert_called_once()
        # Verify the timestamp was passed (can't check exact value due to timing)
        call_args = tracker.progress_repo.update_completed_at.call_args
        assert call_args[0][0] == user_id
        assert call_args[0][1] == lesson_id
        assert isinstance(call_args[0][2], datetime)

    @pytest.mark.asyncio
    async def test_mark_in_progress_updates_status_to_in_progress(self, tracker):
        """Test marking lesson as in progress."""
        user_id = 123
        lesson_id = 456

        await tracker.mark_in_progress(user_id, lesson_id)

        # Verify the repo method was called
        tracker.progress_repo.update_status.assert_called_once_with(
            user_id, lesson_id, LessonStatus.IN_PROGRESS
        )
