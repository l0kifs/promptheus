"""Tests for data repositories."""

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from promptheus.data.async_repositories import (
    AsyncLessonRepository,
    AsyncProgressRepository,
    AsyncSessionRepository,
    AsyncUserRepository,
)
from promptheus.data.models import (
    LearningGoal,
    Lesson,
    LessonStatus,
    SessionState,
    SkillLevel,
    User,
)


class TestUserRepository:
    """Tests for UserRepository."""

    @pytest.fixture
    async def repo(self, async_db_session: AsyncSession):
        """Create user repository."""

        # Create a session maker that returns the test session
        def session_maker():
            return async_db_session

        return AsyncUserRepository(session_maker)  # type: ignore

    async def test_create_user(self, repo, async_db_session: AsyncSession):
        """Test creating a new user."""
        user = await repo.create(
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
        db_user = await async_db_session.scalar(select(User).where(User.telegram_id == 99999))
        assert db_user is not None

    async def test_find_by_telegram_id(self, repo, async_sample_user: User):
        """Test finding user by telegram ID."""
        user = await repo.find_by_telegram_id(async_sample_user.telegram_id)

        assert user is not None
        assert user.telegram_id == async_sample_user.telegram_id
        assert user.username == async_sample_user.username

    async def test_find_by_telegram_id_not_found(self, repo):
        """Test finding non-existent user."""
        import random

        non_existent_id = random.randint(1000000, 9999999)  # Use a very large random ID
        user = await repo.find_by_telegram_id(non_existent_id)

        assert user is None

    async def test_update_assessment_score(self, repo, async_sample_user_id: int):
        """Test updating assessment score."""
        await repo.update_assessment_score(async_sample_user_id, 85)

        user = await repo.find_by_telegram_id(async_sample_user_id)
        assert user is not None

        assert user.assessment_score == 85  # type: ignore


class TestLessonRepository:
    """Tests for LessonRepository."""

    @pytest.fixture
    async def repo(self, async_db_session: AsyncSession):
        """Create lesson repository."""

        # Create a session maker that returns the test session
        def session_maker():
            return async_db_session

        return AsyncLessonRepository(session_maker)  # type: ignore

    async def test_create_lesson(self, repo, async_db_session: AsyncSession):
        """Test creating a new lesson."""
        lesson = await repo.create(
            title="New Lesson",
            skill_level=SkillLevel.INTERMEDIATE,
            slug="new-lesson",
            position=10,
            tags=["test"],
            theory_content={"sections": []},
            examples={"comparisons": []},
            exercises={"scenarios": []},
        )

        assert lesson.title == "New Lesson"
        assert lesson.skill_level == SkillLevel.INTERMEDIATE
        assert lesson.slug == "new-lesson"
        assert lesson.position == 10

        # Verify in database
        db_lesson = await async_db_session.scalar(
            select(Lesson).where(Lesson.title == "New Lesson")
        )
        assert db_lesson is not None

    async def test_find_by_id(self, repo, async_sample_lesson: Lesson):
        """Test finding lesson by ID."""
        lesson = await repo.find_by_id(async_sample_lesson.id)

        assert lesson is not None
        assert lesson.title == async_sample_lesson.title  # type: ignore

    async def test_find_by_slug(self, repo, async_sample_lesson: Lesson):
        """Test finding lesson by slug and skill level."""
        lesson = await repo.find_by_slug(async_sample_lesson.skill_level, async_sample_lesson.slug)

        assert lesson is not None
        assert lesson.id == async_sample_lesson.id
        assert lesson.slug == async_sample_lesson.slug

    async def test_find_by_skill_level(self, repo, async_multiple_lessons):
        """Test finding lessons by skill level."""
        lessons = await repo.find_by_skill_level(SkillLevel.BEGINNER)

        # Should find at least the 3 fixture lessons plus any seeded lessons
        assert len(lessons) >= 3
        assert all(lesson.skill_level == SkillLevel.BEGINNER for lesson in lessons)

    async def test_find_next_lesson(self, repo, async_multiple_lessons):
        """Test finding next lesson in sequence."""
        # Sort the fixture lessons by position to find the expected next one
        sorted_lessons = sorted(async_multiple_lessons, key=lambda lesson: lesson.position)
        first_lesson = sorted_lessons[0]

        # Find the next lesson using the repo method
        next_lesson = await repo.find_next_lesson(SkillLevel.BEGINNER, first_lesson.position)

        if next_lesson:
            # The next lesson should have position > first_lesson.position
            assert next_lesson.position > first_lesson.position
            # The next lesson should be for BEGINNER skill level
            assert next_lesson.skill_level == SkillLevel.BEGINNER


class TestProgressRepository:
    """Tests for ProgressRepository."""

    @pytest.fixture
    async def repo(self, async_db_session: AsyncSession):
        """Create progress repository."""

        # Create a session maker that returns the test session
        def session_maker():
            return async_db_session

        return AsyncProgressRepository(session_maker)  # type: ignore

    async def test_create_progress(
        self, repo, async_sample_user_id: int, async_sample_lesson_id: int
    ):
        """Test creating progress record."""
        progress = await repo.create(async_sample_user_id, async_sample_lesson_id)

        assert progress.user_id == async_sample_user_id  # type: ignore
        assert progress.lesson_id == async_sample_lesson_id  # type: ignore
        assert progress.status == LessonStatus.NOT_STARTED

    async def test_find_by_user_and_lesson(
        self, repo, async_sample_user_id: int, async_sample_lesson_id: int
    ):
        """Test finding progress by user and lesson."""
        # Create progress first
        await repo.create(async_sample_user_id, async_sample_lesson_id)

        # Find it
        progress = await repo.find_by_user_and_lesson(async_sample_user_id, async_sample_lesson_id)

        assert progress is not None
        assert progress.user_id == async_sample_user_id  # type: ignore

    async def test_increment_attempts(
        self, repo, async_sample_user_id: int, async_sample_lesson_id: int
    ):
        """Test incrementing attempt counter."""
        await repo.create(async_sample_user_id, async_sample_lesson_id)

        await repo.increment_attempts(async_sample_user_id, async_sample_lesson_id)
        await repo.increment_attempts(async_sample_user_id, async_sample_lesson_id)

        progress = await repo.find_by_user_and_lesson(async_sample_user_id, async_sample_lesson_id)
        assert progress.attempts == 2  # type: ignore


class TestSessionRepository:
    """Tests for SessionRepository."""

    @pytest.fixture
    async def repo(self, async_db_session: AsyncSession):
        """Create session repository."""

        # Create a session maker that returns the test session
        def session_maker():
            return async_db_session

        return AsyncSessionRepository(session_maker)  # type: ignore

    async def test_create_session(self, repo, async_sample_user_id: int):
        """Test creating session."""
        context = {"step": "test"}
        session = await repo.create_or_update(
            async_sample_user_id, SessionState.ONBOARDING, context
        )

        assert session is not None

        assert session.user_id == async_sample_user_id  # type: ignore
        assert session.state == SessionState.ONBOARDING

    async def test_update_session(self, repo, async_sample_user_id: int):
        """Test updating existing session."""
        # Create session
        await repo.create_or_update(async_sample_user_id, SessionState.ONBOARDING, {"step": "1"})

        # Update it
        await repo.create_or_update(async_sample_user_id, SessionState.LEARNING, {"step": "2"})

        # Verify update
        session = await repo.find_by_user(async_sample_user_id)
        assert session is not None
        assert session.state == SessionState.LEARNING  # type: ignore
        assert session.context_data["step"] == "2"  # type: ignore
