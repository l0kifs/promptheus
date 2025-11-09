"""Tests for lesson loader service."""

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from promptheus.data.async_repositories import AsyncLessonRepository
from promptheus.data.lesson_cache import LessonCache
from promptheus.data.lesson_loader import LessonLoaderService
from promptheus.data.models import SkillLevel


class TestLessonLoaderService:
    """Tests for LessonLoaderService."""

    @pytest.fixture
    def mock_settings(self):
        """Mock settings with test lesson path."""
        settings = MagicMock()
        settings.lessons_content_path = Path("/fake/path")
        return settings

    @pytest.fixture
    def mock_lesson_repo(self):
        """Mock lesson repository."""
        repo = MagicMock(spec=AsyncLessonRepository)
        repo.upsert_lesson = AsyncMock()
        return repo

    @pytest.fixture
    def mock_lesson_cache(self):
        """Mock lesson cache."""
        cache = MagicMock(spec=LessonCache)
        cache.get = AsyncMock(return_value=None)
        cache.set = AsyncMock()
        cache.reload_skill_level = AsyncMock(return_value=1)
        return cache

    @pytest.fixture
    def mock_schemas(self, sample_lesson_json):
        """Mock schemas that returns real schema instances."""
        from promptheus.data.schemas import LessonContentSchema

        schemas = MagicMock()
        schemas.from_json = MagicMock(
            return_value=LessonContentSchema.from_json(sample_lesson_json)
        )
        return schemas

    @pytest.fixture
    def loader_service(self, mock_settings, mock_lesson_repo, mock_lesson_cache, mock_schemas):
        """Create loader service with mocked dependencies."""
        return LessonLoaderService(
            settings=mock_settings,
            lesson_repo=mock_lesson_repo,
            cache=mock_lesson_cache,
            schemas=mock_schemas,
        )

    @pytest.fixture
    def sample_lesson_json(self):
        """Sample valid lesson JSON data."""
        return {
            "title": "Test Lesson",
            "skill_level": "beginner",
            "tags": ["general"],  # Use valid tag from enum
            "theory_content": {"sections": [{"content": "This is theory content."}]},
            "examples": {
                "comparisons": [
                    {
                        "bad": "Bad example",
                        "bad_reason": "It's bad",
                        "good": "Good example",
                        "good_reason": "It's good",
                    }
                ]
            },
            "exercises": {"scenarios": [{"scenario": "Test scenario", "task": "Test task"}]},
        }

    def test_init_with_dependencies(
        self, mock_settings, mock_lesson_repo, mock_lesson_cache, mock_schemas
    ):
        """Test initialization with provided dependencies."""
        service = LessonLoaderService(
            settings=mock_settings,
            lesson_repo=mock_lesson_repo,
            cache=mock_lesson_cache,
            schemas=mock_schemas,
        )

        assert service.settings == mock_settings
        assert service.lesson_repo == mock_lesson_repo
        assert service.cache == mock_lesson_cache
        assert service.schemas == mock_schemas

    @pytest.mark.asyncio
    async def test_get_lesson_from_cache(
        self, loader_service, mock_lesson_cache, sample_lesson_json
    ):
        """Test getting lesson from cache first."""
        from promptheus.data.schemas import LessonContentSchema

        # Mock cache hit
        cached_lesson = LessonContentSchema.from_json(sample_lesson_json)
        mock_lesson_cache.get.return_value = cached_lesson

        result = await loader_service.get_lesson("beginner", "test-lesson")

        assert result == cached_lesson
        mock_lesson_cache.get.assert_called_once_with(SkillLevel.BEGINNER, "test-lesson")
        # Should not call database
        loader_service.lesson_repo.find_by_slug.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_lesson_from_database_and_cache(
        self, loader_service, mock_lesson_cache, mock_lesson_repo, mock_schemas, sample_lesson_json
    ):
        """Test getting lesson from database when not in cache."""
        from promptheus.data.schemas import LessonContentSchema

        # Mock cache miss
        mock_lesson_cache.get.return_value = None

        # Mock database result
        mock_db_lesson = MagicMock()
        mock_db_lesson.title = "Test Lesson"
        mock_db_lesson.skill_level = SkillLevel.BEGINNER
        mock_db_lesson.tags = ["general"]
        mock_db_lesson.theory_content = {"sections": [{"content": "test"}]}
        mock_db_lesson.examples = {"comparisons": []}
        mock_db_lesson.exercises = {"scenarios": []}
        mock_lesson_repo.find_by_slug.return_value = mock_db_lesson

        # Mock schema creation
        mock_schema_instance = LessonContentSchema.from_json(sample_lesson_json)
        mock_schemas.from_json.return_value = mock_schema_instance

        result = await loader_service.get_lesson("beginner", "test-lesson")

        assert result == mock_schema_instance
        mock_lesson_cache.get.assert_called_once_with(SkillLevel.BEGINNER, "test-lesson")
        mock_lesson_repo.find_by_slug.assert_called_once_with(SkillLevel.BEGINNER, "test-lesson")
        # Should cache the result
        mock_lesson_cache.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_lesson_invalid_skill_level(self, loader_service):
        """Test getting lesson with invalid skill level."""
        result = await loader_service.get_lesson("invalid", "test-lesson")

        assert result is None

    @pytest.mark.asyncio
    async def test_get_lesson_no_cache_no_repo(self, loader_service):
        """Test getting lesson when no cache or repo available."""
        loader_service.cache = None
        loader_service.lesson_repo = None

        result = await loader_service.get_lesson("beginner", "test-lesson")

        assert result is None

    def test_init_without_dependencies(self):
        """Test initialization without dependencies (uses defaults)."""
        with patch("promptheus.data.lesson_loader.get_settings") as mock_get_settings:
            mock_settings = MagicMock()
            mock_get_settings.return_value = mock_settings

            service = LessonLoaderService()

            assert service.settings == mock_settings
            assert service.lesson_repo is None

    @pytest.mark.asyncio
    async def test_scan_directory_missing_path(self, loader_service, mock_settings):
        """Test scanning directory when path doesn't exist."""
        mock_settings.lessons_content_path = Path("/nonexistent/path")

        with pytest.raises(FileNotFoundError, match="Lessons content directory does not exist"):
            await loader_service.scan_directory()

    @pytest.mark.asyncio
    async def test_scan_directory_with_files(self, loader_service, mock_settings, tmp_path):
        """Test scanning directory with lesson files."""
        # Create temporary directory structure
        lessons_dir = tmp_path / "lessons"
        beginner_dir = lessons_dir / "beginner"
        intermediate_dir = lessons_dir / "intermediate"
        advanced_dir = lessons_dir / "advanced"

        beginner_dir.mkdir(parents=True)
        intermediate_dir.mkdir(parents=True)
        advanced_dir.mkdir(parents=True)

        # Create some JSON files
        (beginner_dir / "01_lesson1.json").write_text("{}")
        (beginner_dir / "02_lesson2.json").write_text("{}")
        (intermediate_dir / "01_lesson3.json").write_text("{}")
        (advanced_dir / "01_lesson4.json").write_text("{}")

        mock_settings.lessons_content_path = lessons_dir

        result = await loader_service.scan_directory()

        assert "beginner" in result
        assert "intermediate" in result
        assert "advanced" in result
        assert len(result["beginner"]) == 2
        assert len(result["intermediate"]) == 1
        assert len(result["advanced"]) == 1

    @pytest.mark.asyncio
    async def test_scan_directory_missing_subdirs(self, loader_service, mock_settings, tmp_path):
        """Test scanning directory with missing subdirectories."""
        # Create directory with only beginner
        lessons_dir = tmp_path / "lessons"
        beginner_dir = lessons_dir / "beginner"
        beginner_dir.mkdir(parents=True)

        (beginner_dir / "01_lesson.json").write_text("{}")

        mock_settings.lessons_content_path = lessons_dir

        result = await loader_service.scan_directory()

        assert "beginner" in result
        assert len(result["beginner"]) == 1
        assert "intermediate" not in result
        assert "advanced" not in result

    def test_load_json_file_success(self, loader_service, tmp_path, sample_lesson_json):
        """Test loading valid JSON file."""
        json_file = tmp_path / "test.json"
        json_file.write_text(json.dumps(sample_lesson_json))

        result = loader_service.load_json_file(json_file)

        assert result == sample_lesson_json

    def test_load_json_file_not_found(self, loader_service):
        """Test loading non-existent JSON file."""
        with pytest.raises(FileNotFoundError):
            loader_service.load_json_file(Path("/nonexistent/file.json"))

    def test_load_json_file_invalid_json(self, loader_service, tmp_path):
        """Test loading invalid JSON file."""
        json_file = tmp_path / "invalid.json"
        json_file.write_text("invalid json content")

        with pytest.raises(json.JSONDecodeError):
            loader_service.load_json_file(json_file)

    def test_validate_lesson_content_success(self, loader_service, sample_lesson_json):
        """Test validating valid lesson content."""
        from promptheus.data.schemas import LessonContentSchema

        result = loader_service.validate_lesson_content(sample_lesson_json, Path("test.json"))

        assert isinstance(result, LessonContentSchema)
        assert result.title == "Test Lesson"
        assert result.skill_level.value == "beginner"

    def test_validate_lesson_content_failure(self, loader_service, sample_lesson_json):
        """Test validating invalid lesson content."""
        # Mock the schemas attribute
        mock_schema = MagicMock()
        mock_schema.from_json.side_effect = Exception("Validation error")
        loader_service.schemas = mock_schema

        with pytest.raises(
            ValueError, match="Validation failed for .*test.json.*: Validation error"
        ):
            loader_service.validate_lesson_content(sample_lesson_json, Path("test.json"))

    @pytest.mark.asyncio
    async def test_load_lesson_success(self, loader_service, tmp_path, sample_lesson_json):
        """Test loading and validating a complete lesson."""
        from promptheus.data.schemas import LessonContentSchema

        json_file = tmp_path / "test.json"
        json_file.write_text(json.dumps(sample_lesson_json))

        result = await loader_service.load_lesson(json_file)

        assert isinstance(result, LessonContentSchema)
        assert result.title == "Test Lesson"
        assert result.skill_level.value == "beginner"

    @pytest.mark.asyncio
    async def test_load_lesson_file_error(self, loader_service):
        """Test load_lesson with file reading error."""
        with pytest.raises(FileNotFoundError):
            await loader_service.load_lesson(Path("/nonexistent/file.json"))

    @pytest.mark.asyncio
    async def test_batch_load_all_no_repo(self, loader_service):
        """Test batch_load_all without lesson repository."""
        loader_service.lesson_repo = None

        with pytest.raises(RuntimeError, match="Lesson repository not available"):
            await loader_service.batch_load_all()

    @pytest.mark.asyncio
    async def test_batch_load_all_success(
        self, loader_service, mock_settings, tmp_path, sample_lesson_json
    ):
        """Test successful batch loading of lessons."""
        # Create temporary lesson files
        lessons_dir = tmp_path / "lessons"
        beginner_dir = lessons_dir / "beginner"
        beginner_dir.mkdir(parents=True)

        lesson_file = beginner_dir / "01_test.json"
        lesson_file.write_text(json.dumps(sample_lesson_json))

        mock_settings.lessons_content_path = lessons_dir

        result = await loader_service.batch_load_all()

        assert result == 1
        loader_service.lesson_repo.upsert_lesson.assert_called_once()

    @pytest.mark.asyncio
    async def test_batch_load_all_with_errors(self, loader_service, mock_settings, tmp_path):
        """Test batch loading with some lesson errors."""
        # Create directory with valid and invalid files
        lessons_dir = tmp_path / "lessons"
        beginner_dir = lessons_dir / "beginner"
        beginner_dir.mkdir(parents=True)

        # Valid lesson
        valid_file = beginner_dir / "01_valid.json"
        valid_file.write_text(
            '{"title": "Valid", "skill_level": "beginner", "tags": ["general"], "theory_content": {"sections": [{"content": "test"}]}, "examples": {"comparisons": [{"bad": "bad", "bad_reason": "bad", "good": "good", "good_reason": "good"}]}, "exercises": {"scenarios": [{"scenario": "scenario", "task": "task"}]}}'
        )

        # Invalid lesson (missing required fields)
        invalid_file = beginner_dir / "02_invalid.json"
        invalid_file.write_text('{"invalid": "data"}')

        mock_settings.lessons_content_path = lessons_dir

        # Mock the schemas to fail on invalid data
        def mock_from_json(data):
            if "title" in data and "skill_level" in data:
                # Return real schema for valid data
                from promptheus.data.schemas import LessonContentSchema

                return LessonContentSchema.from_json(data)
            else:
                raise Exception("Validation failed")

        loader_service.schemas.from_json.side_effect = mock_from_json

        result = await loader_service.batch_load_all()

        # Should have loaded 1 lesson successfully
        assert result == 1
        loader_service.lesson_repo.upsert_lesson.assert_called_once()
