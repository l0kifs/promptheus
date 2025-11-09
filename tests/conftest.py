"""Test configuration and fixtures."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from promptheus.data.async_repositories import (
    AsyncLessonRepository,
    AsyncProgressRepository,
    AsyncSessionRepository,
    AsyncUserRepository,
)
from promptheus.data.database import Base
from promptheus.data.models import LearningGoal, Lesson, SkillLevel, User


@pytest.fixture(scope="session")
def async_db_engine():
    """Create async in-memory SQLite engine for testing."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    return engine


@pytest.fixture(scope="session", autouse=True)
async def setup_async_db(async_db_engine):
    """Set up async database tables."""
    async with async_db_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with async_db_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await async_db_engine.dispose()


@pytest.fixture
async def async_db_session(async_db_engine):
    """Create async database session for testing."""
    async_session_local = async_sessionmaker(bind=async_db_engine)
    session = async_session_local()
    try:
        yield session
    finally:
        await session.close()


@pytest.fixture
async def async_user_repo(async_db_session: AsyncSession) -> AsyncUserRepository:
    """Create async user repository."""

    # Create a session maker that returns the test session
    def session_maker():
        return async_db_session

    return AsyncUserRepository(session_maker)  # type: ignore


@pytest.fixture
async def async_lesson_repo(async_db_session: AsyncSession) -> AsyncLessonRepository:
    """Create async lesson repository."""

    # Create a session maker that returns the test session
    def session_maker():
        return async_db_session

    return AsyncLessonRepository(session_maker)  # type: ignore


@pytest.fixture
async def async_progress_repo(async_db_session: AsyncSession) -> AsyncProgressRepository:
    """Create async progress repository."""

    # Create a session maker that returns the test session
    def session_maker():
        return async_db_session

    return AsyncProgressRepository(session_maker)  # type: ignore


@pytest.fixture
async def async_session_repo(async_db_session: AsyncSession) -> AsyncSessionRepository:
    """Create async session repository."""

    # Create a session maker that returns the test session
    def session_maker():
        return async_db_session

    return AsyncSessionRepository(session_maker)  # type: ignore


@pytest.fixture
async def async_sample_user(async_db_session: AsyncSession) -> User:
    """Create a sample user for async tests."""
    import random

    telegram_id = random.randint(100000, 999999)
    user = User(
        telegram_id=telegram_id,
        username="testuser",
        skill_level=SkillLevel.BEGINNER,
        learning_goal=LearningGoal.PROFESSIONAL,
        assessment_score=50,
    )
    async_db_session.add(user)
    await async_db_session.commit()
    await async_db_session.refresh(user)
    return user


@pytest.fixture
async def async_sample_user_id(async_db_session: AsyncSession) -> int:
    """Create a sample user ID for async tests."""
    import random

    telegram_id = random.randint(100000, 999999)
    user = User(
        telegram_id=telegram_id,
        username="testuser",
        skill_level=SkillLevel.BEGINNER,
        learning_goal=LearningGoal.PROFESSIONAL,
        assessment_score=50,
    )
    async_db_session.add(user)
    await async_db_session.commit()
    return telegram_id


@pytest.fixture
async def async_sample_lesson(async_db_session: AsyncSession) -> Lesson:
    """Create a sample lesson for async tests."""
    import random

    title = f"Async Test Lesson {random.randint(10000, 99999)}"
    slug = f"async-test-lesson-{random.randint(10000, 99999)}"
    position = random.randint(1000, 9999)  # Use random position to avoid conflicts
    lesson = Lesson(
        title=title,
        skill_level=SkillLevel.BEGINNER,
        slug=slug,
        position=position,
        tags=["test", "beginner"],
        theory_content={"sections": [{"content": "Test theory"}]},
        examples={"comparisons": [{"bad": "Bad example", "good": "Good example"}]},
        exercises={"scenarios": [{"scenario": "Test scenario", "task": "Test task"}]},
    )
    async_db_session.add(lesson)
    await async_db_session.commit()
    await async_db_session.refresh(lesson)
    return lesson


@pytest.fixture
async def async_sample_lesson_id(async_db_session: AsyncSession) -> int:
    """Create a sample lesson ID for async tests."""
    import random

    title = f"Async Test Lesson {random.randint(10000, 99999)}"
    slug = f"async-test-lesson-{random.randint(10000, 99999)}"
    position = random.randint(1000, 9999)  # Use random position to avoid conflicts
    lesson = Lesson(
        title=title,
        skill_level=SkillLevel.BEGINNER,
        slug=slug,
        position=position,
        tags=["test", "beginner"],
        theory_content={"sections": [{"content": "Test theory"}]},
        examples={"comparisons": [{"bad": "Bad example", "good": "Good example"}]},
        exercises={"scenarios": [{"scenario": "Test scenario", "task": "Test task"}]},
    )
    async_db_session.add(lesson)
    await async_db_session.commit()
    await async_db_session.refresh(lesson)
    return lesson.id  # type: ignore


@pytest.fixture
async def async_multiple_lessons(async_db_session: AsyncSession) -> list[Lesson]:
    """Create multiple lessons for async testing."""
    import random

    lessons = []
    for i in range(1, 4):
        title = f"Async Test Lesson {random.randint(10000, 99999)} {i}"
        slug = f"async-test-lesson-{random.randint(10000, 99999)}-{i}"
        position = random.randint(10000, 20000) + i  # Use random position to avoid conflicts
        lesson = Lesson(
            title=title,
            skill_level=SkillLevel.BEGINNER,
            slug=slug,
            position=position,
            tags=["test", "beginner"],
            theory_content={"sections": [{"content": "Test theory"}]},
            examples={"comparisons": [{"bad": "Bad example", "good": "Good example"}]},
            exercises={"scenarios": [{"scenario": "Test scenario", "task": "Test task"}]},
        )
        lessons.append(lesson)
    async_db_session.add_all(lessons)
    await async_db_session.commit()
    for lesson in lessons:
        await async_db_session.refresh(lesson)
    return lessons
