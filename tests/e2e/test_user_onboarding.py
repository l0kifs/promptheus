"""E2E tests for user onboarding flow."""

import pytest
from telegram import Update


class TestUserOnboardingE2E:
    """E2E tests for complete user onboarding flow."""

    @pytest.fixture
    async def bot_handlers(self, dependency_container):
        """Get bot handlers from dependency container."""
        return await dependency_container.get_bot_handlers()

    @pytest.fixture
    def new_user_update(self, mock_update_factory):
        """Create update for new user."""
        return mock_update_factory(
            update_type="message", user_id=99999, username="newuser", text="/start"
        )

    @pytest.fixture
    def new_user_context(self, mock_context_factory):
        """Create context for new user."""
        return mock_context_factory()

    @pytest.mark.asyncio
    async def test_simple_onboarding_flow(
        self, bot_handlers, new_user_update, new_user_context, mocker
    ):
        """Test basic onboarding flow steps."""
        # Mock database responses for new user
        mock_user_repo = mocker.AsyncMock()
        mock_session_repo = mocker.AsyncMock()
        bot_handlers.learning_orchestrator.user_repo = mock_user_repo
        bot_handlers.learning_orchestrator.session_repo = mock_session_repo

        # New user - no existing user in DB
        mock_user_repo.find_by_telegram_id.return_value = None
        mock_session_repo.find_by_user_id.return_value = None

        # Step 1: Handle /start command for new user
        await bot_handlers.start_command(new_user_update, new_user_context)

        # Verify welcome message was sent
        new_user_update.message.reply_text.assert_called_once()
        call_args = new_user_update.message.reply_text.call_args
        assert "Welcome" in call_args[0][0]
        assert "Promptheus" in call_args[0][0]

        # Check that reply_markup contains "Start Learning" button
        reply_markup = call_args[1]["reply_markup"]
        assert reply_markup is not None
        keyboard_text = str(reply_markup)
        assert "Start Learning" in keyboard_text

    @pytest.mark.asyncio
    async def test_complete_onboarding_flow(
        self, bot_handlers, new_user_update, new_user_context, mocker
    ):
        """Test complete onboarding flow from /start to personalized path."""
        # Mock all dependencies
        mock_user_repo = mocker.AsyncMock()
        mock_session_repo = mocker.AsyncMock()
        mock_lesson_repo = mocker.AsyncMock()
        mock_progress_repo = mocker.AsyncMock()

        bot_handlers.learning_orchestrator.user_repo = mock_user_repo
        bot_handlers.learning_orchestrator.session_repo = mock_session_repo
        bot_handlers.learning_orchestrator.lesson_repo = mock_lesson_repo
        bot_handlers.progress_tracker.progress_repo = mock_progress_repo

        # Mock assessment engine
        bot_handlers.assessment_engine.get_assessment_questions.return_value = [
            {
                "question": "What is prompt engineering?",
                "options": ["A) Writing code", "B) Crafting prompts for AI", "C) Building robots"],
                "correct": "B",
            }
        ]
        bot_handlers.assessment_engine.evaluate_answers = mocker.AsyncMock(
            return_value={
                "score": 100,
                "level": "advanced",
                "correct": 1,
                "total": 1,
            }
        )

        # Mock learning orchestrator
        bot_handlers.learning_orchestrator.get_session_context = mocker.AsyncMock(
            return_value={
                "assessment_questions": [
                    {
                        "question": "What is prompt engineering?",
                        "options": [
                            "A) Writing code",
                            "B) Crafting prompts for AI",
                            "C) Building robots",
                        ],
                        "correct": "B",
                    }
                ],
                "assessment_answers": ["B"],
                "current_question": 0,
            }
        )
        bot_handlers.learning_orchestrator.save_session_context = mocker.AsyncMock()
        bot_handlers.learning_orchestrator.update_session_state = mocker.AsyncMock()
        bot_handlers.learning_orchestrator.get_personalized_path = mocker.AsyncMock(
            return_value=[
                {"id": 1, "title": "Introduction to Prompt Engineering", "order": 1},
                {"id": 2, "title": "Defining AI Roles", "order": 2},
            ]
        )

        # New user setup
        mock_user_repo.find_by_telegram_id.return_value = None
        mock_session_repo.find_by_user_id.return_value = None
        mock_user_repo.create = mocker.AsyncMock()
        mock_user_repo.update_assessment_score = mocker.AsyncMock()

        # Step 1: /start command
        await bot_handlers.start_command(new_user_update, new_user_context)

        # Verify welcome message
        new_user_update.message.reply_text.assert_called_once()
        call_args = new_user_update.message.reply_text.call_args
        assert "Welcome" in call_args[0][0]
        assert "Start Learning" in str(call_args[1]["reply_markup"])

        # Step 2: Click "Start Learning"
        start_learning_update = mocker.Mock(spec=Update)
        start_learning_update.effective_user = new_user_update.effective_user
        start_learning_update.callback_query = mocker.Mock()
        start_learning_update.callback_query.data = "start_learning"
        start_learning_update.callback_query.answer = mocker.AsyncMock()
        start_learning_update.callback_query.edit_message_text = mocker.AsyncMock()

        await bot_handlers.start_learning_callback(start_learning_update, new_user_context)

        # Verify assessment intro
        start_learning_update.callback_query.edit_message_text.assert_called_once()
        edit_call_args = start_learning_update.callback_query.edit_message_text.call_args
        assert "determine your level" in edit_call_args[0][0].lower()
        assert "Start Test" in str(edit_call_args[1]["reply_markup"])

        # Step 3: Click "Start Test"
        start_assessment_update = mocker.Mock(spec=Update)
        start_assessment_update.effective_user = new_user_update.effective_user
        start_assessment_update.callback_query = mocker.Mock()
        start_assessment_update.callback_query.data = "start_assessment"
        start_assessment_update.callback_query.answer = mocker.AsyncMock()
        start_assessment_update.callback_query.edit_message_text = mocker.AsyncMock()

        await bot_handlers.start_assessment_callback(start_assessment_update, new_user_context)

        # Verify first question
        start_assessment_update.callback_query.edit_message_text.assert_called_once()
        question_call_args = start_assessment_update.callback_query.edit_message_text.call_args
        assert "What is prompt engineering?" in question_call_args[0][0]
        assert "A) Writing code" in str(question_call_args[1]["reply_markup"])

        # Step 4: Answer question
        answer_update = mocker.Mock(spec=Update)
        answer_update.effective_user = new_user_update.effective_user
        answer_update.callback_query = mocker.Mock()
        answer_update.callback_query.data = "answer_B"
        answer_update.callback_query.answer = mocker.AsyncMock()
        answer_update.callback_query.edit_message_text = mocker.AsyncMock()
        answer_update.callback_query.message = mocker.Mock()
        answer_update.callback_query.message.reply_text = mocker.AsyncMock()
        answer_update.callback_query.message.chat = mocker.Mock()
        answer_update.callback_query.message.chat.send_action = mocker.AsyncMock()

        # Mock the loading message returned by reply_text
        loading_msg = mocker.AsyncMock()
        answer_update.callback_query.message.reply_text.return_value = loading_msg

        await bot_handlers.answer_callback(answer_update, new_user_context)

        # Verify goal selection shown by editing the loading message
        loading_msg.edit_text.assert_called_once()
        goal_call_args = loading_msg.edit_text.call_args
        assert "learning goal" in goal_call_args[0][0].lower()
        assert "Professional" in str(goal_call_args[1]["reply_markup"])

        # Step 5: Select goal
        goal_update = mocker.Mock(spec=Update)
        goal_update.effective_user = new_user_update.effective_user
        goal_update.callback_query = mocker.Mock()
        goal_update.callback_query.data = "goal_professional"
        goal_update.callback_query.answer = mocker.AsyncMock()
        goal_update.callback_query.edit_message_text = mocker.AsyncMock()

        await bot_handlers.goal_callback(goal_update, new_user_context)

        # Verify personalized path
        goal_update.callback_query.edit_message_text.assert_called_once()
        path_call_args = goal_update.callback_query.edit_message_text.call_args
        assert "path is ready" in path_call_args[0][0].lower()
        assert "recommended lessons" in path_call_args[0][0].lower()
        assert "Introduction to Prompt Engineering" in path_call_args[0][0]

        # Verify user was created
        mock_user_repo.create.assert_called_once()
        mock_user_repo.update_assessment_score.assert_called_once()

    @pytest.mark.asyncio
    async def test_onboarding_flow_error_handling(
        self, bot_handlers, new_user_update, new_user_context, mocker
    ):
        """Test error handling during onboarding flow."""
        # Mock database error
        mock_user_repo = mocker.AsyncMock()
        bot_handlers.learning_orchestrator.user_repo = mock_user_repo
        mock_user_repo.find_by_telegram_id.side_effect = Exception("Database connection failed")

        # Attempt /start command - should raise exception
        with pytest.raises(Exception, match="Database connection failed"):
            await bot_handlers.start_command(new_user_update, new_user_context)
