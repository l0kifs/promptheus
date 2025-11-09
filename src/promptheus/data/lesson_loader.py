"""Lesson loader service for loading lessons from JSON files."""

import json
import re
from pathlib import Path
from typing import Any

from loguru import logger

from promptheus.config import get_settings
from promptheus.data.async_repositories import AsyncLessonRepository
from promptheus.data.lesson_cache import LessonCache
from promptheus.data.schemas import LessonContentSchema


def generate_slug(title: str, max_length: int = 100) -> str:
    """Generate URL-safe slug from title.

    Converts title to lowercase, replaces spaces with hyphens,
    removes special characters, and ensures uniqueness.

    Args:
        title: The lesson title to convert
        max_length: Maximum length of the slug (default: 100)

    Returns:
        URL-safe slug string

    Examples:
        >>> generate_slug("Introduction to Prompt Engineering")
        'introduction-to-prompt-engineering'
        >>> generate_slug("Advanced Techniques & Best Practices")
        'advanced-techniques-best-practices'
    """
    if not title:
        return ""

    # Convert to lowercase
    slug = title.lower()

    # Replace spaces and underscores with hyphens
    slug = re.sub(r"[_\s]+", "-", slug)

    # Remove special characters, keeping only alphanumeric and hyphens
    slug = re.sub(r"[^a-z0-9-]", "", slug)

    # Remove consecutive hyphens
    slug = re.sub(r"-+", "-", slug)

    # Remove leading/trailing hyphens
    slug = slug.strip("-")

    # Truncate to max length
    if len(slug) > max_length:
        slug = slug[:max_length].rstrip("-")

    return slug


class LessonLoaderService:
    """Service for loading and validating lessons from JSON files."""

    def __init__(
        self,
        settings: Any = None,
        lesson_repo: AsyncLessonRepository | None = None,
        schemas: Any = None,
        cache: LessonCache | None = None,
        version_manager: Any = None,
    ) -> None:
        """Initialize lesson loader service.

        Args:
            settings: Application settings (uses get_settings() if not provided)
            lesson_repo: Lesson repository (will be injected via dependency container)
            schemas: Schema classes (will be injected via dependency container)
            cache: Lesson cache for in-memory storage (will be injected via dependency container)
            version_manager: Version manager service (will be injected via dependency container)
        """
        self.settings = settings or get_settings()
        self.lesson_repo = lesson_repo
        self.schemas = schemas or LessonContentSchema
        self.cache = cache
        self.version_manager = version_manager

    async def get_lesson(self, skill_level: str, slug: str) -> LessonContentSchema | None:
        """Get lesson from cache or database.

        Args:
            skill_level: Skill level name (beginner, intermediate, advanced)
            slug: Lesson slug identifier

        Returns:
            Lesson content if found, None otherwise
        """
        from promptheus.data.models import SkillLevel

        try:
            skill_level_enum = SkillLevel(skill_level.lower())
        except ValueError:
            logger.warning("Invalid skill level requested", skill_level=skill_level)
            return None

        # Try cache first if available
        if self.cache:
            cached_lesson = await self.cache.get(skill_level_enum, slug)
            if cached_lesson:
                return cached_lesson

        # Fall back to database
        if not self.lesson_repo:
            logger.warning("No lesson repository available for database lookup")
            return None

        try:
            lesson_data = await self.lesson_repo.find_by_slug(skill_level_enum, slug)
            if not lesson_data:
                return None

            # Convert database model to schema
            lesson_schema = self.schemas.from_json(
                {
                    "title": lesson_data.title,
                    "skill_level": lesson_data.skill_level.value,
                    "tags": lesson_data.tags,
                    "theory_content": lesson_data.theory_content,
                    "examples": lesson_data.examples,
                    "exercises": lesson_data.exercises,
                }
            )

            # Cache the lesson if cache is available
            if self.cache:
                await self.cache.set(skill_level_enum, slug, lesson_schema)

            return lesson_schema

        except Exception as e:
            logger.error(
                "Error retrieving lesson from database",
                skill_level=skill_level,
                slug=slug,
                error=str(e),
            )
            return None

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
        cache_updates = {}  # skill_level -> {slug: lesson}

        # Process each skill level
        for skill_level, file_paths in lessons_by_level.items():
            logger.debug(
                "Processing skill level", skill_level=skill_level, file_count=len(file_paths)
            )

            skill_cache = {}
            for index, file_path in enumerate(file_paths, 1):
                try:
                    # Load and validate lesson
                    schema = await self.load_lesson(file_path)

                    # Generate slug from title
                    slug = generate_slug(schema.title)
                    if not slug:
                        raise ValueError(f"Cannot generate slug for title: {schema.title}")

                    # Calculate position from file order (10, 20, 30, etc. for easy insertion)
                    position = index * 10

                    # Upsert to database
                    await self.lesson_repo.upsert_lesson(
                        title=schema.title,
                        skill_level=schema.skill_level,
                        slug=slug,
                        position=position,
                        tags=[tag.value for tag in schema.tags],  # Convert Tag enums to strings
                        theory_content=schema.theory_content.model_dump(),
                        examples=schema.examples.model_dump(),
                        exercises=schema.exercises.model_dump(),
                    )

                    # Add to cache update
                    skill_cache[slug] = schema

                    loaded_count += 1
                    logger.info(
                        "Lesson upserted successfully",
                        title=schema.title,
                        skill_level=skill_level,
                        slug=slug,
                        position=position,
                    )

                except Exception as e:
                    error_msg = f"Failed to load lesson {file_path}: {e}"
                    logger.error(error_msg)
                    errors.append(error_msg)
                    # Continue with other lessons

            # Store cache updates for this skill level
            if skill_cache:
                from promptheus.data.models import SkillLevel

                cache_updates[SkillLevel(skill_level.lower())] = skill_cache

        # Update cache with all loaded lessons
        if self.cache and cache_updates:
            for skill_level, lessons in cache_updates.items():
                count = await self.cache.reload_skill_level(skill_level, lessons)
                logger.info(
                    "Skill level cached",
                    skill_level=skill_level.value,
                    lessons_cached=count,
                )

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

    async def reload_lesson(self, file_path: Path) -> bool:
        """Reload a single lesson from file and update cache.

        Args:
            file_path: Path to the lesson JSON file

        Returns:
            True if reload successful, False otherwise
        """
        try:
            logger.info("Reloading lesson from file", file_path=file_path)

            # Load and validate lesson
            schema = await self.load_lesson(file_path)

            # Generate slug
            slug = generate_slug(schema.title)
            if not slug:
                raise ValueError(f"Cannot generate slug for title: {schema.title}")

            # Prepare content for versioning
            content_dict = {
                "title": schema.title,
                "skill_level": schema.skill_level.value,
                "slug": slug,
                "tags": [tag.value for tag in schema.tags],
                "theory_content": schema.theory_content.model_dump(),
                "examples": schema.examples.model_dump(),
                "exercises": schema.exercises.model_dump(),
            }

            # Handle versioning if version manager is available
            version_created = False
            if self.version_manager and self.lesson_repo:
                try:
                    # Find existing lesson
                    existing_lesson = await self.lesson_repo.find_by_slug(schema.skill_level, slug)
                    if existing_lesson:
                        # Check if content changed
                        change_info = self.version_manager.detect_changes(
                            lesson_id=existing_lesson.id,
                            new_content=content_dict,
                            current_hash=None,  # Will be looked up internally if needed
                        )

                        if change_info:
                            # Content changed, create new version
                            # For now, we'll handle versioning through direct repository access
                            # This will be improved when dependency injection is updated
                            from promptheus.data.async_repositories import (
                                AsyncLessonVersionRepository,
                            )

                            version_repo = AsyncLessonVersionRepository(
                                self.lesson_repo.session_maker
                            )
                            current_active = await version_repo.find_active_by_lesson(
                                existing_lesson.id
                            )
                            current_version = current_active.version if current_active else "1.0.0"
                            new_version = self.version_manager.increment_version(current_version)

                            # Create new version
                            await version_repo.create(
                                lesson_id=existing_lesson.id,
                                version=new_version,
                                content_hash=change_info["new_hash"],
                                content_snapshot=content_dict,
                                is_active=True,
                                created_by="hot_reload",
                            )

                            # Deactivate other versions
                            await version_repo.deactivate_other_versions(
                                existing_lesson.id, keep_version_id=None
                            )

                            version_created = True
                            logger.info(
                                "New version created",
                                lesson_id=existing_lesson.id,
                                version=new_version,
                                title=schema.title,
                            )
                        else:
                            logger.debug("No content changes detected", title=schema.title)
                    else:
                        logger.debug("New lesson, no versioning needed yet", title=schema.title)
                except Exception as e:
                    logger.warning(
                        "Version management failed, continuing with reload",
                        error=str(e),
                        title=schema.title,
                    )

            # Update cache if available
            if self.cache:
                await self.cache.set(schema.skill_level, slug, schema)
                logger.info("Lesson reloaded and cached", title=schema.title, slug=slug)

            # Update database if repository available
            if self.lesson_repo:
                # Calculate position (use a default since we don't know the order)
                position = 999

                await self.lesson_repo.upsert_lesson(
                    title=schema.title,
                    skill_level=schema.skill_level,
                    slug=slug,
                    position=position,
                    tags=[tag.value for tag in schema.tags],
                    theory_content=schema.theory_content.model_dump(),
                    examples=schema.examples.model_dump(),
                    exercises=schema.exercises.model_dump(),
                )
                logger.info(
                    "Lesson reloaded and saved to database",
                    title=schema.title,
                    slug=slug,
                    version_created=version_created,
                )

            return True

        except Exception as e:
            logger.error(
                "Failed to reload lesson",
                file_path=file_path,
                error=str(e),
                error_type=type(e).__name__,
            )
            return False

    async def reload_skill_level(self, skill_level_name: str) -> int:
        """Reload all lessons for a skill level from files.

        Args:
            skill_level_name: Name of the skill level (beginner, intermediate, advanced)

        Returns:
            Number of lessons reloaded
        """
        from promptheus.data.models import SkillLevel

        try:
            skill_level = SkillLevel(skill_level_name.lower())
        except ValueError:
            logger.error("Invalid skill level for reload", skill_level=skill_level_name)
            return 0

        logger.info("Reloading skill level from files", skill_level=skill_level_name)

        try:
            # Scan directory for this skill level
            level_path = self.settings.lessons_content_path / skill_level_name
            if not level_path.exists():
                logger.warning("Skill level directory not found", skill_level=skill_level_name)
                return 0

            json_files = sorted(level_path.glob("*.json"))
            logger.debug(
                "Found files for reload",
                skill_level=skill_level_name,
                file_count=len(json_files),
            )

            # Load all lessons for this skill level
            lessons = {}
            for file_path in json_files:
                try:
                    schema = await self.load_lesson(file_path)
                    slug = generate_slug(schema.title)
                    if slug:
                        lessons[slug] = schema
                    else:
                        logger.warning("Skipping lesson without valid slug", file_path=file_path)
                except Exception as e:
                    logger.error(
                        "Failed to load lesson during skill level reload",
                        file_path=file_path,
                        error=str(e),
                    )
                    # Continue with other lessons

            # Update cache atomically
            if self.cache:
                count = await self.cache.reload_skill_level(skill_level, lessons)
                logger.info(
                    "Skill level reloaded into cache",
                    skill_level=skill_level_name,
                    lessons_loaded=count,
                )
                return count
            else:
                logger.warning("No cache available for skill level reload")
                return len(lessons)

        except Exception as e:
            logger.error(
                "Failed to reload skill level",
                skill_level=skill_level_name,
                error=str(e),
                error_type=type(e).__name__,
            )
            return 0

    def _extract_order_index(self, file_path: Path) -> int:
        """Extract order index from filename.

        DEPRECATED: This method is kept for backward compatibility
        but is no longer used since we switched to slug-based identification.

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
