"""Unit tests for lesson handlers."""

import pytest
from telegram import InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from promptheus.bot.base_handlers import BaseBotHandlers
from promptheus.bot.lesson_handlers import LessonHandlersMixin
from promptheus.data.models import SkillLevel


class MockLessonHandlers(BaseBotHandlers, LessonHandlersMixin):
    """Mock handlers class for testing."""


class TestLessonHandlers:
    """Tests for LessonHandlersMixin."""

    @pytest.fixture
    def mock_handlers(self, mocker):
        """Create mock handlers instance."""
        ai_client = mocker.Mock()
        assessment_engine = mocker.Mock()
        learning_orchestrator = mocker.Mock()
        progress_tracker = mocker.Mock()

        # Mock async methods
        learning_orchestrator.get_session_context = mocker.AsyncMock()
        learning_orchestrator.save_session_context = mocker.AsyncMock()
        learning_orchestrator.lesson_repo = mocker.Mock()
        learning_orchestrator.lesson_repo.find_by_id = mocker.AsyncMock()
        learning_orchestrator.lesson_repo.find_by_skill_level = mocker.AsyncMock()
        learning_orchestrator.lesson_repo.find_next_lesson = mocker.AsyncMock()
        learning_orchestrator.user_repo = mocker.Mock()
        learning_orchestrator.user_repo.find_by_telegram_id = mocker.AsyncMock()
        progress_tracker.start_lesson = mocker.AsyncMock()

        return MockLessonHandlers(
            ai_client=ai_client,
            assessment_engine=assessment_engine,
            learning_orchestrator=learning_orchestrator,
            progress_tracker=progress_tracker,
        )

    @pytest.fixture
    def mock_callback_update(self, mocker):
        """Create mock Update object with callback_query."""
        update = mocker.Mock(spec=Update)
        update.effective_user = mocker.Mock()
        update.effective_user.id = 12345
        update.callback_query = mocker.Mock()
        update.callback_query.data = "lesson_1"
        return update

    @pytest.fixture
    def mock_context(self, mocker):
        """Create mock ContextTypes object."""
        return mocker.Mock(spec=ContextTypes.DEFAULT_TYPE)

    @pytest.mark.asyncio
    async def test_lesson_callback(self, mock_handlers, mock_callback_update, mock_context, mocker):
        """Test lesson selection callback."""
        # Mock lesson
        mock_lesson = mocker.Mock()
        mock_lesson.title = "Test Lesson"
        mock_lesson.order_index = 1
        mock_handlers.learning_orchestrator.lesson_repo.find_by_id.return_value = mock_lesson

        # Mock session operations
        mock_handlers.learning_orchestrator.get_session_context.return_value = {}

        # Mock callback operations
        mock_callback_update.callback_query.answer = mocker.AsyncMock()
        mock_callback_update.callback_query.edit_message_text = mocker.AsyncMock()

        await mock_handlers.lesson_callback(mock_callback_update, mock_context)

        # Verify lesson retrieved
        mock_handlers.learning_orchestrator.lesson_repo.find_by_id.assert_called_once_with(1)

        # Verify progress started
        mock_handlers.progress_tracker.start_lesson.assert_called_once_with(12345, 1)

        # Verify session updated
        expected_context = {"current_lesson_id": 1, "lesson_step": "start"}
        mock_handlers.learning_orchestrator.save_session_context.assert_called_with(
            12345, expected_context
        )

        # Verify lesson start message shown
        mock_callback_update.callback_query.edit_message_text.assert_called_once()
        call_args = mock_callback_update.callback_query.edit_message_text.call_args
        assert "Test Lesson" in call_args[0][0]
        assert "Lesson 1:" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_lesson_callback_lesson_not_found(
        self, mock_handlers, mock_callback_update, mock_context, mocker
    ):
        """Test lesson callback when lesson not found."""
        # Mock lesson not found
        mock_handlers.learning_orchestrator.lesson_repo.find_by_id.return_value = None

        # Mock callback operations
        mock_callback_update.callback_query.answer = mocker.AsyncMock()
        mock_callback_update.callback_query.edit_message_text = mocker.AsyncMock()

        await mock_handlers.lesson_callback(mock_callback_update, mock_context)

        # Verify error message shown
        mock_callback_update.callback_query.edit_message_text.assert_called_once()
        call_args = mock_callback_update.callback_query.edit_message_text.call_args
        assert "not found" in call_args[0][0].lower()

    @pytest.mark.asyncio
    async def test_lesson_list_callback(
        self, mock_handlers, mock_callback_update, mock_context, mocker
    ):
        """Test lesson list callback."""
        # Mock user
        mock_user = mocker.Mock()
        mock_user.skill_level = SkillLevel.BEGINNER
        mock_handlers.learning_orchestrator.user_repo.find_by_telegram_id.return_value = mock_user

        # Mock lessons
        mock_lessons = [
            mocker.Mock(title="Lesson 1", id=1),
            mocker.Mock(title="Lesson 2", id=2),
            mocker.Mock(title="Lesson 3", id=3),
        ]
        mock_handlers.learning_orchestrator.lesson_repo.find_by_skill_level.return_value = (
            mock_lessons
        )

        # Mock callback operations
        mock_callback_update.callback_query.answer = mocker.AsyncMock()
        mock_callback_update.callback_query.edit_message_text = mocker.AsyncMock()

        await mock_handlers.lesson_list_callback(mock_callback_update, mock_context)

        # Verify lessons retrieved
        mock_handlers.learning_orchestrator.lesson_repo.find_by_skill_level.assert_called_once_with(
            SkillLevel.BEGINNER
        )

        # Verify lesson list shown
        mock_callback_update.callback_query.edit_message_text.assert_called_once()
        call_args = mock_callback_update.callback_query.edit_message_text.call_args
        assert "Available Lessons" in call_args[0][0]
        assert "Lesson 1" in call_args[0][0]
        assert "Lesson 2" in call_args[0][0]
        assert isinstance(call_args[1]["reply_markup"], InlineKeyboardMarkup)

    @pytest.mark.asyncio
    async def test_lesson_list_callback_no_lessons(
        self, mock_handlers, mock_callback_update, mock_context, mocker
    ):
        """Test lesson list callback when no lessons available."""
        # Mock user
        mock_user = mocker.Mock()
        mock_user.skill_level = SkillLevel.BEGINNER
        mock_handlers.learning_orchestrator.user_repo.find_by_telegram_id.return_value = mock_user

        # Mock no lessons
        mock_handlers.learning_orchestrator.lesson_repo.find_by_skill_level.return_value = []

        # Mock callback operations
        mock_callback_update.callback_query.answer = mocker.AsyncMock()
        mock_callback_update.callback_query.edit_message_text = mocker.AsyncMock()

        await mock_handlers.lesson_list_callback(mock_callback_update, mock_context)

        # Verify error message shown
        mock_callback_update.callback_query.edit_message_text.assert_called_once()
        call_args = mock_callback_update.callback_query.edit_message_text.call_args
        assert "no lessons available" in call_args[0][0].lower()

    @pytest.mark.asyncio
    async def test_lesson_start_callback(
        self, mock_handlers, mock_callback_update, mock_context, mocker
    ):
        """Test lesson start callback."""
        mock_callback_update.callback_query.data = "lesson_start_1"

        # Mock lesson with theory content
        mock_lesson = mocker.Mock()
        mock_lesson.title = "Test Lesson"
        mock_lesson.order_index = 1
        mock_lesson.theory_content = {
            "sections": [{"content": "Section 1"}, {"content": "Section 2"}]
        }
        mock_handlers.learning_orchestrator.lesson_repo.find_by_id.return_value = mock_lesson

        # Mock session operations
        mock_handlers.learning_orchestrator.get_session_context.return_value = {}

        # Mock callback operations
        mock_callback_update.callback_query.answer = mocker.AsyncMock()
        mock_callback_update.callback_query.edit_message_text = mocker.AsyncMock()

        await mock_handlers.lesson_start_callback(mock_callback_update, mock_context)

        # Verify session updated for theory
        expected_context = {"current_lesson_id": 1, "theory_section": 0, "lesson_step": "theory"}
        mock_handlers.learning_orchestrator.save_session_context.assert_called_with(
            12345, expected_context
        )

        # Verify first theory section shown
        mock_callback_update.callback_query.edit_message_text.assert_called_once()
        call_args = mock_callback_update.callback_query.edit_message_text.call_args
        assert "Theory" in call_args[0][0]
        assert "(1/2)" in call_args[0][0]
        assert "Section 1" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_theory_next_callback(
        self, mock_handlers, mock_callback_update, mock_context, mocker
    ):
        """Test theory next section callback."""
        mock_callback_update.callback_query.data = "theory_next_1"

        # Mock lesson
        mock_lesson = mocker.Mock()
        mock_lesson.theory_content = {
            "sections": [{"content": "Section 1"}, {"content": "Section 2"}]
        }
        mock_handlers.learning_orchestrator.lesson_repo.find_by_id.return_value = mock_lesson

        # Mock session context
        session_context = {"theory_section": 0}
        mock_handlers.learning_orchestrator.get_session_context.return_value = session_context

        # Mock callback operations
        mock_callback_update.callback_query.answer = mocker.AsyncMock()
        mock_callback_update.callback_query.edit_message_text = mocker.AsyncMock()

        await mock_handlers.theory_next_callback(mock_callback_update, mock_context)

        # Verify session updated
        expected_context = {"theory_section": 1}
        mock_handlers.learning_orchestrator.save_session_context.assert_called_with(
            12345, expected_context
        )

        # Verify next section shown
        mock_callback_update.callback_query.edit_message_text.assert_called_once()
        call_args = mock_callback_update.callback_query.edit_message_text.call_args
        assert "(2/2)" in call_args[0][0]
        assert "Section 2" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_theory_next_to_examples(
        self, mock_handlers, mock_callback_update, mock_context, mocker
    ):
        """Test theory next when reaching end - should move to examples."""
        mock_callback_update.callback_query.data = "theory_next_1"

        # Mock lesson
        mock_lesson = mocker.Mock()
        mock_lesson.theory_content = {"sections": [{"content": "Section 1"}]}
        mock_handlers.learning_orchestrator.lesson_repo.find_by_id.return_value = mock_lesson

        # Mock session context
        session_context = {"theory_section": 0}
        mock_handlers.learning_orchestrator.get_session_context.return_value = session_context

        # Mock examples callback (should be called when theory ends)
        mock_handlers.examples_callback = mocker.AsyncMock()

        # Mock callback operations
        mock_callback_update.callback_query.answer = mocker.AsyncMock()

        await mock_handlers.theory_next_callback(mock_callback_update, mock_context)

        # Verify moved to examples
        expected_context = {"theory_section": 0, "lesson_step": "examples"}
        mock_handlers.learning_orchestrator.save_session_context.assert_called_with(
            12345, expected_context
        )

        # Verify examples callback called
        mock_handlers.examples_callback.assert_called_once()

    @pytest.mark.asyncio
    async def test_theory_prev_callback_to_start(
        self, mock_handlers, mock_callback_update, mock_context, mocker
    ):
        """Test theory prev when going back from first section."""
        mock_callback_update.callback_query.data = "theory_prev_1"

        # Mock lesson
        mock_lesson = mocker.Mock()
        mock_lesson.title = "Test Lesson"
        mock_handlers.learning_orchestrator.lesson_repo.find_by_id.return_value = mock_lesson

        # Mock session context with theory_section = 0 (first section)
        session_context = {"theory_section": 0}
        mock_handlers.learning_orchestrator.get_session_context.return_value = session_context

        # Mock callback operations
        mock_callback_update.callback_query.answer = mocker.AsyncMock()
        mock_callback_update.callback_query.edit_message_text = mocker.AsyncMock()

        await mock_handlers.theory_prev_callback(mock_callback_update, mock_context)

        # Verify lesson start is shown
        mock_callback_update.callback_query.edit_message_text.assert_called_once()
        call_args = mock_callback_update.callback_query.edit_message_text.call_args
        assert "Test Lesson" in call_args[0][0]
        assert "Let's begin" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_theory_prev_callback_invalid_section(
        self, mock_handlers, mock_callback_update, mock_context, mocker
    ):
        """Test theory prev with invalid section."""
        mock_callback_update.callback_query.data = "theory_prev_1"

        # Mock lesson
        mock_lesson = mocker.Mock()
        mock_lesson.theory_content = {"sections": [{"content": "Section 1"}]}
        mock_handlers.learning_orchestrator.lesson_repo.find_by_id.return_value = mock_lesson

        # Mock session context with invalid theory_section
        session_context = {"theory_section": 5}  # Beyond available sections
        mock_handlers.learning_orchestrator.get_session_context.return_value = session_context

        # Mock callback operations
        mock_callback_update.callback_query.answer = mocker.AsyncMock()
        mock_callback_update.callback_query.edit_message_text = mocker.AsyncMock()

        await mock_handlers.theory_prev_callback(mock_callback_update, mock_context)

        # Verify error message shown
        mock_callback_update.callback_query.edit_message_text.assert_called_once()
        call_args = mock_callback_update.callback_query.edit_message_text.call_args
        assert "Invalid section" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_examples_callback_lesson_not_found(
        self, mock_handlers, mock_callback_update, mock_context, mocker
    ):
        """Test examples callback when lesson not found."""
        mock_callback_update.callback_query.data = "examples_1"

        # Mock lesson not found
        mock_handlers.learning_orchestrator.lesson_repo.find_by_id.return_value = None

        # Mock callback operations
        mock_callback_update.callback_query.answer = mocker.AsyncMock()
        mock_callback_update.callback_query.edit_message_text = mocker.AsyncMock()

        await mock_handlers.examples_callback(mock_callback_update, mock_context)

        # Verify error message shown
        mock_callback_update.callback_query.edit_message_text.assert_called_once()
        call_args = mock_callback_update.callback_query.edit_message_text.call_args
        assert "Lesson not found" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_examples_callback_no_comparisons(
        self, mock_handlers, mock_callback_update, mock_context, mocker
    ):
        """Test examples callback when no comparisons available."""
        mock_callback_update.callback_query.data = "examples_1"

        # Mock lesson with empty comparisons
        mock_lesson = mocker.Mock()
        mock_lesson.examples = {"comparisons": []}
        mock_handlers.learning_orchestrator.lesson_repo.find_by_id.return_value = mock_lesson

        # Mock callback operations
        mock_callback_update.callback_query.answer = mocker.AsyncMock()
        mock_callback_update.callback_query.edit_message_text = mocker.AsyncMock()

        await mock_handlers.examples_callback(mock_callback_update, mock_context)

        # Verify skip to practice message
        mock_callback_update.callback_query.edit_message_text.assert_called_once()
        call_args = mock_callback_update.callback_query.edit_message_text.call_args
        assert "No examples available" in call_args[0][0]
        assert "Moving to practice" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_lesson_complete_callback_user_not_found(
        self, mock_handlers, mock_callback_update, mock_context, mocker
    ):
        """Test lesson completion when user not found."""
        mock_callback_update.callback_query.data = "lesson_complete_1"

        # Mock user not found
        mock_handlers.learning_orchestrator.user_repo.find_by_telegram_id.return_value = None

        # Mock callback operations
        mock_callback_update.callback_query.answer = mocker.AsyncMock()
        mock_callback_update.callback_query.edit_message_text = mocker.AsyncMock()

        await mock_handlers.lesson_complete_callback(mock_callback_update, mock_context)

        # Verify error message shown
        mock_callback_update.callback_query.edit_message_text.assert_called_once()
        call_args = mock_callback_update.callback_query.edit_message_text.call_args
        assert "User not found" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_lesson_complete_callback_lesson_not_found(
        self, mock_handlers, mock_callback_update, mock_context, mocker
    ):
        """Test lesson completion when lesson not found."""
        mock_callback_update.callback_query.data = "lesson_complete_1"

        # Mock user found
        mock_user = mocker.Mock()
        mock_handlers.learning_orchestrator.user_repo.find_by_telegram_id.return_value = mock_user

        # Mock lesson not found
        mock_handlers.learning_orchestrator.lesson_repo.find_by_id.return_value = None

        # Mock callback operations
        mock_callback_update.callback_query.answer = mocker.AsyncMock()
        mock_callback_update.callback_query.edit_message_text = mocker.AsyncMock()

        await mock_handlers.lesson_complete_callback(mock_callback_update, mock_context)

        # Verify error message shown
        mock_callback_update.callback_query.edit_message_text.assert_called_once()
        call_args = mock_callback_update.callback_query.edit_message_text.call_args
        assert "Lesson not found" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_examples_callback(
        self, mock_handlers, mock_callback_update, mock_context, mocker
    ):
        """Test examples callback."""
        mock_callback_update.callback_query.data = "examples_1"

        # Mock lesson with examples
        mock_lesson = mocker.Mock()
        mock_lesson.examples = {
            "comparisons": [
                {
                    "bad": "Bad example",
                    "bad_reason": "Too vague",
                    "good": "Good example",
                    "good_reason": "Clear and specific",
                }
            ]
        }
        mock_handlers.learning_orchestrator.lesson_repo.find_by_id.return_value = mock_lesson

        # Mock callback operations
        mock_callback_update.callback_query.answer = mocker.AsyncMock()
        mock_callback_update.callback_query.edit_message_text = mocker.AsyncMock()

        await mock_handlers.examples_callback(mock_callback_update, mock_context)

        # Verify examples shown
        mock_callback_update.callback_query.edit_message_text.assert_called_once()
        call_args = mock_callback_update.callback_query.edit_message_text.call_args
        assert "Examples" in call_args[0][0]
        assert "Bad example" in call_args[0][0]
        assert "Good example" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_lesson_complete_callback(
        self, mock_handlers, mock_callback_update, mock_context, mocker
    ):
        """Test lesson completion callback."""
        mock_callback_update.callback_query.data = "lesson_complete_1"

        # Mock user and current lesson
        mock_user = mocker.Mock()
        mock_handlers.learning_orchestrator.user_repo.find_by_telegram_id.return_value = mock_user

        mock_current_lesson = mocker.Mock()
        mock_current_lesson.title = "Completed Lesson"
        mock_current_lesson.skill_level = SkillLevel.BEGINNER
        mock_current_lesson.order_index = 1
        mock_handlers.learning_orchestrator.lesson_repo.find_by_id.return_value = (
            mock_current_lesson
        )

        # Mock next lesson
        mock_next_lesson = mocker.Mock()
        mock_next_lesson.title = "Next Lesson"
        mock_next_lesson.id = 2
        mock_handlers.learning_orchestrator.lesson_repo.find_next_lesson.return_value = (
            mock_next_lesson
        )

        # Mock callback operations
        mock_callback_update.callback_query.answer = mocker.AsyncMock()
        mock_callback_update.callback_query.edit_message_text = mocker.AsyncMock()

        await mock_handlers.lesson_complete_callback(mock_callback_update, mock_context)

        # Verify next lesson shown
        mock_callback_update.callback_query.edit_message_text.assert_called_once()
        call_args = mock_callback_update.callback_query.edit_message_text.call_args
        assert "Lesson Complete" in call_args[0][0]
        assert "Completed Lesson" in call_args[0][0]
        assert "Next Lesson" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_lesson_complete_callback_last_lesson(
        self, mock_handlers, mock_callback_update, mock_context, mocker
    ):
        """Test lesson completion when it's the last lesson."""
        mock_callback_update.callback_query.data = "lesson_complete_1"

        # Mock user and current lesson
        mock_user = mocker.Mock()
        mock_handlers.learning_orchestrator.user_repo.find_by_telegram_id.return_value = mock_user

        mock_current_lesson = mocker.Mock()
        mock_current_lesson.title = "Last Lesson"
        mock_current_lesson.skill_level = SkillLevel.BEGINNER
        mock_current_lesson.order_index = 5
        mock_handlers.learning_orchestrator.lesson_repo.find_by_id.return_value = (
            mock_current_lesson
        )

        # Mock no next lesson
        mock_handlers.learning_orchestrator.lesson_repo.find_next_lesson.return_value = None

        # Mock callback operations
        mock_callback_update.callback_query.answer = mocker.AsyncMock()
        mock_callback_update.callback_query.edit_message_text = mocker.AsyncMock()

        await mock_handlers.lesson_complete_callback(mock_callback_update, mock_context)

        # Verify completion message for last lesson
        mock_callback_update.callback_query.edit_message_text.assert_called_once()
        call_args = mock_callback_update.callback_query.edit_message_text.call_args
        assert "Congratulations" in call_args[0][0]
        assert "Last Lesson" in call_args[0][0]
        assert "all lessons" in call_args[0][0].lower()
