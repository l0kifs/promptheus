"""E2E tests for navigation and menu flow."""

import pytest
from telegram import Update

from promptheus.data.models import SkillLevel


class TestNavigationE2E:
    """E2E tests for bot navigation and menu system."""

    @pytest.fixture
    async def bot_handlers(self, dependency_container):
        """Get bot handlers from dependency container."""
        return await dependency_container.get_bot_handlers()

    @pytest.fixture
    def menu_user_update(self, mock_update_factory):
        """Create update for menu navigation."""
        return mock_update_factory(
            update_type="callback_query", user_id=12345, username="testuser", callback_data="menu"
        )

    @pytest.fixture
    def menu_user_context(self, mock_context_factory):
        """Create context for menu navigation."""
        return mock_context_factory()

    @pytest.mark.asyncio
    async def test_main_menu_navigation(
        self, bot_handlers, menu_user_update, menu_user_context, mocker
    ):
        """Test main menu display and navigation options."""
        # Mock user repository
        mock_user_repo = mocker.AsyncMock()
        bot_handlers.learning_orchestrator.user_repo = mock_user_repo

        # Mock session methods
        bot_handlers.learning_orchestrator.get_session_context = mocker.AsyncMock(return_value={})
        bot_handlers.learning_orchestrator.update_session_state = mocker.AsyncMock()

        # Mock existing user
        mock_user = type("MockUser", (), {"skill_level": SkillLevel.BEGINNER})()
        mock_user_repo.find_by_telegram_id.return_value = mock_user

        # Step 1: Access main menu
        await bot_handlers.menu_callback(menu_user_update, menu_user_context)

        # Verify main menu shown
        menu_user_update.callback_query.edit_message_text.assert_called_once()
        menu_call_args = menu_user_update.callback_query.edit_message_text.call_args
        menu_text = menu_call_args[0][0]

        assert "menu" in menu_text.lower() or "choose" in menu_text.lower()
        assert "main menu" in menu_text.lower()  # Updated assertion to match actual text

        # Check menu buttons (progress is in the buttons, not the text)
        reply_markup = menu_call_args[1]["reply_markup"]
        keyboard_text = str(reply_markup).lower()
        assert "progress" in keyboard_text

    @pytest.mark.asyncio
    async def test_menu_command_access(self, bot_handlers, menu_user_context, mocker):
        """Test accessing menu via /menu command."""
        # Mock user
        mock_user_repo = mocker.AsyncMock()
        bot_handlers.learning_orchestrator.user_repo = mock_user_repo
        mock_user = type("MockUser", (), {"skill_level": SkillLevel.BEGINNER})()
        mock_user_repo.find_by_telegram_id.return_value = mock_user

        # Create command update
        menu_command_update = mocker.Mock(spec=Update)
        menu_command_update.effective_user = mocker.Mock()
        menu_command_update.effective_user.id = 12345
        menu_command_update.effective_user.username = "testuser"
        menu_command_update.message = mocker.Mock()
        menu_command_update.message.reply_text = mocker.AsyncMock()

        # Step 1: Use /menu command
        await bot_handlers.menu_command(menu_command_update, menu_user_context)

        # Verify menu response
        menu_command_update.message.reply_text.assert_called_once()
        command_call_args = menu_command_update.message.reply_text.call_args
        assert "menu" in command_call_args[0][0].lower()

    @pytest.mark.asyncio
    async def test_navigation_from_menu_to_lessons(
        self, bot_handlers, menu_user_update, menu_user_context, mocker
    ):
        """Test navigation from main menu to lessons list."""
        # Mock dependencies
        mock_user_repo = mocker.AsyncMock()
        mock_lesson_repo = mocker.AsyncMock()
        bot_handlers.learning_orchestrator.user_repo = mock_user_repo
        bot_handlers.learning_orchestrator.lesson_repo = mock_lesson_repo

        # Mock session methods
        bot_handlers.learning_orchestrator.get_session_context = mocker.AsyncMock(return_value={})
        bot_handlers.learning_orchestrator.update_session_state = mocker.AsyncMock()

        # Mock user and lessons
        mock_user = type("MockUser", (), {"skill_level": SkillLevel.BEGINNER})()
        mock_user_repo.find_by_telegram_id.return_value = mock_user

        mock_lessons = [
            type("MockLesson", (), {"id": 1, "title": "Lesson 1"})(),
            type("MockLesson", (), {"id": 2, "title": "Lesson 2"})(),
        ]
        mock_lesson_repo.find_by_skill_level.return_value = mock_lessons

        # Step 1: Go to main menu
        await bot_handlers.menu_callback(menu_user_update, menu_user_context)

        # Step 2: Navigate to lessons from menu
        lessons_update = mocker.Mock(spec=Update)
        lessons_update.effective_user = menu_user_update.effective_user
        lessons_update.callback_query = mocker.Mock()
        lessons_update.callback_query.data = "lesson_list"
        lessons_update.callback_query.answer = mocker.AsyncMock()
        lessons_update.callback_query.edit_message_text = mocker.AsyncMock()

        await bot_handlers.lesson_list_callback(lessons_update, menu_user_context)

        # Verify lessons list shown
        lessons_update.callback_query.edit_message_text.assert_called_once()
        lessons_call_args = lessons_update.callback_query.edit_message_text.call_args
        assert "Lesson 1" in lessons_call_args[0][0]
        assert "Lesson 2" in lessons_call_args[0][0]

    @pytest.mark.asyncio
    async def test_navigation_back_to_menu(
        self, bot_handlers, menu_user_update, menu_user_context, mocker
    ):
        """Test navigation back to main menu from various sections."""
        # Mock user
        mock_user_repo = mocker.AsyncMock()
        bot_handlers.learning_orchestrator.user_repo = mock_user_repo
        mock_user = type("MockUser", (), {"skill_level": SkillLevel.BEGINNER})()
        mock_user_repo.find_by_telegram_id.return_value = mock_user

        # Mock session methods
        bot_handlers.learning_orchestrator.get_session_context = mocker.AsyncMock(return_value={})
        bot_handlers.learning_orchestrator.update_session_state = mocker.AsyncMock()

        # Step 1: Be in some section (simulate lesson view)
        lesson_view_update = mocker.Mock(spec=Update)
        lesson_view_update.effective_user = menu_user_update.effective_user
        lesson_view_update.callback_query = mocker.Mock()
        lesson_view_update.callback_query.data = "menu"
        lesson_view_update.callback_query.answer = mocker.AsyncMock()
        lesson_view_update.callback_query.edit_message_text = mocker.AsyncMock()

        # Step 2: Click "Back to Menu" or similar
        await bot_handlers.menu_callback(lesson_view_update, menu_user_context)

        # Verify returned to main menu
        lesson_view_update.callback_query.edit_message_text.assert_called_once()
        back_call_args = lesson_view_update.callback_query.edit_message_text.call_args
        assert "menu" in back_call_args[0][0].lower()

    @pytest.mark.asyncio
    async def test_continue_session_navigation(self, bot_handlers, menu_user_context, mocker):
        """Test continue session navigation for returning users."""
        # Mock dependencies
        mock_user_repo = mocker.AsyncMock()
        mock_session_repo = mocker.AsyncMock()
        mock_lesson_repo = mocker.AsyncMock()
        bot_handlers.learning_orchestrator.user_repo = mock_user_repo
        bot_handlers.learning_orchestrator.session_repo = mock_session_repo
        bot_handlers.learning_orchestrator.lesson_repo = mock_lesson_repo

        # Mock returning user with active session
        mock_user = type("MockUser", (), {"skill_level": SkillLevel.BEGINNER})()
        mock_user_repo.find_by_telegram_id.return_value = mock_user

        # Mock session context for start_command
        bot_handlers.learning_orchestrator.get_session_context = mocker.AsyncMock(
            return_value={"current_lesson_id": 1, "lesson_step": "practice"}
        )

        mock_session = type(
            "MockSession", (), {"current_lesson_id": 1, "lesson_step": "practice"}
        )()
        mock_session_repo.find_by_user_id.return_value = mock_session

        mock_lesson = type("MockLesson", (), {"title": "Active Lesson"})()
        mock_lesson_repo.find_by_id.return_value = mock_lesson

        # Create /start update for returning user
        start_update = mocker.Mock(spec=Update)
        start_update.effective_user = mocker.Mock()
        start_update.effective_user.id = 12345
        start_update.effective_user.username = "returninguser"
        start_update.message = mocker.Mock()
        start_update.message.reply_text = mocker.AsyncMock()

        # Step 1: Returning user starts bot
        await bot_handlers.start_command(start_update, menu_user_context)

        # Verify resume option shown
        start_update.message.reply_text.assert_called_once()
        resume_call_args = start_update.message.reply_text.call_args
        assert "Welcome back" in resume_call_args[0][0]
        assert "Active Lesson" in resume_call_args[0][0]
        assert "Continue" in str(resume_call_args[1]["reply_markup"])

    @pytest.mark.asyncio
    async def test_navigation_progress_tracking(
        self, bot_handlers, menu_user_update, menu_user_context, mocker
    ):
        """Test navigation to progress tracking section."""
        # Mock dependencies
        mock_user_repo = mocker.AsyncMock()
        mock_progress_repo = mocker.AsyncMock()
        mock_lesson_repo = mocker.AsyncMock()
        bot_handlers.learning_orchestrator.user_repo = mock_user_repo
        bot_handlers.learning_orchestrator.lesson_repo = mock_lesson_repo
        bot_handlers.progress_tracker.progress_repo = mock_progress_repo
        bot_handlers.progress_tracker.get_progress_summary = mocker.AsyncMock(
            return_value={"completed": 1, "in_progress": 1, "total": 2, "average_score": 85.0}
        )

        # Mock user and progress
        mock_user = type(
            "MockUser",
            (),
            {
                "skill_level": SkillLevel.BEGINNER,
                "learning_goal": type("MockGoal", (), {"value": "academic"})(),
            },
        )()
        mock_user_repo.find_by_telegram_id.return_value = mock_user

        mock_progresses = [
            type("MockProgress", (), {"status": "completed", "last_score": 85, "lesson_id": 1})(),
            type(
                "MockProgress", (), {"status": "in_progress", "last_score": None, "lesson_id": 2}
            )(),
        ]
        mock_progress_repo.find_by_user.return_value = mock_progresses

        # Mock lessons
        mock_lesson1 = type("MockLesson", (), {"title": "Completed Lesson"})()
        mock_lesson2 = type("MockLesson", (), {"title": "In Progress Lesson"})()
        mock_lesson_repo.find_by_id.side_effect = (
            lambda id: mock_lesson1 if id == 1 else mock_lesson2
        )

        # Step 1: Navigate to progress from menu
        progress_update = mocker.Mock(spec=Update)
        progress_update.effective_user = menu_user_update.effective_user
        progress_update.callback_query = mocker.Mock()
        progress_update.callback_query.data = "progress"
        progress_update.callback_query.answer = mocker.AsyncMock()
        progress_update.callback_query.edit_message_text = mocker.AsyncMock()

        await bot_handlers.progress_callback(progress_update, menu_user_context)

        # Verify progress shown
        progress_update.callback_query.edit_message_text.assert_called_once()
        progress_call_args = progress_update.callback_query.edit_message_text.call_args
        assert "progress" in progress_call_args[0][0].lower()
        assert "completed" in progress_call_args[0][0].lower() or "85" in progress_call_args[0][0]
