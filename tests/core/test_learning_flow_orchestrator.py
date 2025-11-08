"""Tests for LearningFlowOrchestrator."""

import pytest

from promptheus.core.learning_flow_orchestrator import LearningFlowOrchestrator
from promptheus.data.models import SessionState, SkillLevel


class TestLearningFlowOrchestrator:
    """Tests for LearningFlowOrchestrator."""

    @pytest.fixture
    async def orchestrator(self, mocker):
        """Create orchestrator with mocked repos."""
        mock_user_repo = mocker.AsyncMock()
        mock_lesson_repo = mocker.AsyncMock()
        mock_session_repo = mocker.AsyncMock()
        return LearningFlowOrchestrator(mock_user_repo, mock_lesson_repo, mock_session_repo)

    @pytest.mark.asyncio
    async def test_get_personalized_path_returns_ordered_lessons_for_skill_level(
        self, orchestrator
    ):
        """Test getting personalized learning path."""
        user_id = 123

        # Mock user and lessons
        mock_user = type("MockUser", (), {"skill_level": SkillLevel.BEGINNER})()
        mock_lessons = [
            type("MockLesson", (), {"id": 1, "title": "Lesson 1", "order_index": 1})(),
            type("MockLesson", (), {"id": 2, "title": "Lesson 2", "order_index": 2})(),
            type("MockLesson", (), {"id": 3, "title": "Lesson 3", "order_index": 3})(),
        ]

        orchestrator.user_repo.find_by_telegram_id.return_value = mock_user
        orchestrator.lesson_repo.find_by_skill_level.return_value = mock_lessons

        path = await orchestrator.get_personalized_path(user_id, SkillLevel.BEGINNER)

        assert len(path) == 3
        assert path[0]["title"] == "Lesson 1"
        assert path[1]["title"] == "Lesson 2"
        assert path[2]["title"] == "Lesson 3"

    @pytest.mark.asyncio
    async def test_get_next_lesson_returns_next_lesson_in_sequence(self, orchestrator):
        """Test getting next lesson in sequence."""
        user_id = 123
        current_lesson_id = 1

        # Mock user and lessons
        mock_user = type("MockUser", (), {"skill_level": SkillLevel.BEGINNER})()
        mock_current_lesson = type("MockLesson", (), {"order_index": 1})()
        mock_next_lesson = type(
            "MockLesson", (), {"id": 2, "title": "Lesson 2", "order_index": 2}
        )()

        orchestrator.user_repo.find_by_telegram_id.return_value = mock_user
        orchestrator.lesson_repo.find_by_id.return_value = mock_current_lesson
        orchestrator.lesson_repo.find_next_lesson.return_value = mock_next_lesson

        next_lesson = await orchestrator.get_next_lesson(user_id, current_lesson_id)

        assert next_lesson is not None
        assert next_lesson["title"] == "Lesson 2"
        assert next_lesson["order"] == 2

    @pytest.mark.asyncio
    async def test_get_next_lesson_when_on_last_lesson_returns_none(self, orchestrator):
        """Test getting next lesson when on last lesson."""
        user_id = 123
        current_lesson_id = 3

        # Mock user and lessons
        mock_user = type("MockUser", (), {"skill_level": SkillLevel.BEGINNER})()
        mock_current_lesson = type("MockLesson", (), {"order_index": 3})()

        orchestrator.user_repo.find_by_telegram_id.return_value = mock_user
        orchestrator.lesson_repo.find_by_id.return_value = mock_current_lesson
        orchestrator.lesson_repo.find_next_lesson.return_value = None

        next_lesson = await orchestrator.get_next_lesson(user_id, current_lesson_id)

        assert next_lesson is None

    @pytest.mark.asyncio
    async def test_update_session_state_creates_or_updates_session_with_state_and_context(
        self, orchestrator
    ):
        """Test updating session state."""
        user_id = 123
        context = {"current_step": "assessment", "question": 1}

        await orchestrator.update_session_state(user_id, SessionState.ONBOARDING, context)

        # Verify the session repo was called
        orchestrator.session_repo.create_or_update.assert_called_once_with(
            user_id, SessionState.ONBOARDING, context
        )

    @pytest.mark.asyncio
    async def test_get_next_lesson_when_user_not_found_returns_none(self, orchestrator):
        """Test getting next lesson when user is not found."""
        user_id = 123
        current_lesson_id = 1

        # Mock user not found
        orchestrator.user_repo.find_by_telegram_id.return_value = None

        next_lesson = await orchestrator.get_next_lesson(user_id, current_lesson_id)

        assert next_lesson is None
        # Verify user repo was called but lesson repo was not
        orchestrator.user_repo.find_by_telegram_id.assert_called_once_with(user_id)
        orchestrator.lesson_repo.find_by_id.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_next_lesson_when_current_lesson_not_found_returns_none(self, orchestrator):
        """Test getting next lesson when current lesson is not found."""
        user_id = 123
        current_lesson_id = 1

        # Mock user exists but current lesson not found
        mock_user = type("MockUser", (), {"skill_level": SkillLevel.BEGINNER})()
        orchestrator.user_repo.find_by_telegram_id.return_value = mock_user
        orchestrator.lesson_repo.find_by_id.return_value = None

        next_lesson = await orchestrator.get_next_lesson(user_id, current_lesson_id)

        assert next_lesson is None
        # Verify both repos were called
        orchestrator.user_repo.find_by_telegram_id.assert_called_once_with(user_id)
        orchestrator.lesson_repo.find_by_id.assert_called_once_with(current_lesson_id)
        orchestrator.lesson_repo.find_next_lesson.assert_not_called()

    @pytest.mark.asyncio
    async def test_save_session_context_when_session_exists_updates_context(self, orchestrator):
        """Test saving session context when session exists."""
        user_id = 123
        context = {"current_step": "lesson", "progress": 50}

        # Mock existing session
        mock_session = type("MockSession", (), {})()
        orchestrator.session_repo.find_by_user.return_value = mock_session

        await orchestrator.save_session_context(user_id, context)

        # Verify context was updated
        orchestrator.session_repo.update_context.assert_called_once_with(user_id, context)
        orchestrator.session_repo.create_or_update.assert_not_called()

    @pytest.mark.asyncio
    async def test_save_session_context_when_no_session_exists_creates_new_session(
        self, orchestrator
    ):
        """Test saving session context when no session exists."""
        user_id = 123
        context = {"current_step": "lesson", "progress": 50}

        # Mock no existing session
        orchestrator.session_repo.find_by_user.return_value = None

        await orchestrator.save_session_context(user_id, context)

        # Verify new session was created
        orchestrator.session_repo.create_or_update.assert_called_once_with(
            user_id, SessionState.ONBOARDING, context
        )
        orchestrator.session_repo.update_context.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_session_context_when_session_exists_returns_context_data(self, orchestrator):
        """Test getting session context when session exists."""
        user_id = 123
        expected_context = {"current_step": "assessment", "question": 2}

        # Mock existing session
        mock_session = type("MockSession", (), {"context_data": expected_context})()
        orchestrator.session_repo.find_by_user.return_value = mock_session

        context = await orchestrator.get_session_context(user_id)

        assert context == expected_context
        orchestrator.session_repo.find_by_user.assert_called_once_with(user_id)

    @pytest.mark.asyncio
    async def test_get_session_context_when_no_session_exists_returns_empty_dict(
        self, orchestrator
    ):
        """Test getting session context when no session exists."""
        user_id = 123

        # Mock no existing session
        orchestrator.session_repo.find_by_user.return_value = None

        context = await orchestrator.get_session_context(user_id)

        assert context == {}
        orchestrator.session_repo.find_by_user.assert_called_once_with(user_id)
