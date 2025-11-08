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
        progress_tracker.record_attempt = mocker.AsyncMock()
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

        # Mock chat for typing indicator
        mock_chat = mocker.Mock()
        mock_chat.send_action = mocker.AsyncMock()
        mock_text_update.message.chat = mock_chat

        await mock_handlers.text_message_handler(mock_text_update, mock_context)

        # Verify AI evaluation called
        mock_handlers.assessment_engine.evaluate_user_prompt.assert_called_once_with(user_prompt, 1)

        # Verify progress incremented
        mock_handlers.progress_tracker.increment_attempts.assert_called_once_with(12345, 1)

        # Verify lesson completed (score >= 7)
        mock_handlers.progress_tracker.complete_lesson.assert_called_once_with(12345, 1, 8)

        # Verify typing indicator was sent
        mock_chat.send_action.assert_called_once()

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
        assert "Back to Examples" in keyboard[1][0].text

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

        # Mock chat for typing indicator
        mock_chat = mocker.Mock()
        mock_chat.send_action = mocker.AsyncMock()
        mock_text_update.message.chat = mock_chat

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

        # Mock chat for typing indicator
        mock_chat = mocker.Mock()
        mock_chat.send_action = mocker.AsyncMock()
        mock_text_update.message.chat = mock_chat

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
        assert "Back to Examples" in keyboard[1][0].text

    # =====================================================================
    # REGRESSION TESTS FOR SCORE SAVING BUG FIX
    # Bug: Scores below 7 were not being saved to database
    # Fix: Added record_attempt() call for ALL scores before completion check
    # =====================================================================

    @pytest.mark.asyncio
    async def test_score_saved_for_low_scores(
        self, mock_handlers, mock_text_update, mock_context, mocker
    ):
        """Test that scores below 7 are recorded in database.

        REGRESSION TEST: Previously, only scores >= 7 were saved because
        record_attempt() was never called for low scores. This test ensures
        ALL scores are now saved regardless of value.
        """
        # Mock session context
        session_context = {"lesson_step": "practice", "current_lesson_id": 1}
        mock_handlers.learning_orchestrator.get_session_context = mocker.AsyncMock(
            return_value=session_context
        )

        # Mock AI evaluation with low score (below completion threshold)
        feedback = {"score": 3, "strengths": [], "improvements": ["Be more specific"]}
        mock_handlers.assessment_engine.evaluate_user_prompt = mocker.AsyncMock(
            return_value=feedback
        )

        # Mock progress tracking
        mock_handlers.progress_tracker.increment_attempts = mocker.AsyncMock()
        mock_handlers.progress_tracker.record_attempt = mocker.AsyncMock()
        mock_handlers.progress_tracker.complete_lesson = mocker.AsyncMock()

        # Mock message operations
        mock_text_update.message.reply_text = mocker.AsyncMock()
        loading_msg = mocker.Mock()
        loading_msg.edit_text = mocker.AsyncMock()
        mock_text_update.message.reply_text.return_value = loading_msg

        # Mock chat for typing indicator
        mock_chat = mocker.Mock()
        mock_chat.send_action = mocker.AsyncMock()
        mock_text_update.message.chat = mock_chat

        await mock_handlers.text_message_handler(mock_text_update, mock_context)

        # CRITICAL: Verify record_attempt was called with the low score
        # This is the fix for the bug - scores must be saved regardless of value
        mock_handlers.progress_tracker.record_attempt.assert_called_once_with(12345, 1, 3)

        # Verify attempts incremented
        mock_handlers.progress_tracker.increment_attempts.assert_called_once_with(12345, 1)

        # Verify lesson NOT completed (score < 7)
        mock_handlers.progress_tracker.complete_lesson.assert_not_called()

    @pytest.mark.asyncio
    async def test_score_saved_for_high_scores(
        self, mock_handlers, mock_text_update, mock_context, mocker
    ):
        """Test that scores >= 7 are recorded AND lesson is completed.

        REGRESSION TEST: Verifies that high scores still trigger both
        record_attempt() AND complete_lesson() calls.
        """
        # Mock session context
        session_context = {"lesson_step": "practice", "current_lesson_id": 1}
        mock_handlers.learning_orchestrator.get_session_context = mocker.AsyncMock(
            return_value=session_context
        )

        # Mock AI evaluation with high score (above completion threshold)
        feedback = {"score": 9, "strengths": ["Excellent detail"], "improvements": []}
        mock_handlers.assessment_engine.evaluate_user_prompt = mocker.AsyncMock(
            return_value=feedback
        )

        # Mock progress tracking
        mock_handlers.progress_tracker.increment_attempts = mocker.AsyncMock()
        mock_handlers.progress_tracker.record_attempt = mocker.AsyncMock()
        mock_handlers.progress_tracker.complete_lesson = mocker.AsyncMock()

        # Mock message operations
        mock_text_update.message.reply_text = mocker.AsyncMock()
        loading_msg = mocker.Mock()
        loading_msg.edit_text = mocker.AsyncMock()
        mock_text_update.message.reply_text.return_value = loading_msg

        # Mock chat for typing indicator
        mock_chat = mocker.Mock()
        mock_chat.send_action = mocker.AsyncMock()
        mock_text_update.message.chat = mock_chat

        await mock_handlers.text_message_handler(mock_text_update, mock_context)

        # CRITICAL: Verify record_attempt was called FIRST with the score
        mock_handlers.progress_tracker.record_attempt.assert_called_once_with(12345, 1, 9)

        # Verify attempts incremented
        mock_handlers.progress_tracker.increment_attempts.assert_called_once_with(12345, 1)

        # Verify lesson completed (score >= 7)
        mock_handlers.progress_tracker.complete_lesson.assert_called_once_with(12345, 1, 9)

    @pytest.mark.asyncio
    async def test_score_saved_at_threshold(
        self, mock_handlers, mock_text_update, mock_context, mocker
    ):
        """Test that score exactly at threshold (7) is saved and completes lesson.

        REGRESSION TEST: Boundary test to ensure score of 7 triggers both
        record_attempt() and complete_lesson().
        """
        # Mock session context
        session_context = {"lesson_step": "practice", "current_lesson_id": 1}
        mock_handlers.learning_orchestrator.get_session_context = mocker.AsyncMock(
            return_value=session_context
        )

        # Mock AI evaluation with threshold score
        feedback = {"score": 7, "strengths": ["Good effort"], "improvements": ["Minor tweaks"]}
        mock_handlers.assessment_engine.evaluate_user_prompt = mocker.AsyncMock(
            return_value=feedback
        )

        # Mock progress tracking
        mock_handlers.progress_tracker.increment_attempts = mocker.AsyncMock()
        mock_handlers.progress_tracker.record_attempt = mocker.AsyncMock()
        mock_handlers.progress_tracker.complete_lesson = mocker.AsyncMock()

        # Mock message operations
        mock_text_update.message.reply_text = mocker.AsyncMock()
        loading_msg = mocker.Mock()
        loading_msg.edit_text = mocker.AsyncMock()
        mock_text_update.message.reply_text.return_value = loading_msg

        # Mock chat for typing indicator
        mock_chat = mocker.Mock()
        mock_chat.send_action = mocker.AsyncMock()
        mock_text_update.message.chat = mock_chat

        await mock_handlers.text_message_handler(mock_text_update, mock_context)

        # Verify record_attempt called with threshold score
        mock_handlers.progress_tracker.record_attempt.assert_called_once_with(12345, 1, 7)

        # Verify attempts incremented
        mock_handlers.progress_tracker.increment_attempts.assert_called_once_with(12345, 1)

        # Verify lesson completed (score == 7)
        mock_handlers.progress_tracker.complete_lesson.assert_called_once_with(12345, 1, 7)

    @pytest.mark.asyncio
    async def test_multiple_attempts_update_score(
        self, mock_handlers, mock_text_update, mock_context, mocker
    ):
        """Test that multiple attempts with different scores all get recorded.

        REGRESSION TEST: Simulates user making multiple attempts with varying
        scores (2, 6, 8) to ensure all are saved. This matches the real bug
        scenario where user had scores 2 and 8 but average showed 8.0.
        """
        # Mock session context
        session_context = {"lesson_step": "practice", "current_lesson_id": 1}
        mock_handlers.learning_orchestrator.get_session_context = mocker.AsyncMock(
            return_value=session_context
        )

        # Mock progress tracking
        mock_handlers.progress_tracker.increment_attempts = mocker.AsyncMock()
        mock_handlers.progress_tracker.record_attempt = mocker.AsyncMock()
        mock_handlers.progress_tracker.complete_lesson = mocker.AsyncMock()

        # Mock message operations
        mock_text_update.message.reply_text = mocker.AsyncMock()
        loading_msg = mocker.Mock()
        loading_msg.edit_text = mocker.AsyncMock()
        mock_text_update.message.reply_text.return_value = loading_msg

        # Mock chat for typing indicator
        mock_chat = mocker.Mock()
        mock_chat.send_action = mocker.AsyncMock()
        mock_text_update.message.chat = mock_chat

        # Simulate three attempts with different scores: 2, 6, 8
        scores = [2, 6, 8]
        for score in scores:
            # Mock AI evaluation for each attempt
            feedback = {
                "score": score,
                "strengths": [] if score < 7 else ["Good work"],
                "improvements": ["Improve"] if score < 7 else [],
            }
            mock_handlers.assessment_engine.evaluate_user_prompt = mocker.AsyncMock(
                return_value=feedback
            )

            # Reset mocks for each attempt
            mock_handlers.progress_tracker.record_attempt.reset_mock()
            mock_handlers.progress_tracker.increment_attempts.reset_mock()
            mock_handlers.progress_tracker.complete_lesson.reset_mock()

            await mock_handlers.text_message_handler(mock_text_update, mock_context)

            # CRITICAL: Verify record_attempt was called for EVERY score
            mock_handlers.progress_tracker.record_attempt.assert_called_once_with(12345, 1, score)

            # Verify attempts incremented
            mock_handlers.progress_tracker.increment_attempts.assert_called_once_with(12345, 1)

            # Verify complete_lesson only called when score >= 7
            if score >= 7:
                mock_handlers.progress_tracker.complete_lesson.assert_called_once_with(
                    12345, 1, score
                )
            else:
                mock_handlers.progress_tracker.complete_lesson.assert_not_called()
