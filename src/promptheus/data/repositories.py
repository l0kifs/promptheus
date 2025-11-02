"""Repository pattern for data access."""

from typing import Optional

from sqlalchemy.orm import Session

from promptheus.data.models import (
    Lesson,
    LessonStatus,
    LearningGoal,
    SessionState,
    SkillLevel,
    User,
    UserProgress,
    UserSession,
)


class UserRepository:
    """Repository for User operations."""

    def __init__(self, db: Session) -> None:
        """Initialize repository."""
        self.db = db

    def find_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """Find user by telegram ID."""
        return self.db.query(User).filter(User.telegram_id == telegram_id).first()

    def create(
        self,
        telegram_id: int,
        username: Optional[str],
        skill_level: SkillLevel,
        learning_goal: LearningGoal,
    ) -> User:
        """Create new user."""
        user = User(
            telegram_id=telegram_id,
            username=username,
            skill_level=skill_level,
            learning_goal=learning_goal,
        )
        self.db.add(user)
        self.db.flush()
        return user

    def update_skill_level(self, telegram_id: int, skill_level: SkillLevel) -> None:
        """Update user skill level."""
        user = self.find_by_telegram_id(telegram_id)
        if user:
            user.skill_level = skill_level

    def update_assessment_score(self, telegram_id: int, score: int) -> None:
        """Update assessment score."""
        user = self.find_by_telegram_id(telegram_id)
        if user:
            user.assessment_score = score

    def update_current_lesson(self, telegram_id: int, lesson_id: Optional[int]) -> None:
        """Update current lesson."""
        user = self.find_by_telegram_id(telegram_id)
        if user:
            user.current_lesson_id = lesson_id


class LessonRepository:
    """Repository for Lesson operations."""

    def __init__(self, db: Session) -> None:
        """Initialize repository."""
        self.db = db

    def find_by_id(self, lesson_id: int) -> Optional[Lesson]:
        """Find lesson by ID."""
        return self.db.query(Lesson).filter(Lesson.id == lesson_id).first()

    def find_by_skill_level(self, skill_level: SkillLevel) -> list[Lesson]:
        """Find lessons by skill level."""
        return (
            self.db.query(Lesson)
            .filter(Lesson.skill_level == skill_level)
            .order_by(Lesson.order_index)
            .all()
        )

    def find_next_lesson(
        self, skill_level: SkillLevel, current_order: int
    ) -> Optional[Lesson]:
        """Find next lesson by order index."""
        return (
            self.db.query(Lesson)
            .filter(Lesson.skill_level == skill_level, Lesson.order_index > current_order)
            .order_by(Lesson.order_index)
            .first()
        )

    def create(
        self,
        title: str,
        skill_level: SkillLevel,
        order_index: int,
        tags: list[str],
        theory_content: dict,
        examples: dict,
        exercises: dict,
    ) -> Lesson:
        """Create new lesson."""
        lesson = Lesson(
            title=title,
            skill_level=skill_level,
            order_index=order_index,
            tags=tags,
            theory_content=theory_content,
            examples=examples,
            exercises=exercises,
        )
        self.db.add(lesson)
        self.db.flush()
        return lesson


class ProgressRepository:
    """Repository for UserProgress operations."""

    def __init__(self, db: Session) -> None:
        """Initialize repository."""
        self.db = db

    def find_by_user_and_lesson(
        self, user_id: int, lesson_id: int
    ) -> Optional[UserProgress]:
        """Find progress by user and lesson."""
        return (
            self.db.query(UserProgress)
            .filter(UserProgress.user_id == user_id, UserProgress.lesson_id == lesson_id)
            .first()
        )

    def find_by_user(self, user_id: int) -> list[UserProgress]:
        """Find all progress records for user."""
        return self.db.query(UserProgress).filter(UserProgress.user_id == user_id).all()

    def create(self, user_id: int, lesson_id: int) -> UserProgress:
        """Create progress record."""
        progress = UserProgress(
            user_id=user_id,
            lesson_id=lesson_id,
            status=LessonStatus.IN_PROGRESS,
        )
        self.db.add(progress)
        self.db.flush()
        return progress

    def update_status(
        self, user_id: int, lesson_id: int, status: LessonStatus
    ) -> None:
        """Update progress status."""
        progress = self.find_by_user_and_lesson(user_id, lesson_id)
        if progress:
            progress.status = status

    def increment_attempts(self, user_id: int, lesson_id: int) -> None:
        """Increment attempt counter."""
        progress = self.find_by_user_and_lesson(user_id, lesson_id)
        if progress:
            progress.attempts += 1

    def update_score(self, user_id: int, lesson_id: int, score: int) -> None:
        """Update last score."""
        progress = self.find_by_user_and_lesson(user_id, lesson_id)
        if progress:
            progress.last_score = score


class SessionRepository:
    """Repository for UserSession operations."""

    def __init__(self, db: Session) -> None:
        """Initialize repository."""
        self.db = db

    def find_by_user(self, user_id: int) -> Optional[UserSession]:
        """Find session by user ID."""
        return (
            self.db.query(UserSession).filter(UserSession.user_id == user_id).first()
        )

    def create_or_update(
        self, user_id: int, state: SessionState, context_data: dict
    ) -> UserSession:
        """Create or update session."""
        session = self.find_by_user(user_id)
        if session:
            session.state = state
            session.context_data = context_data
        else:
            session = UserSession(
                user_id=user_id, state=state, context_data=context_data
            )
            self.db.add(session)
        self.db.flush()
        return session

    def update_context(self, user_id: int, context_data: dict) -> None:
        """Update session context."""
        session = self.find_by_user(user_id)
        if session:
            session.context_data = context_data
