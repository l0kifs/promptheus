"""Learning flow orchestration."""

from loguru import logger
from sqlalchemy.orm import Session

from promptheus.data.models import SessionState, SkillLevel
from promptheus.data.repositories import (
    LessonRepository,
    SessionRepository,
    UserRepository,
)


class LearningFlowOrchestrator:
    """Orchestrator for learning flows."""

    def __init__(self, db: Session) -> None:
        """Initialize orchestrator."""
        self.user_repo = UserRepository(db)
        self.lesson_repo = LessonRepository(db)
        self.session_repo = SessionRepository(db)

    def get_personalized_path(
        self, user_id: int, skill_level: SkillLevel
    ) -> list[dict[str, str | int]]:
        """Get personalized lesson path for user."""
        logger.info("Getting personalized path", user_id=user_id, skill_level=skill_level.value)
        lessons = self.lesson_repo.find_by_skill_level(skill_level)
        logger.info("Personalized path generated", user_id=user_id, lesson_count=len(lessons))

        return [
            {
                "id": int(lesson.id),  # type: ignore
                "title": str(lesson.title),
                "order": int(lesson.order_index),  # type: ignore
            }
            for lesson in lessons
        ]

    def get_next_lesson(
        self, user_id: int, current_lesson_id: int
    ) -> dict[str, str | int] | None:
        """Get next lesson in sequence."""
        logger.debug("Getting next lesson", user_id=user_id, current_lesson_id=current_lesson_id)
        user = self.user_repo.find_by_telegram_id(user_id)
        if not user:
            logger.warning("Cannot get next lesson: user not found", user_id=user_id)
            return None

        current_lesson = self.lesson_repo.find_by_id(current_lesson_id)
        if not current_lesson:
            logger.warning("Cannot get next lesson: current lesson not found", lesson_id=current_lesson_id)
            return None

        next_lesson = self.lesson_repo.find_next_lesson(
            user.skill_level, current_lesson.order_index  # type: ignore
        )

        if next_lesson:
            logger.info("Next lesson found", user_id=user_id, next_lesson_id=next_lesson.id)
            return {
                "id": int(next_lesson.id),  # type: ignore
                "title": str(next_lesson.title),
                "order": int(next_lesson.order_index),  # type: ignore
            }

        logger.info("No next lesson found", user_id=user_id)
        return None

    def update_session_state(
        self, user_id: int, state: SessionState, context: dict
    ) -> None:
        """Update user session state."""
        logger.debug("Updating session state", user_id=user_id, state=state.value)
        self.session_repo.create_or_update(user_id, state, context)

    def get_session_context(self, user_id: int) -> dict:
        """Get current session context."""
        logger.debug("Getting session context", user_id=user_id)
        session = self.session_repo.find_by_user(user_id)
        if session:
            return session.context_data  # type: ignore
        logger.debug("No session found", user_id=user_id)
        return {}
