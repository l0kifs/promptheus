"""Tests for core business logic."""

import pytest

from promptheus.ai.openrouter_client import OpenRouterClient
from promptheus.core.assessment_engine import AssessmentEngine
from promptheus.core.learning_flow_orchestrator import LearningFlowOrchestrator
from promptheus.core.progress_tracker import ProgressTracker
from promptheus.data.models import (
    LessonStatus,
    SessionState,
    SkillLevel,
)


class TestAssessmentEngine:
    """Tests for AssessmentEngine."""

    @pytest.fixture
    def ai_client(self, mocker):
        """Mock AI client."""
        return mocker.Mock(spec=OpenRouterClient)

    @pytest.fixture
    def engine(self, ai_client):
        """Create assessment engine."""
        return AssessmentEngine(ai_client)

    def test_get_assessment_questions(self, engine):
        """Test getting assessment questions."""
        questions = engine.get_assessment_questions()

        assert len(questions) == 5
        assert all("question" in q for q in questions)
        assert all("options" in q for q in questions)
        assert all("correct" in q for q in questions)

    @pytest.mark.asyncio
    async def test_evaluate_answers_all_correct(self, engine):
        """Test evaluation with all correct answers."""
        answers = ["B", "C", "A", "B", "B"]  # All correct based on questions
        result = await engine.evaluate_answers(answers)

        assert result["score"] == 100
        assert result["level"] == "advanced"
        assert result["correct"] == 5
        assert result["total"] == 5

    @pytest.mark.asyncio
    async def test_evaluate_answers_beginner(self, engine):
        """Test evaluation for beginner level."""
        answers = ["A", "A", "B", "A", "A"]  # 0 correct
        result = await engine.evaluate_answers(answers)

        assert result["score"] == 0
        assert result["level"] == "beginner"
        assert result["correct"] == 0
        assert result["total"] == 5
        assert result["total"] == 5

    @pytest.mark.asyncio
    async def test_evaluate_answers_intermediate(self, engine):
        """Test evaluation for intermediate level."""
        answers = ["B", "C", "A", "A", "A"]  # 3 correct
        result = await engine.evaluate_answers(answers)

        assert result["score"] == 60
        assert result["level"] == "intermediate"
        assert result["correct"] == 3


class TestProgressTracker:
    """Tests for ProgressTracker."""

    @pytest.fixture
    def tracker(self, mocker):
        """Create progress tracker with mocked repo."""
        mock_repo = mocker.AsyncMock()
        return ProgressTracker(mock_repo)

    @pytest.mark.asyncio
    async def test_start_lesson(self, tracker):
        """Test starting a lesson."""
        user_id = 123
        lesson_id = 456

        # Mock the repo to return None (no existing progress)
        tracker.progress_repo.find_by_user_and_lesson.return_value = None
        tracker.progress_repo.create.return_value = None

        await tracker.start_lesson(user_id, lesson_id)

        # Verify the repo methods were called correctly
        tracker.progress_repo.find_by_user_and_lesson.assert_called_once_with(user_id, lesson_id)
        tracker.progress_repo.create.assert_called_once_with(user_id, lesson_id)

    @pytest.mark.asyncio
    async def test_mark_completed(self, tracker):
        """Test marking lesson as completed."""
        user_id = 123
        lesson_id = 456
        score = 85

        # Create a mock progress object
        mock_progress = type(
            "MockProgress", (), {"status": None, "last_score": None, "completed_at": None}
        )()

        tracker.progress_repo.find_by_user_and_lesson.return_value = mock_progress

        await tracker.mark_completed(user_id, lesson_id, score)

        # Verify the progress was updated
        assert mock_progress.status == LessonStatus.COMPLETED
        assert mock_progress.last_score == score
        assert mock_progress.completed_at is not None

    @pytest.mark.asyncio
    async def test_record_attempt(self, tracker):
        """Test recording exercise attempt."""
        user_id = 123
        lesson_id = 456
        score = 75

        # Create a mock progress object
        mock_progress = type("MockProgress", (), {"attempts": 0, "last_score": None})()

        tracker.progress_repo.find_by_user_and_lesson.return_value = mock_progress

        await tracker.record_attempt(user_id, lesson_id, score)

        # Verify the repo methods were called
        tracker.progress_repo.increment_attempts.assert_called_once_with(user_id, lesson_id)
        tracker.progress_repo.update_score.assert_called_once_with(user_id, lesson_id, score)

    @pytest.mark.asyncio
    async def test_get_progress_summary(self, tracker):
        """Test getting progress summary."""
        user_id = 123

        # Create mock progress records
        mock_progresses = [
            type("MockProgress", (), {"status": LessonStatus.COMPLETED, "last_score": 80})(),
            type("MockProgress", (), {"status": LessonStatus.COMPLETED, "last_score": 90})(),
            type("MockProgress", (), {"status": LessonStatus.IN_PROGRESS, "last_score": None})(),
        ]

        tracker.progress_repo.find_by_user.return_value = mock_progresses

        summary = await tracker.get_progress_summary(user_id)

        assert summary["completed"] == 2
        assert summary["total"] == 3
        assert summary["average_score"] == 85.0


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
    async def test_get_personalized_path(self, orchestrator):
        """Test getting personalized lesson path."""
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
    async def test_get_next_lesson(self, orchestrator):
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
    async def test_get_next_lesson_last_lesson(self, orchestrator):
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
    async def test_update_session_state(self, orchestrator):
        """Test updating session state."""
        user_id = 123
        context = {"current_step": "assessment", "question": 1}

        await orchestrator.update_session_state(user_id, SessionState.ONBOARDING, context)

        # Verify the session repo was called
        orchestrator.session_repo.create_or_update.assert_called_once_with(
            user_id, SessionState.ONBOARDING, context
        )


class TestMessageFormatter:
    """Tests for MessageFormatter."""

    def test_format_welcome(self):
        """Test welcome message formatting."""
        from promptheus.bot.message_formatter import MessageFormatter

        formatter = MessageFormatter()
        message = formatter.format_welcome()

        assert "Welcome" in message
        assert "Promptheus" in message

    def test_format_question(self):
        """Test question formatting."""
        from promptheus.bot.message_formatter import MessageFormatter

        formatter = MessageFormatter()
        message = formatter.format_question(
            1, 5, "What is prompt engineering?", ["A) Option 1", "B) Option 2"]
        )

        assert "Question 1/5" in message
        assert "What is prompt engineering?" in message
        assert "A) Option 1" in message

    def test_format_lesson_complete(self):
        """Test lesson completion message."""
        from promptheus.bot.message_formatter import MessageFormatter

        formatter = MessageFormatter()
        message = formatter.format_lesson_complete("Test Lesson", 85, 2)

        assert "completed" in message.lower()
        assert "Test Lesson" in message
        assert "85" in message
        assert "2" in message
