"""Learning flow orchestration."""

from loguru import logger

from promptheus.data.async_repositories import (
    AsyncLessonRepository,
    AsyncSessionRepository,
    AsyncUserRepository,
)
from promptheus.data.models import SessionState, SkillLevel


class LearningFlowOrchestrator:
    """Orchestrator for learning flows."""

    def __init__(
        self,
        user_repo: AsyncUserRepository,
        lesson_repo: AsyncLessonRepository,
        session_repo: AsyncSessionRepository,
    ) -> None:
        """Initialize orchestrator."""
        self.user_repo = user_repo
        self.lesson_repo = lesson_repo
        self.session_repo = session_repo

    async def get_personalized_path(
        self, user_id: int, skill_level: SkillLevel
    ) -> list[dict[str, str | int]]:
        """Get personalized lesson path for user."""
        logger.info("Getting personalized path", user_id=user_id, skill_level=skill_level.value)
        lessons = await self.lesson_repo.find_by_skill_level(skill_level)
        logger.info("Personalized path generated", user_id=user_id, lesson_count=len(lessons))

        return [
            {
                "id": int(lesson.id),  # type: ignore
                "title": str(lesson.title),
                "order": int(lesson.order_index),  # type: ignore
            }
            for lesson in lessons
        ]

    async def get_next_lesson(
        self, user_id: int, current_lesson_id: int
    ) -> dict[str, str | int] | None:
        """Get next lesson in sequence."""
        logger.debug("Getting next lesson", user_id=user_id, current_lesson_id=current_lesson_id)
        user = await self.user_repo.find_by_telegram_id(user_id)
        if not user:
            logger.warning("Cannot get next lesson: user not found", user_id=user_id)
            return None

        current_lesson = await self.lesson_repo.find_by_id(current_lesson_id)
        if not current_lesson:
            logger.warning(
                "Cannot get next lesson: current lesson not found", lesson_id=current_lesson_id
            )
            return None

        next_lesson = await self.lesson_repo.find_next_lesson(
            user.skill_level,
            current_lesson.order_index,  # type: ignore
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

    async def update_session_state(self, user_id: int, state: SessionState, context: dict) -> None:
        """Update user session state."""
        logger.debug("Updating session state", user_id=user_id, state=state.value)
        await self.session_repo.create_or_update(user_id, state, context)

    async def save_session_context(self, user_id: int, context: dict) -> None:
        """Save session context without changing state."""
        logger.debug("Saving session context", user_id=user_id)
        session = await self.session_repo.find_by_user(user_id)
        if session:
            await self.session_repo.update_context(user_id, context)
        else:
            # Create new session with default state if none exists
            await self.session_repo.create_or_update(user_id, SessionState.ONBOARDING, context)

    async def get_session_context(self, user_id: int) -> dict:
        """Get current session context."""
        logger.debug("Getting session context", user_id=user_id)
        session = await self.session_repo.find_by_user(user_id)
        if session:
            return session.context_data  # type: ignore
        logger.debug("No session found", user_id=user_id)
        return {}
