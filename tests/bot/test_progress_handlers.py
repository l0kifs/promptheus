"""Unit tests for progress handlers."""

import pytest
from telegram import Update
from telegram.ext import ContextTypes

from promptheus.bot.base_handlers import BaseBotHandlers
from promptheus.bot.progress_handlers import ProgressHandlersMixin
from promptheus.data.models import LessonStatus, SkillLevel


class MockProgressHandlers(BaseBotHandlers, ProgressHandlersMixin):
    """Mock handlers class for testing."""


class TestProgressHandlers:
    """Tests for ProgressHandlersMixin."""

    @pytest.fixture
    def mock_handlers(self, mocker):
        """Create mock handlers instance."""
        ai_client = mocker.Mock()
        assessment_engine = mocker.Mock()
        learning_orchestrator = mocker.Mock()
        progress_tracker = mocker.Mock()
        rate_limit_service = mocker.Mock()

        # Mock async methods
        learning_orchestrator.get_session_context = mocker.AsyncMock()
        learning_orchestrator.save_session_context = mocker.AsyncMock()
        learning_orchestrator.user_repo = mocker.Mock()
        learning_orchestrator.user_repo.find_by_telegram_id = mocker.AsyncMock()
        learning_orchestrator.lesson_repo = mocker.Mock()
        learning_orchestrator.lesson_repo.find_by_id = mocker.AsyncMock()
        learning_orchestrator.lesson_repo.find_by_skill_level = mocker.AsyncMock()
        progress_tracker.get_progress_summary = mocker.AsyncMock()
        progress_tracker.progress_repo = mocker.Mock()
        progress_tracker.progress_repo.find_by_user = mocker.AsyncMock()

        return MockProgressHandlers(
            ai_client=ai_client,
            assessment_engine=assessment_engine,
            learning_orchestrator=learning_orchestrator,
            progress_tracker=progress_tracker,
            rate_limit_service=rate_limit_service,
        )

    @pytest.fixture
    def mock_callback_update(self, mocker):
        """Create mock Update object with callback_query."""
        update = mocker.Mock(spec=Update)
        update.effective_user = mocker.Mock()
        update.effective_user.id = 12345
        update.callback_query = mocker.Mock()
        update.callback_query.data = "continue"
        return update

    @pytest.fixture
    def mock_context(self, mocker):
        """Create mock ContextTypes object."""
        return mocker.Mock(spec=ContextTypes.DEFAULT_TYPE)

    @pytest.mark.asyncio
    async def test_continue_callback_with_session(
        self, mock_handlers, mock_callback_update, mock_context, mocker
    ):
        """Test continue callback with active session."""
        # Mock user
        mock_user = mocker.Mock()
        mock_user.skill_level = SkillLevel.BEGINNER
        mock_handlers.learning_orchestrator.user_repo.find_by_telegram_id.return_value = mock_user

        # Mock session context with active lesson
        session_context = {"current_lesson_id": 1, "lesson_step": "theory", "theory_section": 0}
        mock_handlers.learning_orchestrator.get_session_context = mocker.AsyncMock(
            return_value=session_context
        )

        # Mock lesson
        mock_lesson = mocker.Mock()
        mock_lesson.title = "Active Lesson"
        mock_handlers.learning_orchestrator.lesson_repo.find_by_id.return_value = mock_lesson

        # Mock callback operations
        mock_callback_update.callback_query.answer = mocker.AsyncMock()
        mock_callback_update.callback_query.edit_message_text = mocker.AsyncMock()

        await mock_handlers.continue_callback(mock_callback_update, mock_context)

        # Verify resume message shown
        mock_callback_update.callback_query.edit_message_text.assert_called_once()
        call_args = mock_callback_update.callback_query.edit_message_text.call_args
        assert "Resume Learning" in call_args[0][0]
        assert "Active Lesson" in call_args[0][0]
        assert "theory" in call_args[0][0].lower()

    @pytest.mark.asyncio
    async def test_continue_callback_with_user_current_lesson(
        self, mock_handlers, mock_callback_update, mock_context, mocker
    ):
        """Test continue callback showing next lesson when no progress records exist."""
        # Mock user with current lesson (no longer used in new logic)
        mock_user = mocker.Mock()
        mock_user.skill_level = SkillLevel.BEGINNER
        mock_user.current_lesson_id = 2
        mock_handlers.learning_orchestrator.user_repo.find_by_telegram_id.return_value = mock_user

        # Mock empty session context
        mock_handlers.learning_orchestrator.get_session_context = mocker.AsyncMock(return_value={})

        # Mock empty progress records (no IN_PROGRESS or NOT_STARTED lessons)
        mock_handlers.progress_tracker.progress_repo.find_by_user.return_value = []

        # Mock lessons for skill level
        mock_lessons = [
            mocker.Mock(title="Lesson 1", id=1),
            mocker.Mock(title="Lesson 2", id=2),
        ]
        mock_handlers.learning_orchestrator.lesson_repo.find_by_skill_level.return_value = (
            mock_lessons
        )

        # Mock callback operations
        mock_callback_update.callback_query.answer = mocker.AsyncMock()
        mock_callback_update.callback_query.edit_message_text = mocker.AsyncMock()

        await mock_handlers.continue_callback(mock_callback_update, mock_context)

        # Verify next lesson shown (first lesson when no progress)
        mock_callback_update.callback_query.edit_message_text.assert_called_once()
        call_args = mock_callback_update.callback_query.edit_message_text.call_args
        assert "Continue Learning" in call_args[0][0]
        assert "Next lesson:" in call_args[0][0]
        assert "Lesson 1" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_continue_callback_with_in_progress_lesson(
        self, mock_handlers, mock_callback_update, mock_context, mocker
    ):
        """Test continue callback prioritizing IN_PROGRESS lesson."""
        # Mock user
        mock_user = mocker.Mock()
        mock_user.skill_level = SkillLevel.BEGINNER
        mock_handlers.learning_orchestrator.user_repo.find_by_telegram_id.return_value = mock_user

        # Mock empty session context
        mock_handlers.learning_orchestrator.get_session_context = mocker.AsyncMock(return_value={})

        # Mock progress records with IN_PROGRESS lesson
        mock_progress_in_progress = mocker.Mock()
        mock_progress_in_progress.lesson_id = 2
        mock_progress_in_progress.status = LessonStatus.IN_PROGRESS

        mock_progress_completed = mocker.Mock()
        mock_progress_completed.lesson_id = 1
        mock_progress_completed.status = LessonStatus.COMPLETED

        mock_handlers.progress_tracker.progress_repo.find_by_user.return_value = [
            mock_progress_completed,
            mock_progress_in_progress,
        ]

        # Mock IN_PROGRESS lesson
        mock_lesson = mocker.Mock()
        mock_lesson.title = "In Progress Lesson"
        mock_handlers.learning_orchestrator.lesson_repo.find_by_id.return_value = mock_lesson

        # Mock callback operations
        mock_callback_update.callback_query.answer = mocker.AsyncMock()
        mock_callback_update.callback_query.edit_message_text = mocker.AsyncMock()

        await mock_handlers.continue_callback(mock_callback_update, mock_context)

        # Verify IN_PROGRESS lesson resume shown
        mock_callback_update.callback_query.edit_message_text.assert_called_once()
        call_args = mock_callback_update.callback_query.edit_message_text.call_args
        assert "Continue Learning" in call_args[0][0]
        assert "In Progress Lesson" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_continue_callback_show_lesson_list(
        self, mock_handlers, mock_callback_update, mock_context, mocker
    ):
        """Test continue callback showing next lesson when no progress records exist."""
        # Mock user without current lesson
        mock_user = mocker.Mock()
        mock_user.skill_level = SkillLevel.BEGINNER
        mock_user.current_lesson_id = None
        mock_handlers.learning_orchestrator.user_repo.find_by_telegram_id.return_value = mock_user

        # Mock empty session context
        mock_handlers.learning_orchestrator.get_session_context = mocker.AsyncMock(return_value={})

        # Mock empty progress records
        mock_handlers.progress_tracker.progress_repo.find_by_user.return_value = []

        # Mock lessons
        mock_lessons = [
            mocker.Mock(title="Lesson 1", id=1),
            mocker.Mock(title="Lesson 2", id=2),
        ]
        mock_handlers.learning_orchestrator.lesson_repo.find_by_skill_level.return_value = (
            mock_lessons
        )

        # Mock callback operations
        mock_callback_update.callback_query.answer = mocker.AsyncMock()
        mock_callback_update.callback_query.edit_message_text = mocker.AsyncMock()

        await mock_handlers.continue_callback(mock_callback_update, mock_context)

        # Verify next lesson shown (first lesson when no progress)
        mock_callback_update.callback_query.edit_message_text.assert_called_once()
        call_args = mock_callback_update.callback_query.edit_message_text.call_args
        assert "Continue Learning" in call_args[0][0]
        assert "Next lesson:" in call_args[0][0]
        assert "Lesson 1" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_continue_callback_fallback_to_beginner(
        self, mock_handlers, mock_callback_update, mock_context, mocker
    ):
        """Test continue callback falling back to beginner lessons."""
        # Mock user
        mock_user = mocker.Mock()
        mock_user.skill_level = SkillLevel.ADVANCED
        mock_user.current_lesson_id = None
        mock_handlers.learning_orchestrator.user_repo.find_by_telegram_id.return_value = mock_user

        # Mock no lessons for advanced level, then beginner lessons
        mock_handlers.learning_orchestrator.lesson_repo.find_by_skill_level.side_effect = [
            [],  # No advanced lessons (first call)
            [],  # No advanced lessons (second call in fallback)
            [mocker.Mock(title="Beginner Lesson", id=1)],  # Fallback to beginner
        ]

        # Mock empty session context
        mock_handlers.learning_orchestrator.get_session_context = mocker.AsyncMock(return_value={})

        # Mock callback operations
        mock_callback_update.callback_query.answer = mocker.AsyncMock()
        mock_callback_update.callback_query.edit_message_text = mocker.AsyncMock()

        await mock_handlers.continue_callback(mock_callback_update, mock_context)

        # Verify fallback to beginner lessons
        assert mock_handlers.learning_orchestrator.lesson_repo.find_by_skill_level.call_count == 3
        calls = mock_handlers.learning_orchestrator.lesson_repo.find_by_skill_level.call_args_list
        assert calls[0][0][0] == SkillLevel.ADVANCED  # First attempt
        assert calls[1][0][0] == SkillLevel.ADVANCED  # Second attempt in fallback
        assert calls[2][0][0] == SkillLevel.BEGINNER  # Fallback to beginner

        # Verify beginner lesson shown
        mock_callback_update.callback_query.edit_message_text.assert_called_once()
        call_args = mock_callback_update.callback_query.edit_message_text.call_args
        assert "Beginner Lesson" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_progress_callback(
        self, mock_handlers, mock_callback_update, mock_context, mocker
    ):
        """Test progress view callback."""
        # Mock user
        mock_user = mocker.Mock()
        mock_user.skill_level = SkillLevel.INTERMEDIATE
        mock_user.learning_goal = mocker.Mock()
        mock_user.learning_goal.value = "professional"
        mock_handlers.learning_orchestrator.user_repo.find_by_telegram_id.return_value = mock_user

        # Mock progress summary
        summary = {"completed": 3, "total": 5, "average_score": 8.5}
        mock_handlers.progress_tracker.get_progress_summary.return_value = summary

        # Mock progress records
        mock_progress_records = [
            mocker.Mock(lesson_id=1, status=LessonStatus.COMPLETED, last_score=9),
            mocker.Mock(lesson_id=2, status=LessonStatus.COMPLETED, last_score=8),
            mocker.Mock(lesson_id=3, status=LessonStatus.IN_PROGRESS, last_score=None),
        ]
        mock_handlers.progress_tracker.progress_repo.find_by_user.return_value = (
            mock_progress_records
        )

        # Mock lessons for progress records
        mock_lesson1 = mocker.Mock()
        mock_lesson1.title = "Completed Lesson 1"
        mock_lesson2 = mocker.Mock()
        mock_lesson2.title = "Completed Lesson 2"
        mock_lesson3 = mocker.Mock()
        mock_lesson3.title = "In Progress Lesson 3"
        mock_handlers.learning_orchestrator.lesson_repo.find_by_id.side_effect = [
            mock_lesson1,
            mock_lesson2,
            mock_lesson3,
        ]

        # Mock callback operations
        mock_callback_update.callback_query.answer = mocker.AsyncMock()
        mock_callback_update.callback_query.edit_message_text = mocker.AsyncMock()

        await mock_handlers.progress_callback(mock_callback_update, mock_context)

        # Verify progress summary retrieved
        mock_handlers.progress_tracker.get_progress_summary.assert_called_once_with(12345)

        # Verify progress shown
        mock_callback_update.callback_query.edit_message_text.assert_called_once()
        call_args = mock_callback_update.callback_query.edit_message_text.call_args
        progress_text = call_args[0][0]
        assert "Your Progress" in progress_text
        assert "intermediate" in progress_text.lower()
        assert "professional" in progress_text.lower()
        assert "3/5" in progress_text
        assert "8.5/10" in progress_text
        assert "Completed Lesson 1" in progress_text
        assert "Completed Lesson 2" in progress_text

    @pytest.mark.asyncio
    async def test_progress_callback_user_not_found(
        self, mock_handlers, mock_callback_update, mock_context, mocker
    ):
        """Test progress callback when user not found."""
        # Mock user not found
        mock_handlers.learning_orchestrator.user_repo.find_by_telegram_id.return_value = None

        # Mock callback operations
        mock_callback_update.callback_query.answer = mocker.AsyncMock()
        mock_callback_update.callback_query.edit_message_text = mocker.AsyncMock()

        await mock_handlers.progress_callback(mock_callback_update, mock_context)

        # Verify error message shown
        mock_callback_update.callback_query.edit_message_text.assert_called_once()
        call_args = mock_callback_update.callback_query.edit_message_text.call_args
        assert "not found" in call_args[0][0].lower()

    @pytest.mark.asyncio
    async def test_invalid_callbacks(self, mock_handlers, mocker):
        """Test callbacks with invalid updates."""
        # Test with missing user
        update = mocker.Mock(spec=Update)
        update.effective_user = None
        update.callback_query = mocker.Mock()

        context = mocker.Mock()

        # Should not raise exceptions
        await mock_handlers.continue_callback(update, context)
        await mock_handlers.progress_callback(update, context)
