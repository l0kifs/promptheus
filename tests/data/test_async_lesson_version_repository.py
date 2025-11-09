"""Tests for AsyncLessonVersionRepository."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from promptheus.data.async_repositories import AsyncLessonVersionRepository


class TestAsyncLessonVersionRepository:
    """Test cases for AsyncLessonVersionRepository."""

    @pytest.fixture
    async def repo(self, async_db_session: AsyncSession):
        """Create repository instance."""

        # Create a session maker that returns the test session
        def session_maker():
            return async_db_session

        return AsyncLessonVersionRepository(session_maker)  # type: ignore

    @pytest.mark.asyncio
    async def test_create_version(self, repo: AsyncLessonVersionRepository):
        """Test creating a new lesson version."""
        content_snapshot = {"title": "Test Lesson", "content": "test"}
        version = await repo.create(
            lesson_id=1,
            version="1.0.0",
            content_hash="testhash123",
            content_snapshot=content_snapshot,
            is_active=True,
            created_by="test_user",
        )

        assert version.lesson_id == 1
        assert version.version == "1.0.0"
        assert version.content_hash == "testhash123"
        assert version.content_snapshot == content_snapshot
        assert version.is_active is True
        assert version.created_by == "test_user"
        assert version.id is not None

    @pytest.mark.asyncio
    async def test_find_by_lesson_and_version_found(self, repo: AsyncLessonVersionRepository):
        """Test finding version by lesson and version when it exists."""
        # Create a version first
        content_snapshot = {"title": "Test"}
        created = await repo.create(
            lesson_id=2,
            version="2.0.0",
            content_hash="hash2",
            content_snapshot=content_snapshot,
        )

        # Find it
        found = await repo.find_by_lesson_and_version(2, "2.0.0")
        assert found is not None
        assert found.id == created.id
        assert found.version == "2.0.0"

    @pytest.mark.asyncio
    async def test_find_by_lesson_and_version_not_found(self, repo: AsyncLessonVersionRepository):
        """Test finding version by lesson and version when it doesn't exist."""
        found = await repo.find_by_lesson_and_version(999, "1.0.0")
        assert found is None

    @pytest.mark.asyncio
    async def test_find_active_by_lesson_found(self, repo: AsyncLessonVersionRepository):
        """Test finding active version for a lesson."""
        # Create inactive version
        await repo.create(
            lesson_id=3,
            version="3.0.0",
            content_hash="hash3",
            content_snapshot={"title": "Inactive"},
            is_active=False,
        )

        # Create active version
        active = await repo.create(
            lesson_id=3,
            version="3.1.0",
            content_hash="hash3active",
            content_snapshot={"title": "Active"},
            is_active=True,
        )

        # Find active
        found = await repo.find_active_by_lesson(3)
        assert found is not None
        assert found.id == active.id
        assert found.is_active is True

    @pytest.mark.asyncio
    async def test_find_active_by_lesson_not_found(self, repo: AsyncLessonVersionRepository):
        """Test finding active version when none exists."""
        found = await repo.find_active_by_lesson(999)
        assert found is None

    @pytest.mark.asyncio
    async def test_find_all_by_lesson(self, repo: AsyncLessonVersionRepository):
        """Test finding all versions for a lesson."""
        # Create multiple versions for same lesson
        lesson_id = 4
        v1 = await repo.create(
            lesson_id=lesson_id,
            version="4.0.0",
            content_hash="hash4_0",
            content_snapshot={"title": "V4.0"},
        )
        v2 = await repo.create(
            lesson_id=lesson_id,
            version="4.1.0",
            content_hash="hash4_1",
            content_snapshot={"title": "V4.1"},
        )
        v3 = await repo.create(
            lesson_id=lesson_id,
            version="4.2.0",
            content_hash="hash4_2",
            content_snapshot={"title": "V4.2"},
        )

        # Find all
        versions = await repo.find_all_by_lesson(lesson_id)
        assert len(versions) == 3

        # Should be ordered by creation time descending (newest first)
        assert versions[0].id == v3.id
        assert versions[1].id == v2.id
        assert versions[2].id == v1.id

    @pytest.mark.asyncio
    async def test_find_all_by_lesson_empty(self, repo: AsyncLessonVersionRepository):
        """Test finding all versions for a lesson with no versions."""
        versions = await repo.find_all_by_lesson(999)
        assert versions == []

    @pytest.mark.asyncio
    async def test_update_active_status(self, repo: AsyncLessonVersionRepository):
        """Test updating active status of a version."""
        # Create version
        version = await repo.create(
            lesson_id=5,
            version="5.0.0",
            content_hash="hash5",
            content_snapshot={"title": "Test"},
            is_active=False,
        )

        # Update to active
        await repo.update_active_status(version.id, True)

        # Verify
        found = await repo.find_by_lesson_and_version(5, "5.0.0")
        assert found is not None
        assert found.is_active is True

    @pytest.mark.asyncio
    async def test_update_active_status_not_found(self, repo: AsyncLessonVersionRepository):
        """Test updating active status of non-existent version."""
        # Should not raise error
        await repo.update_active_status(99999, True)

    @pytest.mark.asyncio
    async def test_deactivate_other_versions_keep_none(self, repo: AsyncLessonVersionRepository):
        """Test deactivating all versions for a lesson."""
        lesson_id = 6

        # Create multiple active versions
        await repo.create(
            lesson_id=lesson_id,
            version="6.0.0",
            content_hash="hash6_0",
            content_snapshot={"title": "V6.0"},
            is_active=True,
        )
        await repo.create(
            lesson_id=lesson_id,
            version="6.1.0",
            content_hash="hash6_1",
            content_snapshot={"title": "V6.1"},
            is_active=True,
        )

        # Deactivate all
        await repo.deactivate_other_versions(lesson_id)

        # Verify all are inactive
        versions = await repo.find_all_by_lesson(lesson_id)
        for v in versions:
            assert v.is_active is False

    @pytest.mark.asyncio
    async def test_deactivate_other_versions_keep_one(self, repo: AsyncLessonVersionRepository):
        """Test deactivating other versions while keeping one active."""
        lesson_id = 7

        # Create multiple active versions
        await repo.create(
            lesson_id=lesson_id,
            version="7.0.0",
            content_hash="hash7_0",
            content_snapshot={"title": "V7.0"},
            is_active=True,
        )
        v2 = await repo.create(
            lesson_id=lesson_id,
            version="7.1.0",
            content_hash="hash7_1",
            content_snapshot={"title": "V7.1"},
            is_active=True,
        )
        await repo.create(
            lesson_id=lesson_id,
            version="7.2.0",
            content_hash="hash7_2",
            content_snapshot={"title": "V7.2"},
            is_active=True,
        )

        # Keep v2 active, deactivate others
        await repo.deactivate_other_versions(lesson_id, keep_version_id=v2.id)

        # Verify
        versions = await repo.find_all_by_lesson(lesson_id)
        for v in versions:
            if v.id == v2.id:
                assert v.is_active is True
            else:
                assert v.is_active is False
