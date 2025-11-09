"""Tests for version manager service."""

import pytest

from promptheus.data.models import LessonVersion
from promptheus.data.version_manager import VersionManager


class TestVersionManager:
    """Test cases for VersionManager."""

    @pytest.fixture
    def version_manager(self) -> VersionManager:
        """Create VersionManager instance."""
        return VersionManager()

    def test_hash_content_deterministic(self, version_manager: VersionManager):
        """Test that hash_content produces consistent results."""
        content = {"title": "Test Lesson", "content": "test data"}

        hash1 = version_manager.hash_content(content)
        hash2 = version_manager.hash_content(content)

        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 produces 64 hex characters

    def test_hash_content_different_for_different_content(self, version_manager: VersionManager):
        """Test that different content produces different hashes."""
        content1 = {"title": "Lesson 1"}
        content2 = {"title": "Lesson 2"}

        hash1 = version_manager.hash_content(content1)
        hash2 = version_manager.hash_content(content2)

        assert hash1 != hash2

    def test_validate_version_valid(self, version_manager: VersionManager):
        """Test version validation with valid versions."""
        assert version_manager.validate_version("1.0.0") is True
        assert version_manager.validate_version("2.1.3") is True
        assert version_manager.validate_version("10.20.30") is True

    def test_validate_version_invalid(self, version_manager: VersionManager):
        """Test version validation with invalid versions."""
        assert version_manager.validate_version("1.0") is False
        assert version_manager.validate_version("1.0.0.0") is False
        assert version_manager.validate_version("1.0.a") is False
        assert version_manager.validate_version("invalid") is False

    def test_increment_version_patch(self, version_manager: VersionManager):
        """Test version increment with patch bump."""
        assert version_manager.increment_version("1.0.0", "patch") == "1.0.1"
        assert version_manager.increment_version("1.0.9", "patch") == "1.0.10"
        assert version_manager.increment_version("1.2.3", "patch") == "1.2.4"

    def test_increment_version_minor(self, version_manager: VersionManager):
        """Test version increment with minor bump."""
        assert version_manager.increment_version("1.0.0", "minor") == "1.1.0"
        assert version_manager.increment_version("1.0.9", "minor") == "1.1.0"
        assert version_manager.increment_version("1.2.3", "minor") == "1.3.0"

    def test_increment_version_major(self, version_manager: VersionManager):
        """Test version increment with major bump."""
        assert version_manager.increment_version("1.0.0", "major") == "2.0.0"
        assert version_manager.increment_version("1.0.9", "major") == "2.0.0"
        assert version_manager.increment_version("1.2.3", "major") == "2.0.0"

    def test_increment_version_invalid_bump_type(self, version_manager: VersionManager):
        """Test version increment with invalid bump type."""
        with pytest.raises(ValueError, match="Unknown bump type"):
            version_manager.increment_version("1.0.0", "invalid")

    def test_increment_version_invalid_version(self, version_manager: VersionManager):
        """Test version increment with invalid version string."""
        with pytest.raises(ValueError, match="Invalid current version"):
            version_manager.increment_version("invalid", "patch")

    def test_detect_changes_no_change(self, version_manager: VersionManager):
        """Test change detection when content hasn't changed."""
        content = {"title": "Test"}
        hash_value = version_manager.hash_content(content)

        result = version_manager.detect_changes(1, content, hash_value)
        assert result is None

    def test_detect_changes_with_change(self, version_manager: VersionManager):
        """Test change detection when content has changed."""
        new_content = {"title": "New"}

        result = version_manager.detect_changes(1, new_content, "old_hash")
        assert result is not None
        assert "new_hash" in result
        assert "content" in result
        assert result["content"] == new_content

    def test_compare_versions_same_lesson(self, version_manager: VersionManager):
        """Test version comparison for same lesson."""
        # Create mock version objects
        v1 = LessonVersion(
            id=1,
            lesson_id=1,
            version="1.0.0",
            content_hash="hash1",
            content_snapshot={"title": "Old"},
            is_active=False,
            created_at=None,
            created_by="test",
        )
        v2 = LessonVersion(
            id=2,
            lesson_id=1,
            version="1.1.0",
            content_hash="hash2",
            content_snapshot={"title": "New"},
            is_active=True,
            created_at=None,
            created_by="test",
        )

        result = version_manager.compare_versions(v1, v2)

        assert result["lesson_id"] == 1
        assert "changed_fields" in result
        assert "version_comparison" in result
        assert result["version_comparison"]["is_newer"] is True

    def test_compare_versions_different_lessons(self, version_manager: VersionManager):
        """Test version comparison for different lessons raises error."""
        v1 = LessonVersion(
            id=1,
            lesson_id=1,
            version="1.0.0",
            content_hash="hash1",
            content_snapshot={},
            is_active=False,
            created_at=None,
            created_by="test",
        )
        v2 = LessonVersion(
            id=2,
            lesson_id=2,  # Different lesson
            version="1.0.0",
            content_hash="hash1",
            content_snapshot={},
            is_active=True,
            created_at=None,
            created_by="test",
        )

        with pytest.raises(ValueError, match="Cannot compare versions from different lessons"):
            version_manager.compare_versions(v1, v2)

    def test_compare_versions_invalid_version_strings(self, version_manager: VersionManager):
        """Test version comparison with invalid version strings."""
        v1 = LessonVersion(
            id=1,
            lesson_id=1,
            version="invalid",
            content_hash="hash1",
            content_snapshot={"title": "Test"},
            is_active=False,
            created_at=None,
            created_by="test",
        )
        v2 = LessonVersion(
            id=2,
            lesson_id=1,
            version="1.0.0",
            content_hash="hash2",
            content_snapshot={"title": "Test"},
            is_active=True,
            created_at=None,
            created_by="test",
        )

        result = version_manager.compare_versions(v1, v2)
        assert result["version_comparison"]["is_newer"] is None
        assert result["version_comparison"]["bump_type"] is None

    def test_compare_versions_all_bump_types(self, version_manager: VersionManager):
        """Test version comparison covers all bump types."""
        # Test major bump
        v1 = LessonVersion(
            id=1,
            lesson_id=1,
            version="1.0.0",
            content_hash="hash1",
            content_snapshot={"title": "Test"},
            is_active=False,
            created_at=None,
            created_by="test",
        )
        v2 = LessonVersion(
            id=2,
            lesson_id=1,
            version="2.0.0",
            content_hash="hash2",
            content_snapshot={"title": "Test"},
            is_active=True,
            created_at=None,
            created_by="test",
        )

        result = version_manager.compare_versions(v1, v2)
        assert result["version_comparison"]["bump_type"] == "major"

        # Test minor bump
        v3 = LessonVersion(
            id=3,
            lesson_id=1,
            version="2.1.0",
            content_hash="hash3",
            content_snapshot={"title": "Test"},
            is_active=True,
            created_at=None,
            created_by="test",
        )

        result = version_manager.compare_versions(v2, v3)
        assert result["version_comparison"]["bump_type"] == "minor"

        # Test patch bump
        v4 = LessonVersion(
            id=4,
            lesson_id=1,
            version="2.1.1",
            content_hash="hash4",
            content_snapshot={"title": "Test"},
            is_active=True,
            created_at=None,
            created_by="test",
        )

        result = version_manager.compare_versions(v3, v4)
        assert result["version_comparison"]["bump_type"] == "patch"
