"""In-memory cache for lesson content with thread-safe operations."""

import asyncio
from typing import Any

from loguru import logger

from promptheus.data.models import SkillLevel
from promptheus.data.schemas import LessonContentSchema


class LessonCache:
    """Thread-safe in-memory cache for lessons.

    Uses nested dictionary structure: {skill_level: {slug: lesson}}
    All operations are protected by asyncio.Lock for thread safety.
    """

    def __init__(self) -> None:
        """Initialize empty cache with lock."""
        self._cache: dict[str, dict[str, LessonContentSchema]] = {}
        self._lock = asyncio.Lock()
        self._stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
            "clears": 0,
            "reloads": 0,
        }
        logger.debug("LessonCache initialized")

    async def get(self, skill_level: SkillLevel, slug: str) -> LessonContentSchema | None:
        """Get lesson from cache.

        Args:
            skill_level: Skill level of the lesson
            slug: Slug identifier of the lesson

        Returns:
            Cached lesson if found, None otherwise
        """
        async with self._lock:
            skill_dict = self._cache.get(skill_level.value, {})
            lesson = skill_dict.get(slug)

            if lesson is not None:
                self._stats["hits"] += 1
                logger.debug("Cache hit", skill_level=skill_level.value, slug=slug)
            else:
                self._stats["misses"] += 1
                logger.debug("Cache miss", skill_level=skill_level.value, slug=slug)

            return lesson

    async def set(self, skill_level: SkillLevel, slug: str, lesson: LessonContentSchema) -> None:
        """Store lesson in cache.

        Args:
            skill_level: Skill level of the lesson
            slug: Slug identifier of the lesson
            lesson: Lesson content to cache
        """
        async with self._lock:
            if skill_level.value not in self._cache:
                self._cache[skill_level.value] = {}

            self._cache[skill_level.value][slug] = lesson
            self._stats["sets"] += 1

            logger.debug(
                "Lesson cached",
                skill_level=skill_level.value,
                slug=slug,
                title=lesson.title,
            )

    async def delete(self, skill_level: SkillLevel, slug: str) -> bool:
        """Remove lesson from cache.

        Args:
            skill_level: Skill level of the lesson
            slug: Slug identifier of the lesson

        Returns:
            True if lesson was found and removed, False otherwise
        """
        async with self._lock:
            skill_dict = self._cache.get(skill_level.value, {})
            if slug in skill_dict:
                del skill_dict[slug]
                self._stats["deletes"] += 1

                # Clean up empty skill level dict
                if not skill_dict:
                    del self._cache[skill_level.value]

                logger.debug("Lesson removed from cache", skill_level=skill_level.value, slug=slug)
                return True

            logger.debug("Lesson not found in cache", skill_level=skill_level.value, slug=slug)
            return False

    async def clear(self) -> int:
        """Clear all lessons from cache.

        Returns:
            Number of lessons that were cleared
        """
        async with self._lock:
            total_cleared = sum(len(skill_dict) for skill_dict in self._cache.values())
            self._cache.clear()
            self._stats["clears"] += 1

            logger.info("Cache cleared", lessons_cleared=total_cleared)
            return total_cleared

    async def reload_skill_level(
        self, skill_level: SkillLevel, lessons: dict[str, LessonContentSchema]
    ) -> int:
        """Reload all lessons for a skill level atomically.

        Args:
            skill_level: Skill level to reload
            lessons: Dictionary of {slug: lesson} for the skill level

        Returns:
            Number of lessons loaded
        """
        async with self._lock:
            self._cache[skill_level.value] = lessons.copy()
            count = len(lessons)
            self._stats["reloads"] += 1

            logger.info(
                "Skill level reloaded",
                skill_level=skill_level.value,
                lessons_loaded=count,
            )
            return count

    async def get_stats(self) -> dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        async with self._lock:
            stats = self._stats.copy()
            total_cached = sum(len(skill_dict) for skill_dict in self._cache.values())
            stats["total_cached"] = total_cached
            stats["skill_levels"] = list(self._cache.keys())

            # Calculate hit rate
            total_requests = stats["hits"] + stats["misses"]
            stats["hit_rate"] = (
                (stats["hits"] / total_requests * 100) if total_requests > 0 else 0.0
            )

            return stats

    async def get_all_slugs(self, skill_level: SkillLevel) -> list[str]:
        """Get all cached lesson slugs for a skill level.

        Args:
            skill_level: Skill level to query

        Returns:
            List of cached lesson slugs
        """
        async with self._lock:
            skill_dict = self._cache.get(skill_level.value, {})
            return list(skill_dict.keys())

    async def is_empty(self) -> bool:
        """Check if cache is empty.

        Returns:
            True if cache contains no lessons
        """
        async with self._lock:
            return not any(self._cache.values())
