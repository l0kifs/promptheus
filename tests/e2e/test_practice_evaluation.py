"""E2E tests for practice evaluation flow."""

import pytest
from telegram import Update

from promptheus.data.models import SkillLevel


class TestPracticeEvaluationE2E:
    """E2E tests for prompt evaluation during practice."""

    @pytest.fixture
    async def bot_handlers(self, dependency_container):
        """Get bot handlers from dependency container."""
        return await dependency_container.get_bot_handlers()

    @pytest.fixture
    def practice_user_update(self, mock_update_factory):
        """Create update for user in practice mode."""
        return mock_update_factory(
            update_type="callback_query",
            user_id=12345,
            username="testuser",
            callback_data="practice_1",
        )

    @pytest.fixture
    def practice_user_context(self, mock_context_factory):
        """Create context for user in practice."""
        return mock_context_factory()

    @pytest.mark.asyncio
    async def test_successful_prompt_evaluation(
        self, bot_handlers, practice_user_update, practice_user_context, mocker
    ):
        """Test successful prompt submission and evaluation."""
        # Mock all dependencies
        mock_user_repo = mocker.AsyncMock()
        mock_session_repo = mocker.AsyncMock()
        mock_lesson_repo = mocker.AsyncMock()
        mock_progress_repo = mocker.AsyncMock()

        bot_handlers.learning_orchestrator.user_repo = mock_user_repo
        bot_handlers.learning_orchestrator.session_repo = mock_session_repo
        bot_handlers.learning_orchestrator.lesson_repo = mock_lesson_repo
        bot_handlers.progress_tracker.progress_repo = mock_progress_repo

        # Mock existing user
        mock_user = type("MockUser", (), {"skill_level": SkillLevel.BEGINNER})()
        mock_user_repo.find_by_telegram_id.return_value = mock_user

        # Mock lesson with exercises
        mock_lesson = type(
            "MockLesson",
            (),
            {
                "id": 1,
                "title": "Introduction to Prompt Engineering",
                "skill_level": "beginner",
                "order_index": 1,
                "exercises": {
                    "scenarios": [
                        {
                            "scenario": "You need to generate Python code for data analysis",
                            "task": "Write a prompt asking AI to create a function that processes CSV data",
                        }
                    ]
                },
            },
        )()

        mock_lesson_repo.find_by_id.return_value = mock_lesson

        # Mock session context
        bot_handlers.learning_orchestrator.get_session_context = mocker.AsyncMock(
            return_value={"current_lesson_id": 1, "lesson_step": "practice"}
        )
        bot_handlers.learning_orchestrator.save_session_context = mocker.AsyncMock()

        # Mock AI evaluation
        bot_handlers.assessment_engine.evaluate_user_prompt = mocker.AsyncMock(
            return_value={
                "score": 9,
                "strengths": ["Excellent task specificity", "Clear context provided"],
                "improvements": ["Consider adding output format requirements"],
            }
        )

        # Mock progress tracker methods
        bot_handlers.progress_tracker.increment_attempts = mocker.AsyncMock()
        bot_handlers.progress_tracker.complete_lesson = mocker.AsyncMock()
        bot_handlers.progress_tracker.record_attempt = mocker.AsyncMock()

        # Step 1: Start practice
        await bot_handlers.practice_callback(practice_user_update, practice_user_context)

        # Verify practice exercise shown
        practice_user_update.callback_query.edit_message_text.assert_called_once()
        practice_call_args = practice_user_update.callback_query.edit_message_text.call_args
        assert "Practice Exercise" in practice_call_args[0][0]
        assert "generate Python code" in practice_call_args[0][0]
        assert "Send your prompt" in practice_call_args[0][0]

        # Step 2: Submit prompt
        prompt_update = mocker.Mock(spec=Update)
        prompt_update.effective_user = practice_user_update.effective_user
        prompt_update.message = mocker.Mock()
        prompt_update.message.text = "Create a Python function that reads a CSV file and calculates statistics for numerical columns"
        prompt_update.message.reply_text = mocker.AsyncMock()

        # Mock the loading message returned by reply_text
        loading_msg = mocker.AsyncMock()
        prompt_update.message.reply_text.return_value = loading_msg

        await bot_handlers.text_message_handler(prompt_update, practice_user_context)

        # Verify loading message was sent
        prompt_update.message.reply_text.assert_called_once()
        loading_call_args = prompt_update.message.reply_text.call_args
        assert "Analyzing your prompt" in loading_call_args[0][0]

        # Verify evaluation response was shown by editing the loading message
        loading_msg.edit_text.assert_called_once()
        eval_call_args = loading_msg.edit_text.call_args
        response_text = eval_call_args[0][0]

        assert "9" in response_text  # Score
        assert "Excellent task specificity" in response_text  # Strengths
        assert "output format requirements" in response_text  # Improvements

    @pytest.mark.asyncio
    async def test_prompt_evaluation_with_hint(
        self, bot_handlers, practice_user_update, practice_user_context, mocker
    ):
        """Test prompt evaluation flow with hint usage."""
        # Mock dependencies
        mock_lesson_repo = mocker.AsyncMock()
        bot_handlers.learning_orchestrator.lesson_repo = mock_lesson_repo

        # Mock lesson with examples for hints
        mock_lesson = type(
            "MockLesson",
            (),
            {
                "id": 1,
                "examples": {
                    "comparisons": [
                        {
                            "good": "Write a comprehensive Python function with error handling",
                            "good_reason": "Provides clear requirements and constraints",
                            "bad": "Write code",
                            "bad_reason": "Too vague and lacks specifics",
                        }
                    ]
                },
            },
        )()

        mock_lesson_repo.find_by_id.return_value = mock_lesson

        # Step 1: Request hint
        hint_update = mocker.Mock(spec=Update)
        hint_update.effective_user = practice_user_update.effective_user
        hint_update.callback_query = mocker.Mock()
        hint_update.callback_query.data = "hint_1"
        hint_update.callback_query.answer = mocker.AsyncMock()
        hint_update.callback_query.edit_message_text = mocker.AsyncMock()

        await bot_handlers.hint_callback(hint_update, practice_user_context)

        # Verify hint shown
        hint_update.callback_query.edit_message_text.assert_called_once()
        hint_call_args = hint_update.callback_query.edit_message_text.call_args
        assert "Hint" in hint_call_args[0][0]
        assert "comprehensive Python function" in hint_call_args[0][0]
        assert "Provides clear requirements" in hint_call_args[0][0]

    @pytest.mark.asyncio
    async def test_prompt_evaluation_skip_exercise(
        self, bot_handlers, practice_user_update, practice_user_context, mocker
    ):
        """Test skipping practice exercise."""
        # Mock dependencies
        mock_user_repo = mocker.AsyncMock()
        mock_lesson_repo = mocker.AsyncMock()
        mock_progress_repo = mocker.AsyncMock()
        bot_handlers.learning_orchestrator.user_repo = mock_user_repo
        bot_handlers.learning_orchestrator.lesson_repo = mock_lesson_repo
        bot_handlers.progress_tracker.progress_repo = mock_progress_repo

        # Mock user
        mock_user = type("MockUser", (), {"skill_level": SkillLevel.BEGINNER})()
        mock_user_repo.find_by_telegram_id.return_value = mock_user

        # Mock lesson
        mock_lesson = type(
            "MockLesson", (), {"id": 1, "skill_level": "beginner", "order_index": 1}
        )()
        mock_lesson_repo.find_by_id.return_value = mock_lesson
        mock_lesson_repo.find_next_lesson.return_value = None  # No next lesson

        # Mock progress tracking
        mock_progress = type("MockProgress", (), {"attempts": 0})()
        mock_progress_repo.find_by_user_and_lesson.return_value = mock_progress

        # Step 1: Skip exercise
        skip_update = mocker.Mock(spec=Update)
        skip_update.effective_user = practice_user_update.effective_user
        skip_update.callback_query = mocker.Mock()
        skip_update.callback_query.data = "skip_1"
        skip_update.callback_query.answer = mocker.AsyncMock()
        skip_update.callback_query.edit_message_text = mocker.AsyncMock()

        await bot_handlers.skip_callback(skip_update, practice_user_context)

        # Verify skip response
        skip_update.callback_query.edit_message_text.assert_called_once()
        skip_call_args = skip_update.callback_query.edit_message_text.call_args
        assert "skipped" in skip_call_args[0][0].lower() or "skip" in skip_call_args[0][0].lower()

        # Note: skip_callback doesn't increment attempts, only text_message_handler does

    @pytest.mark.asyncio
    async def test_prompt_evaluation_ai_error_fallback(
        self, bot_handlers, practice_user_update, practice_user_context, mocker
    ):
        """Test prompt evaluation with AI error fallback."""
        # Mock dependencies
        mock_user_repo = mocker.AsyncMock()
        mock_session_repo = mocker.AsyncMock()
        mock_lesson_repo = mocker.AsyncMock()

        bot_handlers.learning_orchestrator.user_repo = mock_user_repo
        bot_handlers.learning_orchestrator.session_repo = mock_session_repo
        bot_handlers.learning_orchestrator.lesson_repo = mock_lesson_repo

        # Mock existing user
        mock_user = type("MockUser", (), {"skill_level": SkillLevel.BEGINNER})()
        mock_user_repo.find_by_telegram_id.return_value = mock_user

        # Mock lesson
        mock_lesson = type(
            "MockLesson",
            (),
            {
                "id": 1,
                "exercises": {"scenarios": [{"scenario": "Test scenario", "task": "Test task"}]},
            },
        )()
        mock_lesson_repo.find_by_id.return_value = mock_lesson

        # Mock session
        bot_handlers.learning_orchestrator.get_session_context = mocker.AsyncMock(
            return_value={"current_lesson_id": 1, "lesson_step": "practice"}
        )
        bot_handlers.learning_orchestrator.save_session_context = mocker.AsyncMock()

        # Mock AI evaluation to raise exception
        bot_handlers.assessment_engine.evaluate_user_prompt = mocker.AsyncMock(
            side_effect=Exception("AI service unavailable")
        )

        # Step 1: Submit prompt (will trigger fallback)
        prompt_update = mocker.Mock(spec=Update)
        prompt_update.effective_user = practice_user_update.effective_user
        prompt_update.message = mocker.Mock()
        prompt_update.message.text = "Test prompt"
        prompt_update.message.reply_text = mocker.AsyncMock()

        # Mock the loading message returned by reply_text
        loading_msg = mocker.AsyncMock()
        prompt_update.message.reply_text.return_value = loading_msg

        await bot_handlers.text_message_handler(prompt_update, practice_user_context)

        # Verify loading message was sent
        prompt_update.message.reply_text.assert_called_once()
        loading_call_args = prompt_update.message.reply_text.call_args
        assert "Analyzing your prompt" in loading_call_args[0][0]

        # Verify error message was shown by editing the loading message
        loading_msg.edit_text.assert_called_once()
        error_call_args = loading_msg.edit_text.call_args
        error_text = error_call_args[0][0]
        assert "error evaluating your prompt" in error_text.lower()
