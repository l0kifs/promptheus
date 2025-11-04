"""Test configuration and fixtures."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from promptheus.data.database import Base
from promptheus.data.models import LearningGoal, Lesson, SkillLevel, User


@pytest.fixture(scope="session")
def db_engine():
    """Create in-memory SQLite engine for testing."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})

    # Create all tables
    Base.metadata.create_all(engine)

    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def db_session(db_engine):
    """Create database session for testing."""
    session_local = sessionmaker(bind=db_engine)
    session = session_local()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def sample_user(db_session: Session) -> User:
    """Create a sample user."""
    import random

    telegram_id = random.randint(100000, 999999)
    user = User(
        telegram_id=telegram_id,
        username="testuser",
        skill_level=SkillLevel.BEGINNER,
        learning_goal=LearningGoal.PROFESSIONAL,
        assessment_score=50,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def sample_lesson(db_session: Session) -> Lesson:
    """Create a sample lesson."""
    lesson = Lesson(
        title="Test Lesson",
        skill_level=SkillLevel.BEGINNER,
        order_index=1,
        tags=["test", "beginner"],
        theory_content={"sections": [{"content": "Test theory"}]},
        examples={"comparisons": [{"bad": "Bad example", "good": "Good example"}]},
        exercises={"scenarios": [{"scenario": "Test scenario", "task": "Test task"}]},
    )
    db_session.add(lesson)
    db_session.commit()
    db_session.refresh(lesson)
    return lesson


@pytest.fixture
def multiple_lessons(db_session: Session) -> list[Lesson]:
    """Create multiple lessons for testing."""
    lessons = [
        Lesson(
            title=f"Lesson {i}",
            skill_level=SkillLevel.BEGINNER,
            order_index=i,
            tags=["test"],
            theory_content={"sections": []},
            examples={"comparisons": []},
            exercises={"scenarios": []},
        )
        for i in range(1, 4)
    ]
    db_session.add_all(lessons)
    db_session.commit()
    for lesson in lessons:
        db_session.refresh(lesson)
    return lessons
