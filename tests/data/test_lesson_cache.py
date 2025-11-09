"""Unit tests for lesson cache functionality."""

import asyncio

import pytest

from promptheus.data.lesson_cache import LessonCache
from promptheus.data.models import SkillLevel
from promptheus.data.schemas import (
    ExampleComparison,
    Examples,
    Exercises,
    ExerciseScenario,
    LessonContentSchema,
    Tag,
    TheoryContent,
    TheorySection,
)


@pytest.fixture
def sample_lesson() -> LessonContentSchema:
    """Create a sample lesson for testing."""
    return LessonContentSchema(
        title="Test Lesson",
        skill_level=SkillLevel.BEGINNER,
        tags=[Tag.GENERAL],
        theory_content=TheoryContent(sections=[TheorySection(content="Test theory")]),
        examples=Examples(
            comparisons=[
                ExampleComparison(
                    bad="Bad example",
                    bad_reason="It's bad",
                    good="Good example",
                    good_reason="It's good",
                )
            ]
        ),
        exercises=Exercises(
            scenarios=[ExerciseScenario(scenario="Test scenario", task="Test task")]
        ),
    )


@pytest.fixture
def lesson_cache() -> LessonCache:
    """Create a fresh lesson cache for each test."""
    return LessonCache()


class TestLessonCache:
    """Test suite for LessonCache class."""

    @pytest.mark.asyncio
    async def test_initialization(self, lesson_cache: LessonCache) -> None:
        """Test that cache initializes correctly."""
        stats = await lesson_cache.get_stats()
        assert stats["total_cached"] == 0
        assert stats["skill_levels"] == []
        assert stats["hits"] == 0
        assert stats["misses"] == 0

    @pytest.mark.asyncio
    async def test_set_and_get_lesson(
        self, lesson_cache: LessonCache, sample_lesson: LessonContentSchema
    ) -> None:
        """Test setting and getting a lesson."""
        # Initially should return None
        result = await lesson_cache.get(SkillLevel.BEGINNER, "test-lesson")
        assert result is None

        # Set lesson
        await lesson_cache.set(SkillLevel.BEGINNER, "test-lesson", sample_lesson)

        # Should now return the lesson
        result = await lesson_cache.get(SkillLevel.BEGINNER, "test-lesson")
        assert result is not None
        assert result.title == "Test Lesson"
        assert result.skill_level == SkillLevel.BEGINNER

    @pytest.mark.asyncio
    async def test_get_different_skill_level(
        self, lesson_cache: LessonCache, sample_lesson: LessonContentSchema
    ) -> None:
        """Test getting lesson from different skill level returns None."""
        await lesson_cache.set(SkillLevel.BEGINNER, "test-lesson", sample_lesson)

        result = await lesson_cache.get(SkillLevel.INTERMEDIATE, "test-lesson")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_different_slug(
        self, lesson_cache: LessonCache, sample_lesson: LessonContentSchema
    ) -> None:
        """Test getting lesson with different slug returns None."""
        await lesson_cache.set(SkillLevel.BEGINNER, "test-lesson", sample_lesson)

        result = await lesson_cache.get(SkillLevel.BEGINNER, "different-slug")
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_lesson(
        self, lesson_cache: LessonCache, sample_lesson: LessonContentSchema
    ) -> None:
        """Test deleting a lesson."""
        await lesson_cache.set(SkillLevel.BEGINNER, "test-lesson", sample_lesson)

        # Verify it exists
        result = await lesson_cache.get(SkillLevel.BEGINNER, "test-lesson")
        assert result is not None

        # Delete it
        deleted = await lesson_cache.delete(SkillLevel.BEGINNER, "test-lesson")
        assert deleted is True

        # Should no longer exist
        result = await lesson_cache.get(SkillLevel.BEGINNER, "test-lesson")
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_lesson(self, lesson_cache: LessonCache) -> None:
        """Test deleting a lesson that doesn't exist."""
        deleted = await lesson_cache.delete(SkillLevel.BEGINNER, "nonexistent")
        assert deleted is False

    @pytest.mark.asyncio
    async def test_clear_all(
        self, lesson_cache: LessonCache, sample_lesson: LessonContentSchema
    ) -> None:
        """Test clearing all lessons from cache."""
        # Add multiple lessons
        await lesson_cache.set(SkillLevel.BEGINNER, "lesson1", sample_lesson)
        await lesson_cache.set(SkillLevel.INTERMEDIATE, "lesson2", sample_lesson)

        # Verify they exist
        stats = await lesson_cache.get_stats()
        assert stats["total_cached"] == 2

        # Clear all
        await lesson_cache.clear()

        # Should be empty
        stats = await lesson_cache.get_stats()
        assert stats["total_cached"] == 0

    @pytest.mark.asyncio
    async def test_reload_skill_level(
        self, lesson_cache: LessonCache, sample_lesson: LessonContentSchema
    ) -> None:
        """Test reloading all lessons for a skill level."""
        # Create multiple lessons for the same skill level
        lessons = {
            "lesson1": sample_lesson,
            "lesson2": sample_lesson,
        }

        # Reload skill level
        count = await lesson_cache.reload_skill_level(SkillLevel.BEGINNER, lessons)
        assert count == 2

        # Verify lessons are cached
        result1 = await lesson_cache.get(SkillLevel.BEGINNER, "lesson1")
        result2 = await lesson_cache.get(SkillLevel.BEGINNER, "lesson2")
        assert result1 is not None
        assert result2 is not None

        # Verify stats
        stats = await lesson_cache.get_stats()
        assert stats["total_cached"] == 2
        assert len(stats["skill_levels"]) == 1

    @pytest.mark.asyncio
    async def test_reload_skill_level_empty(self, lesson_cache: LessonCache) -> None:
        """Test reloading skill level with empty lessons dict."""
        count = await lesson_cache.reload_skill_level(SkillLevel.BEGINNER, {})
        assert count == 0

    @pytest.mark.asyncio
    async def test_reload_skill_level_overwrites_existing(
        self, lesson_cache: LessonCache, sample_lesson: LessonContentSchema
    ) -> None:
        """Test that reloading skill level overwrites existing lessons."""
        # Set initial lesson
        await lesson_cache.set(SkillLevel.BEGINNER, "lesson1", sample_lesson)

        # Create new lesson with same slug but different content
        new_lesson = LessonContentSchema(
            title="Updated Lesson",
            skill_level=SkillLevel.BEGINNER,
            tags=[Tag.GENERAL],
            theory_content=TheoryContent(sections=[TheorySection(content="Updated theory")]),
            examples=Examples(
                comparisons=[
                    ExampleComparison(
                        bad="Bad example",
                        bad_reason="It's bad",
                        good="Good example",
                        good_reason="It's good",
                    )
                ]
            ),
            exercises=Exercises(
                scenarios=[ExerciseScenario(scenario="Test scenario", task="Test task")]
            ),
        )

        # Reload with new lesson
        count = await lesson_cache.reload_skill_level(SkillLevel.BEGINNER, {"lesson1": new_lesson})
        assert count == 1

        # Verify updated lesson
        result = await lesson_cache.get(SkillLevel.BEGINNER, "lesson1")
        assert result is not None
        assert result.title == "Updated Lesson"

    @pytest.mark.asyncio
    async def test_concurrent_access(
        self, lesson_cache: LessonCache, sample_lesson: LessonContentSchema
    ) -> None:
        """Test concurrent access to cache operations."""

        async def set_and_get(index: int) -> None:
            slug = f"lesson{index}"
            await lesson_cache.set(SkillLevel.BEGINNER, slug, sample_lesson)
            result = await lesson_cache.get(SkillLevel.BEGINNER, slug)
            assert result is not None

        # Run multiple concurrent operations
        tasks = [set_and_get(i) for i in range(10)]
        await asyncio.gather(*tasks)

        # Verify all lessons are cached
        stats = await lesson_cache.get_stats()
        assert stats["total_cached"] == 10

    @pytest.mark.asyncio
    async def test_stats_accuracy(
        self, lesson_cache: LessonCache, sample_lesson: LessonContentSchema
    ) -> None:
        """Test that statistics are accurate."""
        # Initially empty
        stats = await lesson_cache.get_stats()
        assert stats["total_cached"] == 0
        assert stats["skill_levels"] == []

        # Add lessons to different skill levels
        await lesson_cache.set(SkillLevel.BEGINNER, "lesson1", sample_lesson)
        await lesson_cache.set(SkillLevel.BEGINNER, "lesson2", sample_lesson)
        await lesson_cache.set(SkillLevel.INTERMEDIATE, "lesson3", sample_lesson)

        stats = await lesson_cache.get_stats()
        assert stats["total_cached"] == 3
        assert len(stats["skill_levels"]) == 2

        # Delete a lesson
        await lesson_cache.delete(SkillLevel.BEGINNER, "lesson1")

        stats = await lesson_cache.get_stats()
        assert stats["total_cached"] == 2
        assert len(stats["skill_levels"]) == 2  # Still 2 skill levels even though one is empty

    @pytest.mark.asyncio
    async def test_thread_safety_lock_usage(
        self, lesson_cache: LessonCache, sample_lesson: LessonContentSchema
    ) -> None:
        """Test that operations are thread-safe using asyncio.Lock."""
        # This test verifies that the lock is properly used by checking that
        # concurrent operations don't interfere with each other

        results = []

        async def concurrent_operation(index: int) -> None:
            # Perform multiple operations rapidly
            slug = f"concurrent-lesson-{index}"
            await lesson_cache.set(SkillLevel.BEGINNER, slug, sample_lesson)
            result = await lesson_cache.get(SkillLevel.BEGINNER, slug)
            results.append(result is not None)

            # Delete and verify
            await lesson_cache.delete(SkillLevel.BEGINNER, slug)
            deleted_result = await lesson_cache.get(SkillLevel.BEGINNER, slug)
            results.append(deleted_result is None)

        # Run concurrent operations
        tasks = [concurrent_operation(i) for i in range(5)]
        await asyncio.gather(*tasks)

        # All operations should have succeeded
        assert all(results)
        assert len(results) == 10  # 5 operations * 2 checks each
