"""Unit tests for practice handlers."""

import pytest
from telegram import Update
from telegram.ext import ContextTypes

from promptheus.bot.base_handlers import BaseBotHandlers
from promptheus.bot.practice_handlers import PracticeHandlersMixin


class MockPracticeHandlers(BaseBotHandlers, PracticeHandlersMixin):
    """Mock handlers class for testing."""


class TestPracticeHandlers:
    """Tests for PracticeHandlersMixin."""

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
        learning_orchestrator.user_repo = mocker.Mock()
        learning_orchestrator.user_repo.find_by_telegram_id = mocker.AsyncMock()
        learning_orchestrator.lesson_repo = mocker.Mock()
        learning_orchestrator.lesson_repo.find_by_id = mocker.AsyncMock()
        learning_orchestrator.lesson_repo.find_next_lesson = mocker.AsyncMock()
        assessment_engine.evaluate_user_prompt = mocker.AsyncMock()
        progress_tracker.increment_attempts = mocker.AsyncMock()
        progress_tracker.complete_lesson = mocker.AsyncMock()

        return MockPracticeHandlers(
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
        update.callback_query.data = "practice_1"
        return update

    @pytest.fixture
    def mock_text_update(self, mocker):
        """Create mock Update object with text message."""
        update = mocker.Mock(spec=Update)
        update.effective_user = mocker.Mock()
        update.effective_user.id = 12345
        update.message = mocker.Mock()
        update.message.text = "Test user prompt"
        update.callback_query = None
        return update

    @pytest.fixture
    def mock_context(self, mocker):
        """Create mock ContextTypes object."""
        return mocker.Mock(spec=ContextTypes.DEFAULT_TYPE)

    @pytest.mark.asyncio
    async def test_practice_callback(
        self, mock_handlers, mock_callback_update, mock_context, mocker
    ):
        """Test practice section callback."""
        # Mock lesson with exercises
        mock_lesson = mocker.Mock()
        mock_lesson.exercises = {
            "scenarios": [{"scenario": "Test scenario", "task": "Write a prompt"}]
        }
        mock_handlers.learning_orchestrator.lesson_repo.find_by_id.return_value = mock_lesson

        # Mock session operations
        mock_handlers.learning_orchestrator.get_session_context = mocker.AsyncMock(return_value={})
        mock_handlers.learning_orchestrator.save_session_context = mocker.AsyncMock()

        # Mock callback operations
        mock_callback_update.callback_query.answer = mocker.AsyncMock()
        mock_callback_update.callback_query.edit_message_text = mocker.AsyncMock()

        await mock_handlers.practice_callback(mock_callback_update, mock_context)

        # Verify session updated for practice
        expected_context = {"current_lesson_id": 1, "lesson_step": "practice"}
        mock_handlers.learning_orchestrator.save_session_context.assert_called_with(
            12345, expected_context
        )

        # Verify practice exercise shown
        mock_callback_update.callback_query.edit_message_text.assert_called_once()
        call_args = mock_callback_update.callback_query.edit_message_text.call_args
        assert "Practice Exercise" in call_args[0][0]
        assert "Test scenario" in call_args[0][0]
        assert "Write a prompt" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_practice_callback_no_exercises(
        self, mock_handlers, mock_callback_update, mock_context, mocker
    ):
        """Test practice callback when no exercises available."""
        # Mock lesson without exercises
        mock_lesson = mocker.Mock()
        mock_lesson.exercises = {"scenarios": []}
        mock_handlers.learning_orchestrator.lesson_repo.find_by_id.return_value = mock_lesson

        # Mock callback operations
        mock_callback_update.callback_query.answer = mocker.AsyncMock()
        mock_callback_update.callback_query.edit_message_text = mocker.AsyncMock()

        await mock_handlers.practice_callback(mock_callback_update, mock_context)

        # Verify lesson complete message
        mock_callback_update.callback_query.edit_message_text.assert_called_once()
        call_args = mock_callback_update.callback_query.edit_message_text.call_args
        assert "Lesson Complete" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_hint_callback(self, mock_handlers, mock_callback_update, mock_context, mocker):
        """Test hint request callback."""
        # Mock lesson with examples
        mock_lesson = mocker.Mock()
        mock_lesson.examples = {
            "comparisons": [{"good": "Good example prompt", "good_reason": "Clear and specific"}]
        }
        mock_handlers.learning_orchestrator.lesson_repo.find_by_id.return_value = mock_lesson

        # Mock callback operations
        mock_callback_update.callback_query.answer = mocker.AsyncMock()
        mock_callback_update.callback_query.edit_message_text = mocker.AsyncMock()

        await mock_handlers.hint_callback(mock_callback_update, mock_context)

        # Verify hint shown
        mock_callback_update.callback_query.edit_message_text.assert_called_once()
        call_args = mock_callback_update.callback_query.edit_message_text.call_args
        assert "Hint" in call_args[0][0]
        assert "Good example prompt" in call_args[0][0]
        assert "Clear and specific" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_skip_callback(self, mock_handlers, mock_callback_update, mock_context, mocker):
        """Test skip exercise callback."""
        # Mock user and current lesson
        mock_user = mocker.Mock()
        mock_handlers.learning_orchestrator.user_repo.find_by_telegram_id.return_value = mock_user

        mock_current_lesson = mocker.Mock()
        mock_current_lesson.skill_level = mocker.Mock()
        mock_current_lesson.order_index = 1
        mock_handlers.learning_orchestrator.lesson_repo.find_by_id.return_value = (
            mock_current_lesson
        )

        # Mock next lesson exists
        mock_next_lesson = mocker.Mock()
        mock_next_lesson.title = "Next Lesson"
        mock_next_lesson.id = 2
        mock_handlers.learning_orchestrator.lesson_repo.find_next_lesson.return_value = (
            mock_next_lesson
        )

        # Mock callback operations
        mock_callback_update.callback_query.answer = mocker.AsyncMock()
        mock_callback_update.callback_query.edit_message_text = mocker.AsyncMock()

        await mock_handlers.skip_callback(mock_callback_update, mock_context)

        # Verify skip message shown with next lesson option
        mock_callback_update.callback_query.edit_message_text.assert_called_once()
        call_args = mock_callback_update.callback_query.edit_message_text.call_args
        assert "Exercise Skipped" in call_args[0][0]
        assert "Next Lesson" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_skip_callback_last_lesson(
        self, mock_handlers, mock_callback_update, mock_context, mocker
    ):
        """Test skip callback when it's the last lesson."""
        # Mock user and current lesson
        mock_user = mocker.Mock()
        mock_handlers.learning_orchestrator.user_repo.find_by_telegram_id.return_value = mock_user

        mock_current_lesson = mocker.Mock()
        mock_current_lesson.skill_level = mocker.Mock()
        mock_current_lesson.order_index = 5
        mock_handlers.learning_orchestrator.lesson_repo.find_by_id.return_value = (
            mock_current_lesson
        )

        # Mock no next lesson
        mock_handlers.learning_orchestrator.lesson_repo.find_next_lesson.return_value = None

        # Mock callback operations
        mock_callback_update.callback_query.answer = mocker.AsyncMock()
        mock_callback_update.callback_query.edit_message_text = mocker.AsyncMock()

        await mock_handlers.skip_callback(mock_callback_update, mock_context)

        # Verify skip message for last lesson
        mock_callback_update.callback_query.edit_message_text.assert_called_once()
        call_args = mock_callback_update.callback_query.edit_message_text.call_args
        assert "Exercise Skipped" in call_args[0][0]
        assert "try the exercise again" in call_args[0][0].lower()

    @pytest.mark.asyncio
    async def test_text_message_handler_practice_mode(
        self, mock_handlers, mock_text_update, mock_context, mocker
    ):
        """Test text message handler in practice mode."""
        user_prompt = "Test user prompt"

        # Mock session context for practice
        session_context = {"lesson_step": "practice", "current_lesson_id": 1}
        mock_handlers.learning_orchestrator.get_session_context = mocker.AsyncMock(
            return_value=session_context
        )

        # Mock AI evaluation
        feedback = {
            "score": 8,
            "strengths": ["Clear structure"],
            "improvements": ["Add more context"],
        }
        mock_handlers.assessment_engine.evaluate_user_prompt = mocker.AsyncMock(
            return_value=feedback
        )

        # Mock progress tracking
        mock_handlers.progress_tracker.increment_attempts = mocker.AsyncMock()
        mock_handlers.progress_tracker.complete_lesson = mocker.AsyncMock()

        # Mock message operations
        mock_text_update.message.reply_text = mocker.AsyncMock()
        loading_msg = mocker.Mock()
        loading_msg.edit_text = mocker.AsyncMock()
        mock_text_update.message.reply_text.return_value = loading_msg

        await mock_handlers.text_message_handler(mock_text_update, mock_context)

        # Verify AI evaluation called
        mock_handlers.assessment_engine.evaluate_user_prompt.assert_called_once_with(user_prompt, 1)

        # Verify progress incremented
        mock_handlers.progress_tracker.increment_attempts.assert_called_once_with(12345, 1)

        # Verify lesson completed (score >= 7)
        mock_handlers.progress_tracker.complete_lesson.assert_called_once_with(12345, 1, 8)

        # Verify feedback sent
        assert mock_text_update.message.reply_text.call_count == 1  # Only loading message
        loading_msg.edit_text.assert_called_once()
        call_args = loading_msg.edit_text.call_args
        assert "*Score:* 8/10" in call_args[0][0]
        assert "Clear structure" in call_args[0][0]

        # Verify keyboard is present with lesson complete button
        reply_markup = call_args[1]["reply_markup"]
        assert reply_markup is not None
        keyboard = reply_markup.inline_keyboard
        assert len(keyboard) == 2  # Two rows
        assert "Lesson Complete" in keyboard[0][0].text
        assert keyboard[0][0].callback_data == "lesson_complete_1"
        assert "Menu" in keyboard[1][0].text

    @pytest.mark.asyncio
    async def test_text_message_handler_not_practice_mode(
        self, mock_handlers, mock_text_update, mock_context, mocker
    ):
        """Test text message handler when not in practice mode."""
        # Mock session context not in practice
        session_context = {"lesson_step": "theory"}
        mock_handlers.learning_orchestrator.get_session_context = mocker.AsyncMock(
            return_value=session_context
        )

        # Mock message operations
        mock_text_update.message.reply_text = mocker.AsyncMock()

        await mock_handlers.text_message_handler(mock_text_update, mock_context)

        # Verify helpful message sent
        mock_text_update.message.reply_text.assert_called_once()
        call_args = mock_text_update.message.reply_text.call_args
        assert "/menu" in call_args[0][0] or "/start" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_text_message_handler_no_lesson_id(
        self, mock_handlers, mock_text_update, mock_context, mocker
    ):
        """Test text message handler when no current lesson ID."""
        # Mock session context without lesson_id
        session_context = {"lesson_step": "practice"}
        mock_handlers.learning_orchestrator.get_session_context = mocker.AsyncMock(
            return_value=session_context
        )

        # Mock message operations
        mock_text_update.message.reply_text = mocker.AsyncMock()

        await mock_handlers.text_message_handler(mock_text_update, mock_context)

        # Verify error message sent
        mock_text_update.message.reply_text.assert_called_once()
        call_args = mock_text_update.message.reply_text.call_args
        assert "start a lesson first" in call_args[0][0].lower()

    @pytest.mark.asyncio
    async def test_text_message_handler_evaluation_error(
        self, mock_handlers, mock_text_update, mock_context, mocker
    ):
        """Test text message handler when AI evaluation fails."""
        # Mock session context
        session_context = {"lesson_step": "practice", "current_lesson_id": 1}
        mock_handlers.learning_orchestrator.get_session_context = mocker.AsyncMock(
            return_value=session_context
        )

        # Mock AI evaluation failure
        mock_handlers.assessment_engine.evaluate_user_prompt = mocker.AsyncMock(
            side_effect=Exception("AI Error")
        )

        # Mock message operations
        mock_text_update.message.reply_text = mocker.AsyncMock()
        loading_msg = mocker.Mock()
        loading_msg.edit_text = mocker.AsyncMock()
        mock_text_update.message.reply_text.return_value = loading_msg

        await mock_handlers.text_message_handler(mock_text_update, mock_context)

        # Verify error message sent
        loading_msg.edit_text.assert_called_once()
        call_args = loading_msg.edit_text.call_args
        assert "error" in call_args[0][0].lower()

    @pytest.mark.asyncio
    async def test_text_message_handler_low_score(
        self, mock_handlers, mock_text_update, mock_context, mocker
    ):
        """Test text message handler with low score (no completion)."""
        # Mock session context
        session_context = {"lesson_step": "practice", "current_lesson_id": 1}
        mock_handlers.learning_orchestrator.get_session_context = mocker.AsyncMock(
            return_value=session_context
        )

        # Mock AI evaluation with low score
        feedback = {"score": 5, "strengths": [], "improvements": ["Add more details"]}
        mock_handlers.assessment_engine.evaluate_user_prompt = mocker.AsyncMock(
            return_value=feedback
        )

        # Mock progress tracking
        mock_handlers.progress_tracker.increment_attempts = mocker.AsyncMock()

        # Mock message operations
        mock_text_update.message.reply_text = mocker.AsyncMock()
        loading_msg = mocker.Mock()
        loading_msg.edit_text = mocker.AsyncMock()
        mock_text_update.message.reply_text.return_value = loading_msg

        await mock_handlers.text_message_handler(mock_text_update, mock_context)

        # Verify progress incremented but lesson not completed
        mock_handlers.progress_tracker.increment_attempts.assert_called_once_with(12345, 1)
        mock_handlers.progress_tracker.complete_lesson.assert_not_called()

        # Verify feedback with try again option
        assert mock_text_update.message.reply_text.call_count == 1  # Only loading message
        loading_msg.edit_text.assert_called_once()
        call_args = loading_msg.edit_text.call_args
        assert "*Score:* 5/10" in call_args[0][0]
        assert "Add more details" in call_args[0][0]

        # Verify keyboard is present with try again button
        reply_markup = call_args[1]["reply_markup"]
        assert reply_markup is not None
        keyboard = reply_markup.inline_keyboard
        assert len(keyboard) == 2  # Two rows
        assert "Try Again" in keyboard[0][0].text
        assert keyboard[0][0].callback_data == "practice_1"
        assert "Menu" in keyboard[1][0].text
