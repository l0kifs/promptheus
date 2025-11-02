"""Tests for data repositories."""

import pytest
from sqlalchemy.orm import Session

from promptheus.data.models import (
    LearningGoal,
    Lesson,
    LessonStatus,
    SessionState,
    SkillLevel,
    User,
)
from promptheus.data.repositories import (
    LessonRepository,
    ProgressRepository,
    SessionRepository,
    UserRepository,
)


class TestUserRepository:
    """Tests for UserRepository."""

    @pytest.fixture
    def repo(self, db_session: Session):
        """Create user repository."""
        return UserRepository(db_session)

    def test_create_user(self, repo, db_session: Session):
        """Test creating a new user."""
        user = repo.create(
            telegram_id=99999,
            username="newuser",
            skill_level=SkillLevel.BEGINNER,
            learning_goal=LearningGoal.ACADEMIC,
        )

        assert user.telegram_id == 99999
        assert user.username == "newuser"
        assert user.skill_level == SkillLevel.BEGINNER
        assert user.learning_goal == LearningGoal.ACADEMIC

        # Verify in database
        db_user = db_session.query(User).filter(User.telegram_id == 99999).first()
        assert db_user is not None

    def test_find_by_telegram_id(self, repo, sample_user: User):
        """Test finding user by telegram ID."""
        user = repo.find_by_telegram_id(sample_user.telegram_id)

        assert user is not None
        assert user.telegram_id == sample_user.telegram_id
        assert user.username == sample_user.username

    def test_find_by_telegram_id_not_found(self, repo):
        """Test finding non-existent user."""
        user = repo.find_by_telegram_id(99999)

        assert user is None

    def test_update_assessment_score(self, repo, sample_user: User):
        """Test updating assessment score."""
        repo.update_assessment_score(sample_user.telegram_id, 85)

        user = repo.find_by_telegram_id(sample_user.telegram_id)
        assert user.assessment_score == 85  # type: ignore


class TestLessonRepository:
    """Tests for LessonRepository."""

    @pytest.fixture
    def repo(self, db_session: Session):
        """Create lesson repository."""
        return LessonRepository(db_session)

    def test_create_lesson(self, repo, db_session: Session):
        """Test creating a new lesson."""
        lesson = repo.create(
            title="New Lesson",
            skill_level=SkillLevel.INTERMEDIATE,
            order_index=1,
            tags=["test"],
            theory_content={"sections": []},
            examples={"comparisons": []},
            exercises={"scenarios": []},
        )

        assert lesson.title == "New Lesson"
        assert lesson.skill_level == SkillLevel.INTERMEDIATE

        # Verify in database
        db_lesson = db_session.query(Lesson).filter(Lesson.title == "New Lesson").first()
        assert db_lesson is not None

    def test_find_by_id(self, repo, sample_lesson: Lesson):
        """Test finding lesson by ID."""
        lesson = repo.find_by_id(sample_lesson.id)

        assert lesson is not None
        assert lesson.title == sample_lesson.title  # type: ignore

    def test_find_by_skill_level(self, repo, multiple_lessons):
        """Test finding lessons by skill level."""
        lessons = repo.find_by_skill_level(SkillLevel.BEGINNER)

        assert len(lessons) == 3
        assert all(lesson.skill_level == SkillLevel.BEGINNER for lesson in lessons)

    def test_find_next_lesson(self, repo, multiple_lessons):
        """Test finding next lesson in sequence."""
        next_lesson = repo.find_next_lesson(SkillLevel.BEGINNER, 1)

        assert next_lesson is not None
        assert next_lesson.order_index == 2  # type: ignore


class TestProgressRepository:
    """Tests for ProgressRepository."""

    @pytest.fixture
    def repo(self, db_session: Session):
        """Create progress repository."""
        return ProgressRepository(db_session)

    def test_create_progress(self, repo, sample_user: User, sample_lesson: Lesson):
        """Test creating progress record."""
        progress = repo.create(sample_user.telegram_id, sample_lesson.id)

        assert progress.user_id == sample_user.telegram_id  # type: ignore
        assert progress.lesson_id == sample_lesson.id  # type: ignore
        assert progress.status == LessonStatus.IN_PROGRESS

    def test_find_by_user_and_lesson(
        self, repo, sample_user: User, sample_lesson: Lesson
    ):
        """Test finding progress by user and lesson."""
        # Create progress first
        repo.create(sample_user.telegram_id, sample_lesson.id)

        # Find it
        progress = repo.find_by_user_and_lesson(
            sample_user.telegram_id, sample_lesson.id
        )

        assert progress is not None
        assert progress.user_id == sample_user.telegram_id  # type: ignore

    def test_increment_attempts(self, repo, sample_user: User, sample_lesson: Lesson):
        """Test incrementing attempt counter."""
        repo.create(sample_user.telegram_id, sample_lesson.id)

        repo.increment_attempts(sample_user.telegram_id, sample_lesson.id)
        repo.increment_attempts(sample_user.telegram_id, sample_lesson.id)

        progress = repo.find_by_user_and_lesson(
            sample_user.telegram_id, sample_lesson.id
        )
        assert progress.attempts == 2  # type: ignore


class TestSessionRepository:
    """Tests for SessionRepository."""

    @pytest.fixture
    def repo(self, db_session: Session):
        """Create session repository."""
        return SessionRepository(db_session)

    def test_create_session(self, repo, sample_user: User):
        """Test creating session."""
        context = {"step": "test"}
        session = repo.create_or_update(
            sample_user.telegram_id, SessionState.ONBOARDING, context
        )

        assert session.user_id == sample_user.telegram_id  # type: ignore
        assert session.state == SessionState.ONBOARDING

    def test_update_session(self, repo, sample_user: User):
        """Test updating existing session."""
        # Create session
        repo.create_or_update(
            sample_user.telegram_id, SessionState.ONBOARDING, {"step": "1"}
        )

        # Update it
        repo.create_or_update(
            sample_user.telegram_id, SessionState.LEARNING, {"step": "2"}
        )

        # Verify update
        session = repo.find_by_user(sample_user.telegram_id)
        assert session.state == SessionState.LEARNING  # type: ignore
        assert session.context_data["step"] == "2"  # type: ignore
