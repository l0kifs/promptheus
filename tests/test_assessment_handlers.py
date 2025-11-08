"""Unit tests for assessment handlers."""

import pytest
from telegram import InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from promptheus.bot.assessment_handlers import AssessmentHandlersMixin
from promptheus.bot.base_handlers import BaseBotHandlers
from promptheus.data.models import LearningGoal, SkillLevel


class MockAssessmentHandlers(BaseBotHandlers, AssessmentHandlersMixin):
    """Mock handlers class for testing."""


class TestAssessmentHandlers:
    """Tests for AssessmentHandlersMixin."""

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
        learning_orchestrator.update_session_state = mocker.AsyncMock()
        learning_orchestrator.user_repo = mocker.Mock()
        learning_orchestrator.user_repo.create = mocker.AsyncMock()
        learning_orchestrator.user_repo.update_assessment_score = mocker.AsyncMock()
        learning_orchestrator.user_repo.find_by_telegram_id = mocker.AsyncMock()
        learning_orchestrator.get_personalized_path = mocker.AsyncMock()
        assessment_engine.evaluate_answers = mocker.AsyncMock()

        return MockAssessmentHandlers(
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
        update.effective_user.username = "testuser"
        update.callback_query = mocker.Mock()
        update.callback_query.data = "test_data"
        update.message = None
        return update

    @pytest.fixture
    def mock_context(self, mocker):
        """Create mock ContextTypes object."""
        return mocker.Mock(spec=ContextTypes.DEFAULT_TYPE)

    @pytest.mark.asyncio
    async def test_start_learning_callback(
        self, mock_handlers, mock_callback_update, mock_context, mocker
    ):
        """Test start learning callback."""
        # Mock callback answer and edit
        mock_callback_update.callback_query.answer = mocker.AsyncMock()
        mock_callback_update.callback_query.edit_message_text = mocker.AsyncMock()

        await mock_handlers.start_learning_callback(mock_callback_update, mock_context)

        # Verify callback answered
        mock_callback_update.callback_query.answer.assert_called_once()

        # Verify message edited with assessment intro
        mock_callback_update.callback_query.edit_message_text.assert_called_once()
        call_args = mock_callback_update.callback_query.edit_message_text.call_args
        assert "determine your level" in call_args[0][0].lower()
        assert "5" in call_args[0][0]
        assert isinstance(call_args[1]["reply_markup"], InlineKeyboardMarkup)

    @pytest.mark.asyncio
    async def test_start_assessment_callback(
        self, mock_handlers, mock_callback_update, mock_context, mocker
    ):
        """Test start assessment callback."""
        # Mock assessment questions
        questions = [
            {"question": "Test Q1", "options": ["A) Opt1", "B) Opt2"], "correct": "B"},
            {"question": "Test Q2", "options": ["A) Opt3", "B) Opt4"], "correct": "A"},
        ]
        mock_handlers.assessment_engine.get_assessment_questions.return_value = questions

        # Mock session context operations
        mock_handlers.learning_orchestrator.get_session_context.return_value = {}

        # Mock callback operations
        mock_callback_update.callback_query.answer = mocker.AsyncMock()
        mock_callback_update.callback_query.edit_message_text = mocker.AsyncMock()

        await mock_handlers.start_assessment_callback(mock_callback_update, mock_context)

        # Verify session context saved with assessment data
        expected_context = {
            "assessment_questions": questions,
            "assessment_answers": [],
            "current_question": 0,
        }
        mock_handlers.learning_orchestrator.save_session_context.assert_called_with(
            12345, expected_context
        )

        # Verify first question shown
        mock_callback_update.callback_query.edit_message_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_answer_callback(self, mock_handlers, mock_callback_update, mock_context, mocker):
        """Test answer callback."""
        # Set callback data to simulate answer
        mock_callback_update.callback_query.data = "answer_B"

        # Mock session context
        session_context = {
            "assessment_questions": [{"question": "Q1", "options": ["A", "B"], "correct": "B"}],
            "assessment_answers": [],
            "current_question": 0,
        }
        mock_handlers.learning_orchestrator.get_session_context.return_value = session_context

        # Mock assessment evaluation for finish assessment
        results = {"score": 100, "level": "expert", "correct": 1, "total": 1}
        mock_handlers.assessment_engine.evaluate_answers.return_value = results

        # Mock callback operations
        mock_callback_update.callback_query.answer = mocker.AsyncMock()
        mock_callback_update.callback_query.edit_message_text = mocker.AsyncMock()
        mock_callback_update.callback_query.message = mocker.Mock()
        mock_callback_update.callback_query.message.reply_text = mocker.AsyncMock()
        mock_callback_update.callback_query.message.chat = mocker.Mock()
        mock_callback_update.callback_query.message.chat.send_action = mocker.AsyncMock()

        # Mock the loading message returned by reply_text
        loading_msg = mocker.AsyncMock()
        mock_callback_update.callback_query.message.reply_text.return_value = loading_msg

        await mock_handlers.answer_callback(mock_callback_update, mock_context)

        # Verify answer recorded and question advanced
        expected_context = {
            "assessment_questions": [{"question": "Q1", "options": ["A", "B"], "correct": "B"}],
            "assessment_answers": ["B"],
            "current_question": 1,
            "assessment_results": results,
        }
        mock_handlers.learning_orchestrator.save_session_context.assert_called_with(
            12345, expected_context
        )

    @pytest.mark.asyncio
    async def test_finish_assessment(
        self, mock_handlers, mock_callback_update, mock_context, mocker
    ):
        """Test finishing assessment and showing goal selection."""
        # Mock assessment evaluation
        results = {"score": 80, "level": "intermediate", "correct": 4, "total": 5}
        mock_handlers.assessment_engine.evaluate_answers.return_value = results

        # Mock session context
        session_context = {
            "assessment_questions": [],
            "assessment_answers": ["A", "B", "A", "B", "B"],
            "current_question": 5,
        }
        mock_handlers.learning_orchestrator.get_session_context.return_value = session_context

        # Mock callback operations
        mock_callback_update.callback_query.answer = mocker.AsyncMock()
        mock_callback_update.callback_query.edit_message_text = mocker.AsyncMock()
        mock_callback_update.callback_query.message = mocker.Mock()
        mock_callback_update.callback_query.message.reply_text = mocker.AsyncMock()
        mock_callback_update.callback_query.message.chat = mocker.Mock()
        mock_callback_update.callback_query.message.chat.send_action = mocker.AsyncMock()

        # Mock the loading message returned by reply_text
        loading_msg = mocker.AsyncMock()
        mock_callback_update.callback_query.message.reply_text.return_value = loading_msg

        await mock_handlers._finish_assessment(mock_callback_update, mock_context)

        # Verify loading message was sent
        mock_callback_update.callback_query.message.reply_text.assert_called_once()
        loading_call_args = mock_callback_update.callback_query.message.reply_text.call_args
        assert "Evaluating your" in loading_call_args[0][0]

        # Verify goal selection shown by editing the loading message
        loading_msg.edit_text.assert_called_once()
        edit_call_args = loading_msg.edit_text.call_args
        assert "learning goal" in edit_call_args[0][0].lower()
        assert isinstance(edit_call_args[1]["reply_markup"], InlineKeyboardMarkup)

    @pytest.mark.asyncio
    async def test_goal_callback_academic(
        self, mock_handlers, mock_callback_update, mock_context, mocker
    ):
        """Test goal selection callback for academic goal."""
        mock_callback_update.callback_query.data = "goal_academic"

        # Mock session context with assessment results
        session_context = {"assessment_results": {"score": 80, "level": "intermediate"}}
        mock_handlers.learning_orchestrator.get_session_context.return_value = session_context

        # Mock personalized path
        lessons = [{"id": 1, "title": "Lesson 1"}, {"id": 2, "title": "Lesson 2"}]
        mock_handlers.learning_orchestrator.get_personalized_path.return_value = lessons

        # Mock callback operations
        mock_callback_update.callback_query.answer = mocker.AsyncMock()
        mock_callback_update.callback_query.edit_message_text = mocker.AsyncMock()

        await mock_handlers.goal_callback(mock_callback_update, mock_context)

        # Verify user created with correct parameters
        mock_handlers.learning_orchestrator.user_repo.create.assert_called_once_with(
            telegram_id=12345,
            username="testuser",
            skill_level=SkillLevel.INTERMEDIATE,
            learning_goal=LearningGoal.ACADEMIC,
        )

        # Verify assessment score updated
        mock_handlers.learning_orchestrator.user_repo.update_assessment_score.assert_called_once_with(
            12345, 80
        )

        # Verify personalized path retrieved
        mock_handlers.learning_orchestrator.get_personalized_path.assert_called_once_with(
            12345, SkillLevel.INTERMEDIATE
        )

        # Verify path shown
        mock_callback_update.callback_query.edit_message_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_goal_callback_professional(
        self, mock_handlers, mock_callback_update, mock_context, mocker
    ):
        """Test goal selection callback for professional goal."""
        mock_callback_update.callback_query.data = "goal_professional"

        # Mock session context
        session_context = {"assessment_results": {"score": 60, "level": "beginner"}}
        mock_handlers.learning_orchestrator.get_session_context.return_value = session_context

        # Mock empty personalized path (fallback to beginner)
        mock_handlers.learning_orchestrator.get_personalized_path.side_effect = [
            [],
            [{"id": 1, "title": "Beginner Lesson"}],
        ]

        # Mock callback operations
        mock_callback_update.callback_query.answer = mocker.AsyncMock()
        mock_callback_update.callback_query.edit_message_text = mocker.AsyncMock()

        await mock_handlers.goal_callback(mock_callback_update, mock_context)

        # Verify fallback to beginner lessons
        assert mock_handlers.learning_orchestrator.get_personalized_path.call_count == 2
        calls = mock_handlers.learning_orchestrator.get_personalized_path.call_args_list
        assert calls[0][0] == (12345, SkillLevel.BEGINNER)  # First call with intermediate
        assert calls[1][0] == (12345, SkillLevel.BEGINNER)  # Fallback call

    @pytest.mark.asyncio
    async def test_goal_callback_user_creation_failure(
        self, mock_handlers, mock_callback_update, mock_context, mocker
    ):
        """Test goal callback when user creation fails."""
        mock_callback_update.callback_query.data = "goal_creative"

        # Mock session context
        session_context = {"assessment_results": {"score": 50, "level": "beginner"}}
        mock_handlers.learning_orchestrator.get_session_context.return_value = session_context

        # Mock user creation failure
        mock_handlers.learning_orchestrator.user_repo.create.side_effect = Exception("DB Error")

        # Mock callback operations
        mock_callback_update.callback_query.answer = mocker.AsyncMock()
        mock_callback_update.callback_query.edit_message_text = mocker.AsyncMock()

        await mock_handlers.goal_callback(mock_callback_update, mock_context)

        # Verify error message shown
        mock_callback_update.callback_query.edit_message_text.assert_called_once()
        call_args = mock_callback_update.callback_query.edit_message_text.call_args
        assert "Failed to create user" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_invalid_callbacks(self, mock_handlers, mocker):
        """Test callbacks with invalid updates."""
        # Test with missing user
        update = mocker.Mock(spec=Update)
        update.effective_user = None
        update.callback_query = mocker.Mock()

        context = mocker.Mock(spec=ContextTypes.DEFAULT_TYPE)

        # Should not raise exceptions
        await mock_handlers.start_learning_callback(update, context)
        await mock_handlers.start_assessment_callback(update, context)
        await mock_handlers.answer_callback(update, context)
        await mock_handlers.goal_callback(update, context)
