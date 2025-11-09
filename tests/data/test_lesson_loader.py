"""Tests for lesson loader service."""

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from promptheus.data.async_repositories import AsyncLessonRepository
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
    def loader_service(self, mock_settings, mock_lesson_repo):
        """Create loader service with mocked dependencies."""
        return LessonLoaderService(
            settings=mock_settings,
            lesson_repo=mock_lesson_repo,
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

    def test_init_with_dependencies(self, mock_settings, mock_lesson_repo):
        """Test initialization with provided dependencies."""
        service = LessonLoaderService(
            settings=mock_settings,
            lesson_repo=mock_lesson_repo,
        )

        assert service.settings == mock_settings
        assert service.lesson_repo == mock_lesson_repo

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

    def test_extract_order_index_with_number(self, loader_service):
        """Test extracting order index from filename with number prefix."""
        file_path = Path("01_test_lesson.json")
        result = loader_service._extract_order_index(file_path)
        assert result == 1

    def test_extract_order_index_without_number(self, loader_service):
        """Test extracting order index from filename without number prefix."""
        file_path = Path("test_lesson.json")
        result = loader_service._extract_order_index(file_path)
        assert result == 999

    def test_extract_order_index_invalid_format(self, loader_service):
        """Test extracting order index from malformed filename."""
        file_path = Path("invalid_format.json")
        result = loader_service._extract_order_index(file_path)
        assert result == 999

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

        with patch("promptheus.data.lesson_loader.LessonContentSchema") as mock_schema:
            mock_instance = MagicMock()
            mock_instance.title = "Test Lesson"
            mock_instance.skill_level = SkillLevel.BEGINNER
            mock_instance.tags = ["test"]
            mock_instance.theory_content = {"sections": []}
            mock_instance.examples = {"comparisons": []}
            mock_instance.exercises = {"scenarios": []}
            mock_schema.from_json.return_value = mock_instance

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

        with patch("promptheus.data.lesson_loader.LessonContentSchema") as mock_schema:
            # Mock successful validation for first file
            mock_instance = MagicMock()
            mock_instance.title = "Valid Lesson"
            mock_instance.skill_level = SkillLevel.BEGINNER
            mock_instance.tags = []
            mock_instance.theory_content = {"sections": []}
            mock_instance.examples = {"comparisons": []}
            mock_instance.exercises = {"scenarios": []}

            def mock_from_json(data):
                if "Valid" in json.dumps(data):
                    return mock_instance
                else:
                    raise Exception("Validation failed")

            mock_schema.from_json.side_effect = mock_from_json

            result = await loader_service.batch_load_all()

            # Should have loaded 1 lesson successfully
            assert result == 1
            loader_service.lesson_repo.upsert_lesson.assert_called_once()
