"""Repository pattern for data access."""

from loguru import logger
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

    def find_by_telegram_id(self, telegram_id: int) -> User | None:
        """Find user by telegram ID."""
        logger.debug("Finding user by telegram_id", telegram_id=telegram_id)
        user = self.db.query(User).filter(User.telegram_id == telegram_id).first()
        if user:
            logger.debug("User found", telegram_id=telegram_id)
        else:
            logger.debug("User not found", telegram_id=telegram_id)
        return user

    def create(
        self,
        telegram_id: int,
        username: str | None,
        skill_level: SkillLevel,
        learning_goal: LearningGoal,
    ) -> User:
        """Create new user."""
        logger.info(
            "Creating new user",
            telegram_id=telegram_id,
            username=username,
            skill_level=skill_level.value,
            learning_goal=learning_goal.value,
        )
        user = User(
            telegram_id=telegram_id,
            username=username,
            skill_level=skill_level,
            learning_goal=learning_goal,
        )
        self.db.add(user)
        self.db.flush()
        logger.info("User created successfully", telegram_id=telegram_id)
        return user

    def update_skill_level(self, telegram_id: int, skill_level: SkillLevel) -> None:
        """Update user skill level."""
        logger.debug("Updating skill level", telegram_id=telegram_id, skill_level=skill_level.value)
        user = self.find_by_telegram_id(telegram_id)
        if user:
            user.skill_level = skill_level  # type: ignore
            logger.info("Skill level updated", telegram_id=telegram_id, new_level=skill_level.value)
        else:
            logger.warning("Cannot update skill level: user not found", telegram_id=telegram_id)

    def update_assessment_score(self, telegram_id: int, score: int) -> None:
        """Update assessment score."""
        logger.debug("Updating assessment score", telegram_id=telegram_id, score=score)
        user = self.find_by_telegram_id(telegram_id)
        if user:
            user.assessment_score = score  # type: ignore
            logger.info("Assessment score updated", telegram_id=telegram_id, score=score)
        else:
            logger.warning("Cannot update assessment score: user not found", telegram_id=telegram_id)

    def update_current_lesson(self, telegram_id: int, lesson_id: int | None) -> None:
        """Update current lesson."""
        logger.debug("Updating current lesson", telegram_id=telegram_id, lesson_id=lesson_id)
        user = self.find_by_telegram_id(telegram_id)
        if user:
            user.current_lesson_id = lesson_id  # type: ignore
            logger.info("Current lesson updated", telegram_id=telegram_id, lesson_id=lesson_id)
        else:
            logger.warning("Cannot update current lesson: user not found", telegram_id=telegram_id)


class LessonRepository:
    """Repository for Lesson operations."""

    def __init__(self, db: Session) -> None:
        """Initialize repository."""
        self.db = db

    def find_by_id(self, lesson_id: int) -> Lesson | None:
        """Find lesson by ID."""
        logger.debug("Finding lesson by ID", lesson_id=lesson_id)
        lesson = self.db.query(Lesson).filter(Lesson.id == lesson_id).first()
        if lesson:
            logger.debug("Lesson found", lesson_id=lesson_id, title=lesson.title)
        else:
            logger.warning("Lesson not found", lesson_id=lesson_id)
        return lesson

    def find_by_skill_level(self, skill_level: SkillLevel) -> list[Lesson]:
        """Find lessons by skill level."""
        logger.debug("Finding lessons by skill level", skill_level=skill_level.value)
        lessons = (
            self.db.query(Lesson)
            .filter(Lesson.skill_level == skill_level)
            .order_by(Lesson.order_index)
            .all()
        )
        logger.debug("Lessons found", skill_level=skill_level.value, count=len(lessons))
        return lessons

    def find_next_lesson(
        self, skill_level: SkillLevel, current_order: int
    ) -> Lesson | None:
        """Find next lesson by order index."""
        logger.debug(
            "Finding next lesson",
            skill_level=skill_level.value,
            current_order=current_order,
        )
        lesson = (
            self.db.query(Lesson)
            .filter(Lesson.skill_level == skill_level, Lesson.order_index > current_order)
            .order_by(Lesson.order_index)
            .first()
        )
        if lesson:
            logger.debug("Next lesson found", lesson_id=lesson.id, title=lesson.title)
        else:
            logger.debug("No next lesson found", skill_level=skill_level.value)
        return lesson

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
    ) -> UserProgress | None:
        """Find progress by user and lesson."""
        logger.debug("Finding progress", user_id=user_id, lesson_id=lesson_id)
        progress = (
            self.db.query(UserProgress)
            .filter(UserProgress.user_id == user_id, UserProgress.lesson_id == lesson_id)
            .first()
        )
        if progress:
            logger.debug("Progress found", user_id=user_id, lesson_id=lesson_id, status=progress.status.value)  # type: ignore
        else:
            logger.debug("Progress not found", user_id=user_id, lesson_id=lesson_id)
        return progress

    def find_by_user(self, user_id: int) -> list[UserProgress]:
        """Find all progress records for user."""
        logger.debug("Finding all progress for user", user_id=user_id)
        progress_list = self.db.query(UserProgress).filter(UserProgress.user_id == user_id).all()
        logger.debug("Progress records found", user_id=user_id, count=len(progress_list))
        return progress_list

    def create(self, user_id: int, lesson_id: int) -> UserProgress:
        """Create progress record."""
        logger.info("Creating progress record", user_id=user_id, lesson_id=lesson_id)
        progress = UserProgress(
            user_id=user_id,
            lesson_id=lesson_id,
            status=LessonStatus.IN_PROGRESS,
        )
        self.db.add(progress)
        self.db.flush()
        logger.info("Progress record created", user_id=user_id, lesson_id=lesson_id)
        return progress

    def update_status(
        self, user_id: int, lesson_id: int, status: LessonStatus
    ) -> None:
        """Update progress status."""
        logger.debug("Updating progress status", user_id=user_id, lesson_id=lesson_id, status=status.value)
        progress = self.find_by_user_and_lesson(user_id, lesson_id)
        if progress:
            progress.status = status  # type: ignore
            logger.info("Progress status updated", user_id=user_id, lesson_id=lesson_id, status=status.value)
        else:
            logger.warning("Cannot update status: progress not found", user_id=user_id, lesson_id=lesson_id)

    def increment_attempts(self, user_id: int, lesson_id: int) -> None:
        """Increment attempt counter."""
        logger.debug("Incrementing attempts", user_id=user_id, lesson_id=lesson_id)
        progress = self.find_by_user_and_lesson(user_id, lesson_id)
        if progress:
            progress.attempts += 1  # type: ignore
            logger.info("Attempts incremented", user_id=user_id, lesson_id=lesson_id, attempts=progress.attempts)  # type: ignore
        else:
            logger.warning("Cannot increment attempts: progress not found", user_id=user_id, lesson_id=lesson_id)

    def update_score(self, user_id: int, lesson_id: int, score: int) -> None:
        """Update last score."""
        logger.debug("Updating score", user_id=user_id, lesson_id=lesson_id, score=score)
        progress = self.find_by_user_and_lesson(user_id, lesson_id)
        if progress:
            progress.last_score = score  # type: ignore
            logger.info("Score updated", user_id=user_id, lesson_id=lesson_id, score=score)
        else:
            logger.warning("Cannot update score: progress not found", user_id=user_id, lesson_id=lesson_id)


class SessionRepository:
    """Repository for UserSession operations."""

    def __init__(self, db: Session) -> None:
        """Initialize repository."""
        self.db = db

    def find_by_user(self, user_id: int) -> UserSession | None:
        """Find session by user ID."""
        logger.debug("Finding session for user", user_id=user_id)
        session = (
            self.db.query(UserSession).filter(UserSession.user_id == user_id).first()
        )
        if session:
            logger.debug("Session found", user_id=user_id, state=session.state.value)  # type: ignore
        else:
            logger.debug("Session not found", user_id=user_id)
        return session

    def create_or_update(
        self, user_id: int, state: SessionState, context_data: dict
    ) -> UserSession:
        """Create or update session."""
        logger.debug("Creating/updating session", user_id=user_id, state=state.value)
        session = self.find_by_user(user_id)
        if session:
            logger.debug("Updating existing session", user_id=user_id)
            session.state = state  # type: ignore
            session.context_data = context_data  # type: ignore
        else:
            logger.info("Creating new session", user_id=user_id, state=state.value)
            session = UserSession(
                user_id=user_id, state=state, context_data=context_data
            )
            self.db.add(session)
        self.db.flush()
        logger.info("Session saved", user_id=user_id, state=state.value)
        return session

    def update_context(self, user_id: int, context_data: dict) -> None:
        """Update session context."""
        logger.debug("Updating session context", user_id=user_id)
        session = self.find_by_user(user_id)
        if session:
            session.context_data = context_data  # type: ignore
            logger.info("Session context updated", user_id=user_id)
        else:
            logger.warning("Cannot update context: session not found", user_id=user_id)
