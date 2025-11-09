"""Lesson loader service for loading lessons from JSON files."""

import json
from pathlib import Path
from typing import Any

from loguru import logger

from promptheus.config import get_settings
from promptheus.data.async_repositories import AsyncLessonRepository
from promptheus.data.schemas import LessonContentSchema


class LessonLoaderService:
    """Service for loading and validating lessons from JSON files."""

    def __init__(
        self,
        settings: Any = None,
        lesson_repo: AsyncLessonRepository | None = None,
        schemas: Any = None,
    ) -> None:
        """Initialize lesson loader service.

        Args:
            settings: Application settings (uses get_settings() if not provided)
            lesson_repo: Lesson repository (will be injected via dependency container)
            schemas: Schema classes (will be injected via dependency container)
        """
        self.settings = settings or get_settings()
        self.lesson_repo = lesson_repo
        self.schemas = schemas or LessonContentSchema

    async def scan_directory(self) -> dict[str, list[Path]]:
        """Scan lessons directory and organize JSON files by skill level.

        Returns:
            Dictionary mapping skill level names to lists of JSON file paths

        Raises:
            FileNotFoundError: If lessons directory doesn't exist
        """
        logger.debug("Scanning lessons directory", path=self.settings.lessons_content_path)

        if not self.settings.lessons_content_path.exists():
            raise FileNotFoundError(
                f"Lessons content directory does not exist: {self.settings.lessons_content_path}"
            )

        lessons_by_level: dict[str, list[Path]] = {}

        # Scan each skill level directory
        for level_dir in ["beginner", "intermediate", "advanced"]:
            level_path = self.settings.lessons_content_path / level_dir

            if not level_path.exists():
                logger.warning(
                    "Skill level directory not found, skipping", level=level_dir, path=level_path
                )
                continue

            if not level_path.is_dir():
                logger.warning(
                    "Path is not a directory, skipping", level=level_dir, path=level_path
                )
                continue

            # Find all JSON files in this directory
            json_files = sorted(level_path.glob("*.json"))
            lessons_by_level[level_dir] = json_files

            logger.debug(
                "Found lesson files",
                level=level_dir,
                count=len(json_files),
                files=[f.name for f in json_files],
            )

        total_files = sum(len(files) for files in lessons_by_level.values())
        logger.info(
            "Directory scan completed",
            total_files=total_files,
            levels_found=list(lessons_by_level.keys()),
        )

        return lessons_by_level

    def load_json_file(self, file_path: Path) -> dict[str, Any]:
        """Load and parse a JSON file.

        Args:
            file_path: Path to the JSON file

        Returns:
            Parsed JSON data as dictionary

        Raises:
            FileNotFoundError: If file doesn't exist
            json.JSONDecodeError: If JSON is invalid
            OSError: If file cannot be read
        """
        logger.debug("Loading JSON file", file_path=file_path)

        try:
            with open(file_path, encoding="utf-8") as f:
                data = json.load(f)
            logger.debug("JSON file loaded successfully", file_path=file_path)
            return data
        except FileNotFoundError:
            logger.error("Lesson file not found", file_path=file_path)
            raise
        except json.JSONDecodeError as e:
            logger.error(
                "Invalid JSON in lesson file",
                file_path=file_path,
                error=str(e),
                line=e.lineno if e.lineno else "unknown",
                column=e.colno if e.colno else "unknown",
            )
            raise
        except OSError as e:
            logger.error("Failed to read lesson file", file_path=file_path, error=str(e))
            raise

    def validate_lesson_content(self, data: dict[str, Any], file_path: Path) -> LessonContentSchema:
        """Validate lesson content using Pydantic schema.

        Args:
            data: Raw JSON data
            file_path: Path to the source file (for error context)

        Returns:
            Validated LessonContentSchema instance

        Raises:
            ValueError: If validation fails
        """
        logger.debug("Validating lesson content", file_path=file_path)

        try:
            schema = self.schemas.from_json(data)
            logger.debug(
                "Lesson content validated successfully", file_path=file_path, title=schema.title
            )
            return schema
        except Exception as e:
            logger.error(
                "Lesson content validation failed",
                file_path=file_path,
                error=str(e),
                error_type=type(e).__name__,
            )
            raise ValueError(f"Validation failed for {file_path}: {e}") from e

    async def load_lesson(self, file_path: Path) -> LessonContentSchema:
        """Load and validate a single lesson from JSON file.

        Args:
            file_path: Path to the lesson JSON file

        Returns:
            Validated lesson content schema

        Raises:
            FileNotFoundError: If file doesn't exist
            json.JSONDecodeError: If JSON is invalid
            ValueError: If validation fails
        """
        logger.info("Loading lesson", file_path=file_path)

        # Load JSON data
        data = self.load_json_file(file_path)

        # Validate content
        schema = self.validate_lesson_content(data, file_path)

        logger.info(
            "Lesson loaded successfully",
            file_path=file_path,
            title=schema.title,
            skill_level=schema.skill_level.value,
        )
        return schema

    async def batch_load_all(self) -> int:
        """Load and validate all lessons from the content directory.

        Returns:
            Number of lessons successfully loaded

        Raises:
            RuntimeError: If lesson repository is not available
        """
        if not self.lesson_repo:
            raise RuntimeError(
                "Lesson repository not available - must be injected via dependency container"
            )

        logger.info("Starting batch lesson loading")

        # Scan directory for lesson files
        lessons_by_level = await self.scan_directory()

        loaded_count = 0
        errors: list[str] = []

        # Process each skill level
        for skill_level, file_paths in lessons_by_level.items():
            logger.debug(
                "Processing skill level", skill_level=skill_level, file_count=len(file_paths)
            )

            for file_path in file_paths:
                try:
                    # Load and validate lesson
                    schema = await self.load_lesson(file_path)

                    # Determine order index from filename (assuming format like "01_title.json")
                    order_index = self._extract_order_index(file_path)

                    # Upsert to database
                    await self.lesson_repo.upsert_lesson(
                        title=schema.title,
                        skill_level=schema.skill_level,
                        order_index=order_index,
                        tags=schema.tags,
                        theory_content=schema.theory_content.model_dump(),
                        examples=schema.examples.model_dump(),
                        exercises=schema.exercises.model_dump(),
                    )

                    loaded_count += 1
                    logger.info(
                        "Lesson upserted successfully",
                        title=schema.title,
                        skill_level=skill_level,
                        order_index=order_index,
                    )

                except Exception as e:
                    error_msg = f"Failed to load lesson {file_path}: {e}"
                    logger.error(error_msg)
                    errors.append(error_msg)
                    # Continue with other lessons

        # Log summary
        if errors:
            logger.warning(
                "Batch loading completed with errors",
                loaded_count=loaded_count,
                error_count=len(errors),
            )
            for error in errors[:5]:  # Log first 5 errors
                logger.warning("Lesson loading error", error=error)
            if len(errors) > 5:
                logger.warning("Additional errors not shown", additional_count=len(errors) - 5)
        else:
            logger.info("Batch loading completed successfully", loaded_count=loaded_count)

        return loaded_count

    def _extract_order_index(self, file_path: Path) -> int:
        """Extract order index from filename.

        Assumes filename format like "01_title.json" where 01 is the order index.

        Args:
            file_path: Path to the lesson file

        Returns:
            Order index (defaults to 999 if cannot parse)
        """
        filename = file_path.stem  # Remove .json extension

        # Try to extract number from beginning of filename
        try:
            if "_" in filename:
                prefix = filename.split("_")[0]
                return int(prefix)
        except (ValueError, IndexError):
            pass

        # Fallback to a high number for files that don't follow naming convention
        logger.warning(
            "Could not extract order index from filename, using default", filename=filename
        )
        return 999
