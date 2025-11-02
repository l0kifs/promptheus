"""Learning flow orchestration."""

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
        lessons = self.lesson_repo.find_by_skill_level(skill_level)

        return [
            {
                "id": lesson.id,
                "title": lesson.title,
                "order": lesson.order_index,
            }
            for lesson in lessons
        ]

    def get_next_lesson(
        self, user_id: int, current_lesson_id: int
    ) -> dict[str, str | int] | None:
        """Get next lesson in sequence."""
        user = self.user_repo.find_by_telegram_id(user_id)
        if not user:
            return None

        current_lesson = self.lesson_repo.find_by_id(current_lesson_id)
        if not current_lesson:
            return None

        next_lesson = self.lesson_repo.find_next_lesson(
            user.skill_level, current_lesson.order_index  # type: ignore
        )

        if next_lesson:
            return {
                "id": next_lesson.id,
                "title": next_lesson.title,
                "order": next_lesson.order_index,
            }

        return None

    def update_session_state(
        self, user_id: int, state: SessionState, context: dict
    ) -> None:
        """Update user session state."""
        self.session_repo.create_or_update(user_id, state, context)

    def get_session_context(self, user_id: int) -> dict:
        """Get current session context."""
        session = self.session_repo.find_by_user(user_id)
        if session:
            return session.context_data  # type: ignore
        return {}
