from datetime import datetime

from loguru import logger
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from promptheus.data.models import (
    LearningGoal,
    Lesson,
    LessonStatus,
    LessonVersion,
    SessionState,
    SkillLevel,
    User,
    UserProgress,
    UserSession,
)


class AsyncUserRepository:
    """Async repository for User operations."""

    def __init__(self, session_maker: async_sessionmaker[AsyncSession]) -> None:
        """Initialize repository."""
        self.session_maker = session_maker

    async def find_by_telegram_id(self, telegram_id: int) -> User | None:
        """Find user by telegram ID."""
        logger.debug("Finding user by telegram_id", telegram_id=telegram_id)
        async with self.session_maker() as session:
            stmt = select(User).where(User.telegram_id == telegram_id)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()
            if user:
                logger.debug("User found", telegram_id=telegram_id)
            else:
                logger.debug("User not found", telegram_id=telegram_id)
            return user

    async def create(
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
        async with self.session_maker() as session:
            user = User(
                telegram_id=telegram_id,
                username=username,
                skill_level=skill_level,
                learning_goal=learning_goal,
            )
            session.add(user)
            await session.flush()
            await session.commit()
            await session.refresh(user)  # Refresh to ensure all attributes are loaded
            logger.info("User created successfully", telegram_id=telegram_id)
            return user

    async def update_skill_level(self, telegram_id: int, skill_level: SkillLevel) -> None:
        """Update user skill level."""
        logger.debug("Updating skill level", telegram_id=telegram_id, skill_level=skill_level.value)
        async with self.session_maker() as session:
            user = await self._find_by_telegram_id_in_session(session, telegram_id)
            if user:
                user.skill_level = skill_level  # type: ignore
                await session.commit()
                logger.info(
                    "Skill level updated", telegram_id=telegram_id, new_level=skill_level.value
                )
            else:
                logger.warning("Cannot update skill level: user not found", telegram_id=telegram_id)

    async def update_assessment_score(self, telegram_id: int, score: int) -> None:
        """Update assessment score."""
        logger.debug("Updating assessment score", telegram_id=telegram_id, score=score)
        async with self.session_maker() as session:
            user = await self._find_by_telegram_id_in_session(session, telegram_id)
            if user:
                user.assessment_score = score  # type: ignore
                await session.commit()
                logger.info("Assessment score updated", telegram_id=telegram_id, score=score)
            else:
                logger.warning(
                    "Cannot update assessment score: user not found", telegram_id=telegram_id
                )

    async def update_current_lesson(self, telegram_id: int, lesson_id: int | None) -> None:
        """Update current lesson."""
        logger.debug("Updating current lesson", telegram_id=telegram_id, lesson_id=lesson_id)
        async with self.session_maker() as session:
            user = await self._find_by_telegram_id_in_session(session, telegram_id)
            if user:
                user.current_lesson_id = lesson_id  # type: ignore
                await session.commit()
                logger.info("Current lesson updated", telegram_id=telegram_id, lesson_id=lesson_id)
            else:
                logger.warning(
                    "Cannot update current lesson: user not found", telegram_id=telegram_id
                )

    async def _find_by_telegram_id_in_session(
        self, session: AsyncSession, telegram_id: int
    ) -> User | None:
        """Find user by telegram ID within an existing session."""
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()


class AsyncLessonRepository:
    """Async repository for Lesson operations."""

    def __init__(self, session_maker: async_sessionmaker[AsyncSession]) -> None:
        """Initialize repository."""
        self.session_maker = session_maker

    async def find_by_id(self, lesson_id: int) -> Lesson | None:
        """Find lesson by ID."""
        logger.debug("Finding lesson by ID", lesson_id=lesson_id)
        async with self.session_maker() as session:
            stmt = select(Lesson).where(Lesson.id == lesson_id)
            result = await session.execute(stmt)
            lesson = result.scalar_one_or_none()
            if lesson:
                logger.debug("Lesson found", lesson_id=lesson_id, title=lesson.title)
            else:
                logger.warning("Lesson not found", lesson_id=lesson_id)
            return lesson

    async def find_by_slug(self, skill_level: SkillLevel, slug: str) -> Lesson | None:
        """Find lesson by skill level and slug."""
        logger.debug("Finding lesson by slug", skill_level=skill_level.value, slug=slug)
        async with self.session_maker() as session:
            stmt = select(Lesson).where(Lesson.skill_level == skill_level, Lesson.slug == slug)
            result = await session.execute(stmt)
            lesson = result.scalar_one_or_none()
            if lesson:
                logger.debug("Lesson found", lesson_id=lesson.id, title=lesson.title)
            else:
                logger.debug("Lesson not found", skill_level=skill_level.value, slug=slug)
            return lesson

    async def find_by_skill_level(self, skill_level: SkillLevel) -> list[Lesson]:
        """Find lessons by skill level."""
        logger.debug("Finding lessons by skill level", skill_level=skill_level.value)
        async with self.session_maker() as session:
            stmt = select(Lesson).where(Lesson.skill_level == skill_level).order_by(Lesson.position)
            result = await session.execute(stmt)
            lessons = result.scalars().all()
            logger.debug("Lessons found", skill_level=skill_level.value, count=len(lessons))
            return list(lessons)

    async def find_next_lesson(
        self, skill_level: SkillLevel, current_position: int
    ) -> Lesson | None:
        """Find next lesson by position."""
        logger.debug(
            "Finding next lesson",
            skill_level=skill_level.value,
            current_position=current_position,
        )
        async with self.session_maker() as session:
            stmt = (
                select(Lesson)
                .where(Lesson.skill_level == skill_level, Lesson.position > current_position)
                .order_by(Lesson.position)
            )
            result = await session.execute(stmt)
            lesson = result.scalars().first()
            if lesson:
                logger.debug("Next lesson found", lesson_id=lesson.id, title=lesson.title)
            else:
                logger.debug("No next lesson found", skill_level=skill_level.value)
            return lesson

    async def create(
        self,
        title: str,
        skill_level: SkillLevel,
        slug: str,
        position: int,
        tags: list[str],
        theory_content: dict,
        examples: dict,
        exercises: dict,
    ) -> Lesson:
        """Create new lesson."""
        async with self.session_maker() as session:
            lesson = Lesson(
                title=title,
                skill_level=skill_level,
                slug=slug,
                position=position,
                tags=tags,
                theory_content=theory_content,
                examples=examples,
                exercises=exercises,
            )
            session.add(lesson)
            await session.flush()
            await session.commit()
            await session.refresh(lesson)  # Refresh to ensure all attributes are loaded
            return lesson

    async def upsert_lesson(
        self,
        title: str,
        skill_level: SkillLevel,
        slug: str,
        position: int,
        tags: list[str],
        theory_content: dict,
        examples: dict,
        exercises: dict,
    ) -> Lesson:
        """Create or update lesson by title (upsert operation)."""
        logger.debug(
            "Upserting lesson",
            title=title,
            skill_level=skill_level.value,
            slug=slug,
            position=position,
        )

        async with self.session_maker() as session:
            # Use insert with on_conflict_do_update for upsert
            stmt = (
                insert(Lesson)
                .values(
                    title=title,
                    skill_level=skill_level,
                    slug=slug,
                    position=position,
                    tags=tags,
                    theory_content=theory_content,
                    examples=examples,
                    exercises=exercises,
                    updated_at=datetime.utcnow(),
                )
                .on_conflict_do_update(
                    index_elements=["title"],  # Conflict on title (assuming title is unique)
                    set_={
                        "skill_level": skill_level,
                        "slug": slug,
                        "position": position,
                        "tags": tags,
                        "theory_content": theory_content,
                        "examples": examples,
                        "exercises": exercises,
                        "updated_at": datetime.utcnow(),
                    },
                )
            )

            await session.execute(stmt)
            await session.commit()

            # Fetch the upserted lesson
            result = await session.execute(select(Lesson).where(Lesson.title == title))
            lesson = result.scalar_one()
            logger.debug("Lesson upserted successfully", title=title, id=lesson.id)
            return lesson


class AsyncProgressRepository:
    """Async repository for UserProgress operations."""

    def __init__(self, session_maker: async_sessionmaker[AsyncSession]) -> None:
        """Initialize repository."""
        self.session_maker = session_maker

    async def find_by_user_and_lesson(self, user_id: int, lesson_id: int) -> UserProgress | None:
        """Find progress by user and lesson."""
        logger.debug("Finding progress", user_id=user_id, lesson_id=lesson_id)
        async with self.session_maker() as session:
            stmt = select(UserProgress).where(
                UserProgress.user_id == user_id, UserProgress.lesson_id == lesson_id
            )
            result = await session.execute(stmt)
            progress = result.scalar_one_or_none()
            if progress:
                logger.debug(
                    "Progress found",
                    user_id=user_id,
                    lesson_id=lesson_id,
                    status=progress.status.value,
                )  # type: ignore
            else:
                logger.debug("Progress not found", user_id=user_id, lesson_id=lesson_id)
            return progress

    async def find_by_user(self, user_id: int) -> list[UserProgress]:
        """Find all progress records for user."""
        logger.debug("Finding all progress for user", user_id=user_id)
        async with self.session_maker() as session:
            stmt = select(UserProgress).where(UserProgress.user_id == user_id)
            result = await session.execute(stmt)
            progress_list = result.scalars().all()
            logger.debug("Progress records found", user_id=user_id, count=len(progress_list))
            return list(progress_list)

    async def create(self, user_id: int, lesson_id: int) -> UserProgress:
        """Create progress record."""
        logger.info("Creating progress record", user_id=user_id, lesson_id=lesson_id)
        async with self.session_maker() as session:
            progress = UserProgress(
                user_id=user_id,
                lesson_id=lesson_id,
                status=LessonStatus.NOT_STARTED,  # Changed from IN_PROGRESS to NOT_STARTED
            )
            session.add(progress)
            await session.flush()
            await session.commit()
            await session.refresh(progress)  # Refresh to ensure all attributes are loaded
            logger.info("Progress record created", user_id=user_id, lesson_id=lesson_id)
            return progress

    async def update_status(self, user_id: int, lesson_id: int, status: LessonStatus) -> None:
        """Update progress status."""
        logger.debug(
            "Updating progress status", user_id=user_id, lesson_id=lesson_id, status=status.value
        )
        async with self.session_maker() as session:
            progress = await self._find_by_user_and_lesson_in_session(session, user_id, lesson_id)
            if progress:
                progress.status = status  # type: ignore
                await session.commit()
                logger.info(
                    "Progress status updated",
                    user_id=user_id,
                    lesson_id=lesson_id,
                    status=status.value,
                )
            else:
                logger.warning(
                    "Cannot update status: progress not found", user_id=user_id, lesson_id=lesson_id
                )

    async def increment_attempts(self, user_id: int, lesson_id: int) -> None:
        """Increment attempt counter."""
        logger.debug("Incrementing attempts", user_id=user_id, lesson_id=lesson_id)
        async with self.session_maker() as session:
            progress = await self._find_by_user_and_lesson_in_session(session, user_id, lesson_id)
            if progress:
                progress.attempts += 1  # type: ignore
                attempts = progress.attempts  # Store the value to avoid lazy loading in logging
                await session.commit()
                logger.info(
                    "Attempts incremented",
                    user_id=user_id,
                    lesson_id=lesson_id,
                    attempts=attempts,
                )
            else:
                logger.warning(
                    "Cannot increment attempts: progress not found",
                    user_id=user_id,
                    lesson_id=lesson_id,
                )

    async def update_score(self, user_id: int, lesson_id: int, score: int) -> None:
        """Update last score."""
        logger.debug("Updating score", user_id=user_id, lesson_id=lesson_id, score=score)
        async with self.session_maker() as session:
            progress = await self._find_by_user_and_lesson_in_session(session, user_id, lesson_id)
            if progress:
                progress.last_score = score  # type: ignore
                await session.commit()
                logger.info("Score updated", user_id=user_id, lesson_id=lesson_id, score=score)
            else:
                logger.warning(
                    "Cannot update score: progress not found", user_id=user_id, lesson_id=lesson_id
                )

    async def update_completed_at(
        self, user_id: int, lesson_id: int, completed_at: datetime
    ) -> None:
        """Update completed_at timestamp."""
        logger.debug(
            "Updating completed_at", user_id=user_id, lesson_id=lesson_id, completed_at=completed_at
        )
        async with self.session_maker() as session:
            progress = await self._find_by_user_and_lesson_in_session(session, user_id, lesson_id)
            if progress:
                progress.completed_at = completed_at  # type: ignore
                await session.commit()
                logger.info(
                    "Completed_at updated",
                    user_id=user_id,
                    lesson_id=lesson_id,
                    completed_at=completed_at,
                )
            else:
                logger.warning(
                    "Cannot update completed_at: progress not found",
                    user_id=user_id,
                    lesson_id=lesson_id,
                )

    async def _find_by_user_and_lesson_in_session(
        self, session: AsyncSession, user_id: int, lesson_id: int
    ) -> UserProgress | None:
        """Find progress by user and lesson within an existing session."""
        stmt = select(UserProgress).where(
            UserProgress.user_id == user_id, UserProgress.lesson_id == lesson_id
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()


class AsyncSessionRepository:
    """Async repository for UserSession operations."""

    def __init__(self, session_maker: async_sessionmaker[AsyncSession]) -> None:
        """Initialize repository."""
        self.session_maker = session_maker

    async def find_by_user(self, user_id: int) -> UserSession | None:
        """Find session by user ID."""
        logger.debug("Finding session for user", user_id=user_id)
        async with self.session_maker() as session:
            stmt = select(UserSession).where(UserSession.user_id == user_id)
            result = await session.execute(stmt)
            session_obj = result.scalar_one_or_none()
            if session_obj:
                logger.debug("Session found", user_id=user_id, state=session_obj.state.value)  # type: ignore
            else:
                logger.debug("Session not found", user_id=user_id)
            return session_obj

    async def create_or_update(
        self, user_id: int, state: SessionState, context_data: dict
    ) -> UserSession:
        """Create or update session."""
        logger.debug("Creating/updating session", user_id=user_id, state=state.value)
        async with self.session_maker() as session:
            session_obj = await self._find_by_user_in_session(session, user_id)
            if session_obj:
                logger.debug("Updating existing session", user_id=user_id)
                session_obj.state = state  # type: ignore
                session_obj.context_data = context_data  # type: ignore
            else:
                logger.info("Creating new session", user_id=user_id, state=state.value)
                session_obj = UserSession(user_id=user_id, state=state, context_data=context_data)
                session.add(session_obj)
            await session.flush()
            await session.commit()
            await session.refresh(session_obj)  # Refresh to ensure all attributes are loaded
            logger.info("Session saved", user_id=user_id, state=state.value)
            return session_obj

    async def update_context(self, user_id: int, context_data: dict) -> None:
        """Update session context."""
        logger.debug("Updating session context", user_id=user_id)
        async with self.session_maker() as session:
            session_obj = await self._find_by_user_in_session(session, user_id)
            if session_obj:
                session_obj.context_data = context_data  # type: ignore
                await session.commit()
                logger.info("Session context updated", user_id=user_id)
            else:
                logger.warning("Cannot update context: session not found", user_id=user_id)

    async def cleanup_old_sessions(self, days_old: int = 30) -> int:
        """Delete sessions older than specified days."""
        from datetime import datetime, timedelta

        logger.info("Starting session cleanup", days_old=days_old)
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        async with self.session_maker() as session:
            stmt = select(UserSession).where(UserSession.updated_at < cutoff_date)
            result = await session.execute(stmt)
            old_sessions = result.scalars().all()

            deleted_count = 0
            for session_obj in old_sessions:
                await session.delete(session_obj)
                deleted_count += 1

            if deleted_count > 0:
                await session.commit()
                logger.info("Old sessions cleaned up", count=deleted_count, cutoff_date=cutoff_date)
            else:
                logger.debug("No old sessions to clean up", cutoff_date=cutoff_date)

            return deleted_count

            return deleted_count

    async def _find_by_user_in_session(
        self, session: AsyncSession, user_id: int
    ) -> UserSession | None:
        """Find session by user ID within an existing session."""
        stmt = select(UserSession).where(UserSession.user_id == user_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()


class AsyncLessonVersionRepository:
    """Async repository for LessonVersion operations."""

    def __init__(self, session_maker: async_sessionmaker[AsyncSession]) -> None:
        """Initialize repository."""
        self.session_maker = session_maker

    async def create(
        self,
        lesson_id: int,
        version: str,
        content_hash: str,
        content_snapshot: dict,
        is_active: bool = False,
        created_by: str | None = None,
    ) -> LessonVersion:
        """Create new lesson version."""
        logger.info(
            "Creating lesson version",
            lesson_id=lesson_id,
            version=version,
            content_hash=content_hash[:16],
            is_active=is_active,
        )
        async with self.session_maker() as session:
            version_obj = LessonVersion(
                lesson_id=lesson_id,
                version=version,
                content_hash=content_hash,
                content_snapshot=content_snapshot,
                is_active=is_active,
                created_by=created_by,
            )
            session.add(version_obj)
            await session.flush()
            await session.commit()
            await session.refresh(version_obj)  # Refresh to ensure all attributes are loaded
            logger.info("Lesson version created", version_id=version_obj.id, lesson_id=lesson_id)
            return version_obj

    async def find_by_lesson_and_version(
        self, lesson_id: int, version: str
    ) -> LessonVersion | None:
        """Find version by lesson ID and version string."""
        logger.debug("Finding version", lesson_id=lesson_id, version=version)
        async with self.session_maker() as session:
            stmt = select(LessonVersion).where(
                LessonVersion.lesson_id == lesson_id, LessonVersion.version == version
            )
            result = await session.execute(stmt)
            version_obj = result.scalar_one_or_none()
            if version_obj:
                logger.debug("Version found", version_id=version_obj.id)
            else:
                logger.debug("Version not found", lesson_id=lesson_id, version=version)
            return version_obj

    async def find_active_by_lesson(self, lesson_id: int) -> LessonVersion | None:
        """Find active version for a lesson."""
        logger.debug("Finding active version", lesson_id=lesson_id)
        async with self.session_maker() as session:
            stmt = select(LessonVersion).where(
                LessonVersion.lesson_id == lesson_id, LessonVersion.is_active.is_(True)
            )
            result = await session.execute(stmt)
            version_obj = result.scalar_one_or_none()
            if version_obj:
                logger.debug(
                    "Active version found", version_id=version_obj.id, version=version_obj.version
                )
            else:
                logger.debug("No active version found", lesson_id=lesson_id)
            return version_obj

    async def find_all_by_lesson(self, lesson_id: int) -> list[LessonVersion]:
        """Find all versions for a lesson, ordered by creation time."""
        logger.debug("Finding all versions for lesson", lesson_id=lesson_id)
        async with self.session_maker() as session:
            stmt = (
                select(LessonVersion)
                .where(LessonVersion.lesson_id == lesson_id)
                .order_by(LessonVersion.created_at.desc())
            )
            result = await session.execute(stmt)
            versions = result.scalars().all()
            logger.debug("Versions found", lesson_id=lesson_id, count=len(versions))
            return list(versions)

    async def update_active_status(self, version_id: int, is_active: bool) -> None:
        """Update the active status of a version."""
        logger.debug("Updating active status", version_id=version_id, is_active=is_active)
        async with self.session_maker() as session:
            version_obj = await self._find_by_id_in_session(session, version_id)
            if version_obj:
                version_obj.is_active = is_active  # type: ignore
                await session.commit()
                logger.info("Active status updated", version_id=version_id, is_active=is_active)
            else:
                logger.warning(
                    "Cannot update active status: version not found", version_id=version_id
                )

    async def deactivate_other_versions(
        self, lesson_id: int, keep_version_id: int | None = None
    ) -> None:
        """Deactivate all versions for a lesson except the specified one."""
        logger.debug(
            "Deactivating other versions", lesson_id=lesson_id, keep_version_id=keep_version_id
        )
        async with self.session_maker() as session:
            # First, set all versions for this lesson to inactive
            stmt = (
                select(LessonVersion)
                .where(LessonVersion.lesson_id == lesson_id)
                .where(LessonVersion.is_active.is_(True))
            )
            result = await session.execute(stmt)
            active_versions = result.scalars().all()

            for version_obj in active_versions:
                if keep_version_id is None or version_obj.id != keep_version_id:
                    version_obj.is_active = False  # type: ignore
                    logger.debug("Deactivated version", version_id=version_obj.id)

            if active_versions:
                await session.commit()
                logger.info(
                    "Deactivated versions",
                    lesson_id=lesson_id,
                    deactivated_count=len(active_versions) - (1 if keep_version_id else 0),
                )

    async def _find_by_id_in_session(
        self, session: AsyncSession, version_id: int
    ) -> LessonVersion | None:
        """Find version by ID within an existing session."""
        stmt = select(LessonVersion).where(LessonVersion.id == version_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()
