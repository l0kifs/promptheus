"""Unit tests for command handlers."""

import pytest
from telegram import InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from promptheus.bot.base_handlers import BaseBotHandlers
from promptheus.bot.command_handlers import CommandHandlersMixin


class MockCommandHandlers(BaseBotHandlers, CommandHandlersMixin):
    """Mock handlers class for testing."""


class TestCommandHandlers:
    """Tests for CommandHandlersMixin."""

    @pytest.fixture
    def mock_handlers(self, mocker):
        """Create mock handlers instance."""
        # Mock all dependencies
        ai_client = mocker.Mock()
        assessment_engine = mocker.Mock()
        learning_orchestrator = mocker.Mock()
        progress_tracker = mocker.Mock()

        return MockCommandHandlers(
            ai_client=ai_client,
            assessment_engine=assessment_engine,
            learning_orchestrator=learning_orchestrator,
            progress_tracker=progress_tracker,
        )

    @pytest.fixture
    def mock_update(self, mocker):
        """Create mock Update object."""
        update = mocker.Mock(spec=Update)
        update.effective_user = mocker.Mock()
        update.effective_user.id = 12345
        update.effective_user.username = "testuser"
        update.message = mocker.Mock()
        update.callback_query = None
        return update

    @pytest.fixture
    def mock_context(self, mocker):
        """Create mock ContextTypes object."""
        return mocker.Mock(spec=ContextTypes.DEFAULT_TYPE)

    @pytest.mark.asyncio
    async def test_start_command_new_user(self, mock_handlers, mock_update, mock_context, mocker):
        """Test /start command for new user."""
        # Mock user not found
        mock_handlers.learning_orchestrator.user_repo.find_by_telegram_id = mocker.AsyncMock(
            return_value=None
        )

        # Mock reply_text
        mock_update.message.reply_text = mocker.AsyncMock()

        await mock_handlers.start_command(mock_update, mock_context)

        # Verify user lookup
        mock_handlers.learning_orchestrator.user_repo.find_by_telegram_id.assert_called_once_with(
            12345
        )

        # Verify welcome message sent
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert "Welcome" in call_args[0][0]
        assert isinstance(call_args[1]["reply_markup"], InlineKeyboardMarkup)

    @pytest.mark.asyncio
    async def test_start_command_returning_user_no_session(
        self, mock_handlers, mock_update, mock_context, mocker
    ):
        """Test /start command for returning user with no active session."""
        # Mock existing user
        mock_user = mocker.Mock()
        mock_user.skill_level.value = "BEGINNER"
        mock_handlers.learning_orchestrator.user_repo.find_by_telegram_id = mocker.AsyncMock(
            return_value=mock_user
        )

        # Mock empty session context
        mock_handlers.learning_orchestrator.get_session_context = mocker.AsyncMock(return_value={})

        # Mock reply_text
        mock_update.message.reply_text = mocker.AsyncMock()

        await mock_handlers.start_command(mock_update, mock_context)

        # Verify session context retrieved
        mock_handlers.learning_orchestrator.get_session_context.assert_called_once_with(12345)

        # Verify welcome back message sent
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert "Welcome back" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_start_command_resume_with_section_details_theory(
        self, mock_handlers, mock_update, mock_context, mocker
    ):
        """Test enhanced resume shows specific theory section details."""
        # Mock existing user
        mock_user = mocker.Mock()
        mock_user.skill_level.value = "BEGINNER"
        mock_handlers.learning_orchestrator.user_repo.find_by_telegram_id = mocker.AsyncMock(
            return_value=mock_user
        )

        # Mock session context with theory section
        session_context = {
            "current_lesson_id": 1,
            "lesson_step": "theory",
            "theory_chunk": 1,
            "theory_chunks": ["chunk1", "chunk2", "chunk3"],
        }
        mock_handlers.learning_orchestrator.get_session_context = mocker.AsyncMock(
            return_value=session_context
        )

        # Mock lesson
        mock_lesson = mocker.Mock()
        mock_lesson.title = "Test Lesson"
        mock_handlers.learning_orchestrator.lesson_repo.find_by_id = mocker.AsyncMock(
            return_value=mock_lesson
        )

        # Mock reply_text
        mock_update.message.reply_text = mocker.AsyncMock()

        await mock_handlers.start_command(mock_update, mock_context)

        # Verify resume message contains section details
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        message_text = call_args[0][0]
        assert "Welcome back" in message_text
        assert "Test Lesson" in message_text
        assert "Theory (Part 2 of 3)" in message_text

    @pytest.mark.asyncio
    async def test_start_command_resume_with_section_details_examples(
        self, mock_handlers, mock_update, mock_context, mocker
    ):
        """Test enhanced resume shows examples section."""
        # Mock existing user
        mock_user = mocker.Mock()
        mock_user.skill_level.value = "BEGINNER"
        mock_handlers.learning_orchestrator.user_repo.find_by_telegram_id = mocker.AsyncMock(
            return_value=mock_user
        )

        # Mock session context with examples section
        session_context = {"current_lesson_id": 1, "lesson_step": "examples"}
        mock_handlers.learning_orchestrator.get_session_context = mocker.AsyncMock(
            return_value=session_context
        )

        # Mock lesson
        mock_lesson = mocker.Mock()
        mock_lesson.title = "Test Lesson"
        mock_handlers.learning_orchestrator.lesson_repo.find_by_id = mocker.AsyncMock(
            return_value=mock_lesson
        )

        # Mock reply_text
        mock_update.message.reply_text = mocker.AsyncMock()

        await mock_handlers.start_command(mock_update, mock_context)

        # Verify resume message contains examples section
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        message_text = call_args[0][0]
        assert "Welcome back" in message_text
        assert "Test Lesson" in message_text
        assert "Examples" in message_text

    @pytest.mark.asyncio
    async def test_start_command_resume_with_section_details_practice(
        self, mock_handlers, mock_update, mock_context, mocker
    ):
        """Test enhanced resume shows practice section."""
        # Mock existing user
        mock_user = mocker.Mock()
        mock_user.skill_level.value = "BEGINNER"
        mock_handlers.learning_orchestrator.user_repo.find_by_telegram_id = mocker.AsyncMock(
            return_value=mock_user
        )

        # Mock session context with practice section
        session_context = {"current_lesson_id": 1, "lesson_step": "practice"}
        mock_handlers.learning_orchestrator.get_session_context = mocker.AsyncMock(
            return_value=session_context
        )

        # Mock lesson
        mock_lesson = mocker.Mock()
        mock_lesson.title = "Test Lesson"
        mock_handlers.learning_orchestrator.lesson_repo.find_by_id = mocker.AsyncMock(
            return_value=mock_lesson
        )

        # Mock reply_text
        mock_update.message.reply_text = mocker.AsyncMock()

        await mock_handlers.start_command(mock_update, mock_context)

        # Verify resume message contains practice section
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        message_text = call_args[0][0]
        assert "Welcome back" in message_text
        assert "Test Lesson" in message_text
        assert "Practice Exercise" in message_text

    @pytest.mark.asyncio
    async def test_start_command_invalid_update(self, mock_handlers, mock_context, mocker):
        """Test /start command with invalid update (missing user or message)."""
        # Mock update without user
        mock_update = mocker.Mock(spec=Update)
        mock_update.effective_user = None

        # Should not raise exception, just return
        await mock_handlers.start_command(mock_update, mock_context)

        # Test without message
        mock_update.effective_user = mocker.Mock()
        mock_update.effective_user.id = 12345
        mock_update.message = None

        await mock_handlers.start_command(mock_update, mock_context)

    @pytest.mark.asyncio
    async def test_menu_command(self, mock_handlers, mock_update, mock_context, mocker):
        """Test /menu command."""
        # Mock reply_text
        mock_update.message.reply_text = mocker.AsyncMock()

        await mock_handlers.menu_command(mock_update, mock_context)

        # Verify menu message sent
        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert "Main Menu" in call_args[0][0]
        assert isinstance(call_args[1]["reply_markup"], InlineKeyboardMarkup)

        # Check keyboard buttons
        keyboard = call_args[1]["reply_markup"]
        buttons = []
        for row in keyboard.inline_keyboard:
            buttons.extend([btn.text for btn in row])

        assert "Continue Learning" in " ".join(buttons)
        assert "All Lessons" in " ".join(buttons)
        assert "My Progress" in " ".join(buttons)

    @pytest.mark.asyncio
    async def test_menu_callback(self, mock_handlers, mock_update, mock_context, mocker):
        """Test menu callback."""
        # Mock callback query
        mock_callback = mocker.Mock()
        mock_callback.answer = mocker.AsyncMock()
        mock_callback.edit_message_text = mocker.AsyncMock()
        mock_update.callback_query = mock_callback
        mock_update.effective_user = mocker.Mock()
        mock_update.effective_user.id = 12345

        await mock_handlers.menu_callback(mock_update, mock_context)

        # Verify callback answered
        mock_callback.answer.assert_called_once()

        # Verify message edited
        mock_callback.edit_message_text.assert_called_once()
        call_args = mock_callback.edit_message_text.call_args
        assert "Main Menu" in call_args[0][0]
        assert isinstance(call_args[1]["reply_markup"], InlineKeyboardMarkup)

    @pytest.mark.asyncio
    async def test_menu_callback_invalid_update(self, mock_handlers, mock_context, mocker):
        """Test menu callback with invalid update."""
        # Mock update without callback_query
        mock_update = mocker.Mock(spec=Update)
        mock_update.effective_user = None
        mock_update.callback_query = None

        # Should not raise exception
        await mock_handlers.menu_callback(mock_update, mock_context)
