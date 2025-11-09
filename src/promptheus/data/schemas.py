"""Pydantic schemas for lesson content validation."""

import hashlib
import json
import re
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator

from promptheus.data.models import SkillLevel


class Tag(str, Enum):
    """Valid lesson tags."""

    ACADEMIC = "academic"
    ADVANCED_REASONING = "advanced-reasoning"
    AUTOMATION = "automation"
    CLEAR_OBJECTIVES = "clear-objectives"
    COMPLEX_TASKS = "complex-tasks"
    CONSTRAINTS = "constraints"
    CONTEXT_HEAVY = "context-heavy"
    CONTEXT_MANAGEMENT = "context-management"
    CONTEXT_PROVISION = "context-provision"
    CREATIVE = "creative"
    EXAMPLES = "examples"
    FORMATTING = "formatting"
    GENERAL = "general"
    META_PROMPTING = "meta-prompting"
    OPTIMIZATION = "optimization"
    OUTPUT_FORMATTING = "output-formatting"
    PATTERN_RECOGNITION = "pattern-recognition"
    PERSONA = "persona"
    PERSPECTIVE = "perspective"
    PROBLEM_SOLVING = "problem-solving"
    PROFESSIONAL = "professional"
    REASONING = "reasoning"
    REFINEMENT = "refinement"
    ROBUSTNESS = "robustness"
    ROLE_BASED = "role-based"
    ROLE_DEFINITION = "role-definition"
    TESTING = "testing"
    WORKFLOWS = "workflows"


class TheorySection(BaseModel):
    """Individual theory section."""

    content: str = Field(..., min_length=1, max_length=2000, description="Section content text")

    @field_validator("content")
    @classmethod
    def validate_content_not_empty(cls, v: str) -> str:
        """Ensure content is not empty after stripping whitespace."""
        stripped = v.strip()
        if not stripped:
            raise ValueError("content cannot be empty or whitespace-only")
        return stripped


class TheoryContent(BaseModel):
    """Theory content structure."""

    sections: list[TheorySection] = Field(..., min_length=1, description="List of theory sections")

    @field_validator("sections")
    @classmethod
    def validate_at_least_one_section(cls, v: list[TheorySection]) -> list[TheorySection]:
        """Ensure at least one section is provided."""
        if len(v) < 1:
            raise ValueError("at least 1 section required")
        return v


class ExampleComparison(BaseModel):
    """Example comparison structure."""

    bad: str = Field(..., min_length=1, max_length=1000, description="Bad example text")
    bad_reason: str = Field(
        ..., min_length=1, max_length=500, description="Reason why the bad example is poor"
    )
    good: str = Field(..., min_length=1, max_length=1000, description="Good example text")
    good_reason: str = Field(
        ..., min_length=1, max_length=500, description="Reason why the good example is better"
    )

    @field_validator("bad", "bad_reason", "good", "good_reason")
    @classmethod
    def validate_fields_not_empty(cls, v: str) -> str:
        """Ensure fields are not empty after stripping whitespace."""
        stripped = v.strip()
        if not stripped:
            raise ValueError("field cannot be empty or whitespace-only")
        return stripped


class Examples(BaseModel):
    """Examples structure."""

    comparisons: list[ExampleComparison] = Field(
        ..., min_length=1, description="List of example comparisons"
    )

    @field_validator("comparisons")
    @classmethod
    def validate_at_least_one_comparison(
        cls, v: list[ExampleComparison]
    ) -> list[ExampleComparison]:
        """Ensure at least one comparison is provided."""
        if len(v) < 1:
            raise ValueError("at least 1 comparison required")
        return v


class ExerciseScenario(BaseModel):
    """Exercise scenario structure."""

    scenario: str = Field(..., min_length=1, max_length=1000, description="Scenario description")
    task: str = Field(..., min_length=1, max_length=1000, description="Task description")

    @field_validator("scenario", "task")
    @classmethod
    def validate_fields_not_empty(cls, v: str) -> str:
        """Ensure fields are not empty after stripping whitespace."""
        stripped = v.strip()
        if not stripped:
            raise ValueError("field cannot be empty or whitespace-only")
        return stripped


class Exercises(BaseModel):
    """Exercises structure."""

    scenarios: list[ExerciseScenario] = Field(
        ..., min_length=1, description="List of exercise scenarios"
    )

    @field_validator("scenarios")
    @classmethod
    def validate_at_least_one_scenario(cls, v: list[ExerciseScenario]) -> list[ExerciseScenario]:
        """Ensure at least one scenario is provided."""
        if len(v) < 1:
            raise ValueError("at least 1 scenario required")
        return v


class LessonContentSchema(BaseModel):
    """Main lesson content schema."""

    title: str = Field(..., min_length=1, max_length=255, description="Lesson title")
    skill_level: SkillLevel = Field(..., description="Target skill level")
    tags: list[Tag] = Field(..., min_length=1, description="Lesson tags")
    theory_content: TheoryContent = Field(..., description="Theory content structure")
    examples: Examples = Field(..., description="Examples structure")
    exercises: Exercises = Field(..., description="Exercises structure")
    version: str | None = Field(
        default=None, description="Content version hash (auto-generated if not provided)"
    )
    created_at: datetime | None = Field(
        default=None, description="Creation timestamp (auto-generated if not provided)"
    )
    updated_at: datetime | None = Field(
        default=None, description="Update timestamp (auto-generated if not provided)"
    )

    @field_validator("title")
    @classmethod
    def validate_title_not_empty(cls, v: str) -> str:
        """Ensure title is not empty after stripping whitespace."""
        stripped = v.strip()
        if not stripped:
            raise ValueError("title cannot be empty or whitespace-only")
        return stripped

    @field_validator("tags")
    @classmethod
    def validate_tags_not_empty(cls, v: list[Tag]) -> list[Tag]:
        """Ensure at least one tag is provided."""
        if len(v) < 1:
            raise ValueError("at least 1 tag required")
        return v

    @model_validator(mode="after")
    def generate_auto_fields(self) -> "LessonContentSchema":
        """Auto-generate version, created_at, and updated_at if not provided."""
        # Generate version hash from content if not provided
        if self.version is None:
            content_dict = self.model_dump(exclude={"version", "created_at", "updated_at"})
            content_json = json.dumps(content_dict, sort_keys=True, default=str)
            self.version = hashlib.sha256(content_json.encode()).hexdigest()[:16]

        # Set timestamps if not provided
        now = datetime.now(UTC)
        if self.created_at is None:
            self.created_at = now
        if self.updated_at is None:
            self.updated_at = now

        return self

    @classmethod
    def from_json(cls, json_data: dict[str, Any] | str) -> "LessonContentSchema":
        """Create schema instance from JSON data.

        Args:
            json_data: Dictionary or JSON string containing lesson data

        Returns:
            Validated LessonContentSchema instance
        """
        if isinstance(json_data, str):
            json_data = json.loads(json_data)
        return cls.model_validate(json_data)

    def to_json(self) -> str:
        """Convert schema to JSON string.

        Returns:
            JSON representation of the lesson content
        """
        return self.model_dump_json(indent=2)


class LessonVersionInfo(BaseModel):
    """Lesson version information schema."""

    id: int
    version: str
    content_hash: str
    is_active: bool
    created_at: datetime
    created_by: str | None = None

    @field_validator("version")
    @classmethod
    def validate_version_format(cls, v: str) -> str:
        """Validate version string format."""
        if not re.match(r"^\d+\.\d+\.\d+$", v):
            raise ValueError("Version must follow semantic versioning format (X.Y.Z)")
        return v


class LessonVersionDetail(LessonVersionInfo):
    """Detailed lesson version schema with content."""

    content_snapshot: dict[str, Any]


class VersionComparison(BaseModel):
    """Version comparison result schema."""

    lesson_id: int
    changed_fields: list[str]
    version_comparison: dict[str, Any]
    hash_changed: bool
    created_at_diff: dict[str, str | None]


class CreateVersionRequest(BaseModel):
    """Request schema for creating a new version."""

    version: str
    bump_type: str = "patch"

    @field_validator("version")
    @classmethod
    def validate_version_format(cls, v: str) -> str:
        """Validate version string format."""
        if not re.match(r"^\d+\.\d+\.\d+$", v):
            raise ValueError("Version must follow semantic versioning format (X.Y.Z)")
        return v

    @field_validator("bump_type")
    @classmethod
    def validate_bump_type(cls, v: str) -> str:
        """Validate bump type."""
        if v not in ["major", "minor", "patch"]:
            raise ValueError("Bump type must be 'major', 'minor', or 'patch'")
        return v


class RollbackVersionRequest(BaseModel):
    """Request schema for rolling back to a version."""

    target_version: str

    @field_validator("target_version")
    @classmethod
    def validate_version_format(cls, v: str) -> str:
        """Validate version string format."""
        if not re.match(r"^\d+\.\d+\.\d+$", v):
            raise ValueError("Version must follow semantic versioning format (X.Y.Z)")
        return v
