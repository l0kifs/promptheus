"""SQLAlchemy data models."""

import enum
from datetime import datetime

from sqlalchemy import (
    JSON,
    BigInteger,
    CheckConstraint,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from promptheus.data.database import Base


class SkillLevel(str, enum.Enum):
    """User skill level."""

    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class LearningGoal(str, enum.Enum):
    """User learning goal."""

    ACADEMIC = "academic"
    PROFESSIONAL = "professional"
    CREATIVE = "creative"


class LessonStatus(str, enum.Enum):
    """Lesson completion status."""

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class SessionState(str, enum.Enum):
    """User session state."""

    ONBOARDING = "onboarding"
    LEARNING = "learning"
    PRACTICING = "practicing"
    MENU = "menu"


class User(Base):
    """User model."""

    __tablename__ = "user"

    telegram_id = Column(BigInteger, primary_key=True, index=True)
    username = Column(String(255), nullable=True)
    skill_level = Column(Enum(SkillLevel), nullable=False)
    learning_goal = Column(Enum(LearningGoal), nullable=False)
    current_lesson_id = Column(Integer, ForeignKey("lesson.id"), nullable=True)
    assessment_score = Column(Integer, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        CheckConstraint(
            "assessment_score IS NULL OR (assessment_score >= 0 AND assessment_score <= 100)",
            name="check_assessment_score_range",
        ),
        Index("ix_user_created_at", "created_at"),
    )

    # Relationships
    current_lesson = relationship("Lesson", foreign_keys=[current_lesson_id])
    progress = relationship("UserProgress", back_populates="user", cascade="all, delete-orphan")
    session = relationship("UserSession", back_populates="user", uselist=False)


class Lesson(Base):
    """Lesson model."""

    __tablename__ = "lesson"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False, unique=True)
    skill_level = Column(Enum(SkillLevel), nullable=False, index=True)
    order_index = Column(Integer, nullable=False)
    tags = Column(JSON, nullable=False)
    theory_content = Column(JSON, nullable=False)
    examples = Column(JSON, nullable=False)
    exercises = Column(JSON, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("skill_level", "order_index", name="uq_lesson_skill_level_order_index"),
        Index("ix_lesson_skill_level_order_index", "skill_level", "order_index"),
    )

    # Relationships
    progress = relationship("UserProgress", back_populates="lesson")


class UserProgress(Base):
    """User progress model."""

    __tablename__ = "user_progress"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("user.telegram_id"), nullable=False, index=True)
    lesson_id = Column(Integer, ForeignKey("lesson.id"), nullable=False, index=True)
    status = Column(Enum(LessonStatus), nullable=False, default=LessonStatus.NOT_STARTED)
    attempts = Column(Integer, nullable=False, default=0)
    last_score = Column(Integer, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    __table_args__ = (
        UniqueConstraint("user_id", "lesson_id", name="uq_user_progress_user_lesson"),
        CheckConstraint(
            "last_score IS NULL OR (last_score >= 0 AND last_score <= 100)",
            name="check_last_score_range",
        ),
        Index("ix_user_progress_user_id_status", "user_id", "status"),
    )

    # Relationships
    user = relationship("User", back_populates="progress")
    lesson = relationship("Lesson", back_populates="progress")


class UserSession(Base):
    """User session model."""

    __tablename__ = "user_session"

    user_id = Column(BigInteger, ForeignKey("user.telegram_id"), primary_key=True)
    state = Column(Enum(SessionState), nullable=False)
    context_data = Column(JSON, nullable=False, default=dict)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (Index("ix_user_session_updated_at", "updated_at"),)

    # Relationships
    user = relationship("User", back_populates="session")
