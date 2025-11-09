"""E2E tests for complete lesson flow."""

import pytest
from telegram import Update


class TestLessonFlowE2E:
    """E2E tests for complete lesson learning flow."""

    @pytest.fixture
    async def bot_handlers(self, dependency_container):
        """Get bot handlers from dependency container."""
        return await dependency_container.get_bot_handlers()

    @pytest.fixture
    def existing_user_update(self, mock_update_factory):
        """Create update for existing user."""
        return mock_update_factory(
            update_type="callback_query",
            user_id=12345,
            username="testuser",
            callback_data="lesson_list",
        )

    @pytest.fixture
    def existing_user_context(self, mock_context_factory):
        """Create context for existing user."""
        return mock_context_factory()

    @pytest.mark.asyncio
    async def test_complete_lesson_flow(
        self, bot_handlers, existing_user_update, existing_user_context, mocker
    ):
        """Test complete lesson flow from selection to completion."""
        # Mock telegram components
        mock_keyboard = mocker.Mock()
        mocker.patch("telegram.InlineKeyboardMarkup", return_value=mock_keyboard)
        # Mock all dependencies
        mock_user_repo = mocker.AsyncMock()
        mock_session_repo = mocker.AsyncMock()
        mock_lesson_repo = mocker.AsyncMock()
        mock_progress_repo = mocker.AsyncMock()

        bot_handlers.learning_orchestrator.user_repo = mock_user_repo
        bot_handlers.learning_orchestrator.session_repo = mock_session_repo
        bot_handlers.learning_orchestrator.lesson_repo = mock_lesson_repo
        bot_handlers.progress_tracker.progress_repo = mock_progress_repo

        # Mock progress tracker methods
        bot_handlers.progress_tracker.start_lesson = mocker.AsyncMock()
        bot_handlers.progress_tracker.increment_attempts = mocker.AsyncMock()
        bot_handlers.progress_tracker.complete_lesson = mocker.AsyncMock()
        bot_handlers.progress_tracker.mark_in_progress = mocker.AsyncMock()
        bot_handlers.progress_tracker.record_attempt = mocker.AsyncMock()

        # Mock formatter chunking method
        mocker.patch.object(
            bot_handlers.formatter,
            "chunk_text_by_words",
            return_value=[
                "Prompt engineering is the art of crafting effective prompts for AI models...",
                "Because AI needs clear instructions to produce good results...",
            ],
        )

        # Mock learning orchestrator methods
        bot_handlers.learning_orchestrator.get_session_context = mocker.AsyncMock(
            return_value={"lesson_step": "practice", "current_lesson_id": 1}
        )
        bot_handlers.learning_orchestrator.save_session_context = mocker.AsyncMock()
        bot_handlers.learning_orchestrator.update_session_state = mocker.AsyncMock()

        # Mock existing user
        mock_user = type("MockUser", (), {"skill_level": "beginner"})()
        mock_user_repo.find_by_telegram_id.return_value = mock_user

        # Mock lesson data
        mock_lesson = type(
            "MockLesson",
            (),
            {
                "id": 1,
                "title": "Introduction to Prompt Engineering",
                "position": 1,
                "skill_level": "beginner",
                "theory_content": {
                    "sections": [
                        {
                            "title": "What is Prompt Engineering?",
                            "content": "Prompt engineering is the art of crafting effective prompts for AI models...",
                        },
                        {
                            "title": "Why it matters",
                            "content": "Because AI needs clear instructions to produce good results...",
                        },
                    ]
                },
                "examples": {
                    "comparisons": [
                        {
                            "good": "Write a Python function to calculate factorial",
                            "bad": "Code please",
                            "good_reason": "Clear, specific task",
                            "bad_reason": "Too vague",
                        }
                    ]
                },
                "exercises": {
                    "scenarios": [
                        {
                            "scenario": "You need to create a prompt for code generation",
                            "task": "Write a prompt that asks AI to create a Python function",
                        }
                    ]
                },
            },
        )()

        mock_lesson_repo.find_by_skill_level.return_value = [mock_lesson]
        mock_lesson_repo.find_by_id.return_value = mock_lesson
        mock_lesson_repo.find_next_lesson = mocker.AsyncMock(return_value=None)

        # Mock session and progress
        mock_session_repo.find_by_user_id.return_value = None
        mock_progress_repo.find_by_user_and_lesson.return_value = None
        mock_progress_repo.create = mocker.AsyncMock()
        mock_progress_repo.update_score = mocker.AsyncMock()

        # Mock AI evaluation for practice
        mock_assessment_engine = mocker.AsyncMock()
        mock_assessment_engine.evaluate_user_prompt.return_value = {
            "score": 8,
            "strengths": ["Clear task description", "Good structure"],
            "improvements": ["Add more context"],
        }
        bot_handlers.assessment_engine = mock_assessment_engine

        # Step 1: Show lesson list
        await bot_handlers.lesson_list_callback(existing_user_update, existing_user_context)

        # Verify lesson list shown
        existing_user_update.callback_query.edit_message_text.assert_called_once()
        list_call_args = existing_user_update.callback_query.edit_message_text.call_args
        assert "Introduction to Prompt Engineering" in list_call_args[0][0]
        assert "Lesson 1" in str(list_call_args[1]["reply_markup"])

        # Step 2: Select lesson
        lesson_select_update = mocker.Mock(spec=Update)
        lesson_select_update.effective_user = existing_user_update.effective_user
        lesson_select_update.callback_query = mocker.Mock()
        lesson_select_update.callback_query.data = "lesson_1"
        lesson_select_update.callback_query.answer = mocker.AsyncMock()
        lesson_select_update.callback_query.edit_message_text = mocker.AsyncMock()

        await bot_handlers.lesson_callback(lesson_select_update, existing_user_context)

        # Verify lesson start page
        lesson_select_update.callback_query.edit_message_text.assert_called_once()
        select_call_args = lesson_select_update.callback_query.edit_message_text.call_args
        assert "Introduction to Prompt Engineering" in select_call_args[0][0]
        assert "Start" in str(select_call_args[1]["reply_markup"])

        # Step 3: Start lesson (show theory)
        lesson_start_update = mocker.Mock(spec=Update)
        lesson_start_update.effective_user = existing_user_update.effective_user
        lesson_start_update.callback_query = mocker.Mock()
        lesson_start_update.callback_query.data = "lesson_start_1"
        lesson_start_update.callback_query.answer = mocker.AsyncMock()
        lesson_start_update.callback_query.edit_message_text = mocker.AsyncMock()

        await bot_handlers.lesson_start_callback(lesson_start_update, existing_user_context)

        # Verify theory section 1 shown
        lesson_start_update.callback_query.edit_message_text.assert_called_once()
        theory_call_args = lesson_start_update.callback_query.edit_message_text.call_args
        assert "Prompt engineering is the art of crafting" in theory_call_args[0][0]
        assert "Theory" in theory_call_args[0][0]
        assert "1/2" in theory_call_args[0][0]

        # Step 4: Navigate to next theory section
        theory_next_update = mocker.Mock(spec=Update)
        theory_next_update.effective_user = existing_user_update.effective_user
        theory_next_update.callback_query = mocker.Mock()
        theory_next_update.callback_query.data = "theory_next_1"
        theory_next_update.callback_query.answer = mocker.AsyncMock()
        theory_next_update.callback_query.edit_message_text = mocker.AsyncMock()

        await bot_handlers.theory_next_callback(theory_next_update, existing_user_context)

        # Verify theory section 2 shown
        theory_next_update.callback_query.edit_message_text.assert_called_once()
        next_call_args = theory_next_update.callback_query.edit_message_text.call_args
        assert "Because AI needs clear instructions" in next_call_args[0][0]
        assert "Examples" in str(next_call_args[1]["reply_markup"])

        # Step 5: Show examples
        examples_update = mocker.Mock(spec=Update)
        examples_update.effective_user = existing_user_update.effective_user
        examples_update.callback_query = mocker.Mock()
        examples_update.callback_query.data = "examples_1"
        examples_update.callback_query.answer = mocker.AsyncMock()
        examples_update.callback_query.edit_message_text = mocker.AsyncMock()

        await bot_handlers.examples_callback(examples_update, existing_user_context)

        # Verify examples shown
        examples_update.callback_query.edit_message_text.assert_called_once()
        examples_call_args = examples_update.callback_query.edit_message_text.call_args
        assert "Good Prompt" in examples_call_args[0][0]
        assert "Bad Prompt" in examples_call_args[0][0]
        assert "Practice" in str(examples_call_args[1]["reply_markup"])

        # Step 6: Start practice
        practice_update = mocker.Mock(spec=Update)
        practice_update.effective_user = existing_user_update.effective_user
        practice_update.callback_query = mocker.Mock()
        practice_update.callback_query.data = "practice_1"
        practice_update.callback_query.answer = mocker.AsyncMock()
        practice_update.callback_query.edit_message_text = mocker.AsyncMock()

        await bot_handlers.practice_callback(practice_update, existing_user_context)

        # Verify practice exercise shown
        practice_update.callback_query.edit_message_text.assert_called_once()
        practice_call_args = practice_update.callback_query.edit_message_text.call_args
        assert "Practice Exercise" in practice_call_args[0][0]
        assert "Send your prompt" in practice_call_args[0][0]

        # Step 7: Submit prompt for evaluation
        prompt_update = mocker.Mock(spec=Update)
        prompt_update.effective_user = existing_user_update.effective_user
        prompt_update.message = mocker.Mock()
        prompt_update.message.text = "Write a Python function to calculate fibonacci numbers"
        prompt_update.message.chat = mocker.Mock()
        prompt_update.message.chat.send_action = mocker.AsyncMock()
        analyzing_msg = mocker.AsyncMock()
        analyzing_msg.edit_text = mocker.AsyncMock()
        analyzing_msg.delete = mocker.AsyncMock()
        prompt_update.message.reply_text = mocker.AsyncMock(return_value=analyzing_msg)

        await bot_handlers.text_message_handler(prompt_update, existing_user_context)

        # Verify evaluation response
        prompt_update.message.reply_text.assert_called_once()
        analyzing_call_args = prompt_update.message.reply_text.call_args
        assert "Analyzing your prompt" in analyzing_call_args[0][0]

        # Verify the message was edited with evaluation results
        analyzing_msg.edit_text.assert_called_once()
        edit_call_args = analyzing_msg.edit_text.call_args
        response_text = edit_call_args[0][0]
        assert "8" in response_text  # Score
        assert "Clear task description" in response_text  # Strengths

        # Step 8: Complete lesson
        complete_update = mocker.Mock(spec=Update)
        complete_update.effective_user = existing_user_update.effective_user
        complete_update.callback_query = mocker.Mock()
        complete_update.callback_query.data = "lesson_complete_1"
        complete_update.callback_query.answer = mocker.AsyncMock()
        complete_update.callback_query.edit_message_text = mocker.AsyncMock()

        await bot_handlers.lesson_complete_callback(complete_update, existing_user_context)

        # Verify completion message
        complete_update.callback_query.edit_message_text.assert_called_once()
        complete_call_args = complete_update.callback_query.edit_message_text.call_args
        assert "completed" in complete_call_args[0][0].lower()
        assert "Introduction to Prompt Engineering" in complete_call_args[0][0]

    @pytest.mark.asyncio
    async def test_lesson_flow_error_handling(
        self, bot_handlers, existing_user_update, existing_user_context, mocker
    ):
        """Test error handling in lesson flow."""
        # Mock lesson not found
        mock_lesson_repo = mocker.AsyncMock()
        bot_handlers.learning_orchestrator.lesson_repo = mock_lesson_repo
        mock_lesson_repo.find_by_id.return_value = None

        # Mock session context
        bot_handlers.learning_orchestrator.get_session_context = mocker.AsyncMock(
            return_value={"current_lesson_id": 999, "lesson_step": "theory"}
        )

        lesson_select_update = mocker.Mock(spec=Update)
        lesson_select_update.effective_user = existing_user_update.effective_user
        lesson_select_update.callback_query = mocker.Mock()
        lesson_select_update.callback_query.data = "lesson_999"
        lesson_select_update.callback_query.answer = mocker.AsyncMock()
        lesson_select_update.callback_query.edit_message_text = mocker.AsyncMock()

        await bot_handlers.lesson_callback(lesson_select_update, existing_user_context)

        # Verify error message
        lesson_select_update.callback_query.edit_message_text.assert_called_once()
        error_call_args = lesson_select_update.callback_query.edit_message_text.call_args
        assert "not found" in error_call_args[0][0].lower()
