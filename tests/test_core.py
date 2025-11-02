"""Tests for core business logic."""

import pytest
from sqlalchemy.orm import Session

from promptheus.ai.openrouter_client import OpenRouterClient
from promptheus.core.assessment_engine import AssessmentEngine
from promptheus.core.learning_flow_orchestrator import LearningFlowOrchestrator
from promptheus.core.progress_tracker import ProgressTracker
from promptheus.data.models import (
    LessonStatus,
    SessionState,
    SkillLevel,
    User,
    UserProgress,
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
    def tracker(self, db_session: Session):
        """Create progress tracker."""
        return ProgressTracker(db_session)

    def test_start_lesson(self, tracker, db_session: Session, sample_user: User, sample_lesson):
        """Test starting a lesson."""
        tracker.start_lesson(sample_user.telegram_id, sample_lesson.id)

        progress = (
            db_session.query(UserProgress)
            .filter(
                UserProgress.user_id == sample_user.telegram_id,
                UserProgress.lesson_id == sample_lesson.id,
            )
            .first()
        )

        assert progress is not None
        assert progress.status == LessonStatus.IN_PROGRESS
        assert progress.attempts == 0

    def test_mark_completed(
        self, tracker, db_session: Session, sample_user: User, sample_lesson
    ):
        """Test marking lesson as completed."""
        # Start lesson first
        tracker.start_lesson(sample_user.telegram_id, sample_lesson.id)

        # Mark completed
        tracker.mark_completed(sample_user.telegram_id, sample_lesson.id, 85)

        progress = (
            db_session.query(UserProgress)
            .filter(
                UserProgress.user_id == sample_user.telegram_id,
                UserProgress.lesson_id == sample_lesson.id,
            )
            .first()
        )

        assert progress.status == LessonStatus.COMPLETED
        assert progress.last_score == 85
        assert progress.completed_at is not None

    def test_record_attempt(
        self, tracker, db_session: Session, sample_user: User, sample_lesson
    ):
        """Test recording exercise attempt."""
        # Start lesson first
        tracker.start_lesson(sample_user.telegram_id, sample_lesson.id)

        # Record attempt
        tracker.record_attempt(sample_user.telegram_id, sample_lesson.id, 75)

        progress = (
            db_session.query(UserProgress)
            .filter(
                UserProgress.user_id == sample_user.telegram_id,
                UserProgress.lesson_id == sample_lesson.id,
            )
            .first()
        )

        assert progress.attempts == 1
        assert progress.last_score == 75

    def test_get_progress_summary(
        self, tracker, db_session: Session, sample_user: User, multiple_lessons
    ):
        """Test getting progress summary."""
        # Start and complete some lessons
        tracker.start_lesson(sample_user.telegram_id, multiple_lessons[0].id)
        tracker.mark_completed(sample_user.telegram_id, multiple_lessons[0].id, 80)

        tracker.start_lesson(sample_user.telegram_id, multiple_lessons[1].id)
        tracker.mark_completed(sample_user.telegram_id, multiple_lessons[1].id, 90)

        tracker.start_lesson(sample_user.telegram_id, multiple_lessons[2].id)

        summary = tracker.get_progress_summary(sample_user.telegram_id)

        assert summary["completed"] == 2
        assert summary["total"] == 3
        assert summary["average_score"] == 85.0


class TestLearningFlowOrchestrator:
    """Tests for LearningFlowOrchestrator."""

    @pytest.fixture
    def orchestrator(self, db_session: Session):
        """Create orchestrator."""
        return LearningFlowOrchestrator(db_session)

    def test_get_personalized_path(
        self, orchestrator, db_session: Session, sample_user: User, multiple_lessons
    ):
        """Test getting personalized lesson path."""
        path = orchestrator.get_personalized_path(
            sample_user.telegram_id, SkillLevel.BEGINNER
        )

        assert len(path) == 3
        assert path[0]["title"] == "Lesson 1"
        assert path[1]["title"] == "Lesson 2"
        assert path[2]["title"] == "Lesson 3"

    def test_get_next_lesson(
        self, orchestrator, db_session: Session, sample_user: User, multiple_lessons
    ):
        """Test getting next lesson in sequence."""
        next_lesson = orchestrator.get_next_lesson(
            sample_user.telegram_id, multiple_lessons[0].id
        )

        assert next_lesson is not None
        assert next_lesson["title"] == "Lesson 2"
        assert next_lesson["order"] == 2

    def test_get_next_lesson_last_lesson(
        self, orchestrator, db_session: Session, sample_user: User, multiple_lessons
    ):
        """Test getting next lesson when on last lesson."""
        next_lesson = orchestrator.get_next_lesson(
            sample_user.telegram_id, multiple_lessons[2].id
        )

        assert next_lesson is None

    def test_update_session_state(
        self, orchestrator, db_session: Session, sample_user: User
    ):
        """Test updating session state."""
        context = {"current_step": "assessment", "question": 1}

        orchestrator.update_session_state(
            sample_user.telegram_id, SessionState.ONBOARDING, context
        )

        session = orchestrator.get_session_context(sample_user.telegram_id)

        assert session["current_step"] == "assessment"
        assert session["question"] == 1


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
