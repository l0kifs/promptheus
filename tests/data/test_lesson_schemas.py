"""Tests for lesson content Pydantic schemas."""

import json
from datetime import UTC, datetime

import pytest
from pydantic import ValidationError as PydanticValidationError

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


class TestTagEnum:
    """Test Tag enum values."""

    def test_valid_tags(self):
        """Test all valid tag values."""
        assert Tag.ACADEMIC == "academic"
        assert Tag.PROFESSIONAL == "professional"
        assert Tag.CREATIVE == "creative"
        assert Tag.GENERAL == "general"

    def test_tag_values_list(self):
        """Test that all tag values are accessible."""
        expected = [
            "academic",
            "advanced-reasoning",
            "automation",
            "clear-objectives",
            "complex-tasks",
            "constraints",
            "context-heavy",
            "context-management",
            "context-provision",
            "creative",
            "examples",
            "formatting",
            "general",
            "meta-prompting",
            "optimization",
            "output-formatting",
            "pattern-recognition",
            "persona",
            "perspective",
            "problem-solving",
            "professional",
            "reasoning",
            "refinement",
            "robustness",
            "role-based",
            "role-definition",
            "testing",
            "workflows",
        ]
        actual = [tag.value for tag in Tag]
        assert actual == expected


class TestTheorySection:
    """Test TheorySection schema."""

    def test_valid_theory_section(self):
        """Test valid theory section creation."""
        section = TheorySection(content="This is valid content.")
        assert section.content == "This is valid content."

    def test_empty_content_raises_error(self):
        """Test that empty content raises validation error."""
        with pytest.raises(PydanticValidationError) as exc_info:
            TheorySection(content="")
        assert "String should have at least 1 character" in str(exc_info.value)

    def test_whitespace_only_content_raises_error(self):
        """Test that whitespace-only content raises validation error."""
        with pytest.raises(PydanticValidationError) as exc_info:
            TheorySection(content="   \n\t  ")
        assert "content cannot be empty or whitespace-only" in str(exc_info.value)

    def test_content_stripped(self):
        """Test that content is stripped of whitespace."""
        section = TheorySection(content="  Content with spaces  ")
        assert section.content == "Content with spaces"


class TestTheoryContent:
    """Test TheoryContent schema."""

    def test_valid_theory_content(self):
        """Test valid theory content with multiple sections."""
        sections = [
            TheorySection(content="First section"),
            TheorySection(content="Second section"),
        ]
        theory = TheoryContent(sections=sections)
        assert len(theory.sections) == 2
        assert theory.sections[0].content == "First section"

    def test_empty_sections_list_raises_error(self):
        """Test that empty sections list raises validation error."""
        with pytest.raises(PydanticValidationError) as exc_info:
            TheoryContent(sections=[])
        assert "List should have at least 1 item" in str(exc_info.value)

    def test_single_section_valid(self):
        """Test that single section is valid."""
        sections = [TheorySection(content="Single section")]
        theory = TheoryContent(sections=sections)
        assert len(theory.sections) == 1


class TestExampleComparison:
    """Test ExampleComparison schema."""

    def test_valid_example_comparison(self):
        """Test valid example comparison creation."""
        comparison = ExampleComparison(
            bad="Bad example",
            bad_reason="Too vague",
            good="Good example",
            good_reason="Specific and clear",
        )
        assert comparison.bad == "Bad example"
        assert comparison.good == "Good example"

    @pytest.mark.parametrize("field", ["bad", "bad_reason", "good", "good_reason"])
    def test_empty_field_raises_error(self, field):
        """Test that empty fields raise validation errors."""
        data = {
            "bad": "Bad example",
            "bad_reason": "Too vague",
            "good": "Good example",
            "good_reason": "Specific and clear",
        }
        data[field] = ""

        with pytest.raises(PydanticValidationError) as exc_info:
            ExampleComparison(**data)
        assert "String should have at least 1 character" in str(exc_info.value)

    @pytest.mark.parametrize("field", ["bad", "bad_reason", "good", "good_reason"])
    def test_whitespace_only_field_raises_error(self, field):
        """Test that whitespace-only fields raise validation errors."""
        data = {
            "bad": "Bad example",
            "bad_reason": "Too vague",
            "good": "Good example",
            "good_reason": "Specific and clear",
        }
        data[field] = "   \n\t  "

        with pytest.raises(PydanticValidationError) as exc_info:
            ExampleComparison(**data)
        assert "field cannot be empty" in str(exc_info.value)


class TestExamples:
    """Test Examples schema."""

    def test_valid_examples(self):
        """Test valid examples with multiple comparisons."""
        comparisons = [
            ExampleComparison(
                bad="Bad example 1",
                bad_reason="Reason 1",
                good="Good example 1",
                good_reason="Reason 1",
            ),
            ExampleComparison(
                bad="Bad example 2",
                bad_reason="Reason 2",
                good="Good example 2",
                good_reason="Reason 2",
            ),
        ]
        examples = Examples(comparisons=comparisons)
        assert len(examples.comparisons) == 2

    def test_empty_comparisons_list_raises_error(self):
        """Test that empty comparisons list raises validation error."""
        with pytest.raises(PydanticValidationError) as exc_info:
            Examples(comparisons=[])
        assert "List should have at least 1 item" in str(exc_info.value)


class TestExerciseScenario:
    """Test ExerciseScenario schema."""

    def test_valid_exercise_scenario(self):
        """Test valid exercise scenario creation."""
        scenario = ExerciseScenario(
            scenario="You need help with a task",
            task="Write a prompt for the AI",
        )
        assert scenario.scenario == "You need help with a task"
        assert scenario.task == "Write a prompt for the AI"

    @pytest.mark.parametrize("field", ["scenario", "task"])
    def test_empty_field_raises_error(self, field):
        """Test that empty fields raise validation errors."""
        data = {
            "scenario": "You need help with a task",
            "task": "Write a prompt for the AI",
        }
        data[field] = ""

        with pytest.raises(PydanticValidationError) as exc_info:
            ExerciseScenario(**data)
        assert "String should have at least 1 character" in str(exc_info.value)


class TestExercises:
    """Test Exercises schema."""

    def test_valid_exercises(self):
        """Test valid exercises with multiple scenarios."""
        scenarios = [
            ExerciseScenario(
                scenario="Scenario 1",
                task="Task 1",
            ),
            ExerciseScenario(
                scenario="Scenario 2",
                task="Task 2",
            ),
        ]
        exercises = Exercises(scenarios=scenarios)
        assert len(exercises.scenarios) == 2

    def test_empty_scenarios_list_raises_error(self):
        """Test that empty scenarios list raises validation error."""
        with pytest.raises(PydanticValidationError) as exc_info:
            Exercises(scenarios=[])
        assert "List should have at least 1 item" in str(exc_info.value)


class TestLessonContentSchema:
    """Test main LessonContentSchema."""

    def test_valid_lesson_content(self):
        """Test valid lesson content creation."""
        lesson_data = {
            "title": "Test Lesson",
            "skill_level": "beginner",
            "tags": ["general", "academic"],
            "theory_content": {
                "sections": [
                    {"content": "Theory section 1"},
                    {"content": "Theory section 2"},
                ]
            },
            "examples": {
                "comparisons": [
                    {
                        "bad": "Bad example",
                        "bad_reason": "Too vague",
                        "good": "Good example",
                        "good_reason": "Specific",
                    }
                ]
            },
            "exercises": {
                "scenarios": [
                    {
                        "scenario": "Test scenario",
                        "task": "Test task",
                    }
                ]
            },
        }

        lesson = LessonContentSchema(**lesson_data)

        assert lesson.title == "Test Lesson"
        assert lesson.skill_level == SkillLevel.BEGINNER
        assert lesson.tags == [Tag.GENERAL, Tag.ACADEMIC]
        assert len(lesson.theory_content.sections) == 2
        assert len(lesson.examples.comparisons) == 1
        assert len(lesson.exercises.scenarios) == 1
        assert lesson.version is not None
        assert lesson.created_at is not None
        assert lesson.updated_at is not None

    def test_auto_generated_version(self):
        """Test that version is auto-generated from content."""
        lesson_data = {
            "title": "Test Lesson",
            "skill_level": "beginner",
            "tags": ["general"],
            "theory_content": {"sections": [{"content": "Content"}]},
            "examples": {
                "comparisons": [
                    {
                        "bad": "Bad",
                        "bad_reason": "Reason",
                        "good": "Good",
                        "good_reason": "Reason",
                    }
                ]
            },
            "exercises": {
                "scenarios": [
                    {
                        "scenario": "Scenario",
                        "task": "Task",
                    }
                ]
            },
        }

        lesson1 = LessonContentSchema(**lesson_data)
        lesson2 = LessonContentSchema(**lesson_data)

        # Same content should generate same version
        assert lesson1.version == lesson2.version
        assert len(lesson1.version) == 16  # SHA256 truncated to 16 chars

    def test_auto_generated_timestamps(self):
        """Test that timestamps are auto-generated."""
        lesson_data = {
            "title": "Test Lesson",
            "skill_level": "beginner",
            "tags": ["general"],
            "theory_content": {"sections": [{"content": "Content"}]},
            "examples": {
                "comparisons": [
                    {
                        "bad": "Bad",
                        "bad_reason": "Reason",
                        "good": "Good",
                        "good_reason": "Reason",
                    }
                ]
            },
            "exercises": {
                "scenarios": [
                    {
                        "scenario": "Scenario",
                        "task": "Task",
                    }
                ]
            },
        }

        before = datetime.now(UTC)
        lesson = LessonContentSchema(**lesson_data)
        after = datetime.now(UTC)

        assert before <= lesson.created_at <= after
        assert before <= lesson.updated_at <= after

    def test_provided_version_preserved(self):
        """Test that provided version is preserved."""
        custom_version = "custom-version-123"
        lesson_data = {
            "title": "Test Lesson",
            "skill_level": "beginner",
            "tags": ["general"],
            "version": custom_version,
            "theory_content": {"sections": [{"content": "Content"}]},
            "examples": {
                "comparisons": [
                    {
                        "bad": "Bad",
                        "bad_reason": "Reason",
                        "good": "Good",
                        "good_reason": "Reason",
                    }
                ]
            },
            "exercises": {
                "scenarios": [
                    {
                        "scenario": "Scenario",
                        "task": "Task",
                    }
                ]
            },
        }

        lesson = LessonContentSchema(**lesson_data)
        assert lesson.version == custom_version

    def test_empty_title_raises_error(self):
        """Test that empty title raises validation error."""
        lesson_data = {
            "title": "",
            "skill_level": "beginner",
            "tags": ["general"],
            "theory_content": {"sections": [{"content": "Content"}]},
            "examples": {
                "comparisons": [
                    {
                        "bad": "Bad",
                        "bad_reason": "Reason",
                        "good": "Good",
                        "good_reason": "Reason",
                    }
                ]
            },
            "exercises": {
                "scenarios": [
                    {
                        "scenario": "Scenario",
                        "task": "Task",
                    }
                ]
            },
        }

        with pytest.raises(PydanticValidationError) as exc_info:
            LessonContentSchema(**lesson_data)
        assert "String should have at least 1 character" in str(exc_info.value)

    def test_invalid_skill_level_raises_error(self):
        """Test that invalid skill level raises validation error."""
        lesson_data = {
            "title": "Test Lesson",
            "skill_level": "expert",  # Invalid
            "tags": ["general"],
            "theory_content": {"sections": [{"content": "Content"}]},
            "examples": {
                "comparisons": [
                    {
                        "bad": "Bad",
                        "bad_reason": "Reason",
                        "good": "Good",
                        "good_reason": "Reason",
                    }
                ]
            },
            "exercises": {
                "scenarios": [
                    {
                        "scenario": "Scenario",
                        "task": "Task",
                    }
                ]
            },
        }

        with pytest.raises(PydanticValidationError) as exc_info:
            LessonContentSchema(**lesson_data)
        assert "skill_level" in str(exc_info.value)

    def test_empty_tags_list_raises_error(self):
        """Test that empty tags list raises validation error."""
        lesson_data = {
            "title": "Test Lesson",
            "skill_level": "beginner",
            "tags": [],  # Empty
            "theory_content": {"sections": [{"content": "Content"}]},
            "examples": {
                "comparisons": [
                    {
                        "bad": "Bad",
                        "bad_reason": "Reason",
                        "good": "Good",
                        "good_reason": "Reason",
                    }
                ]
            },
            "exercises": {
                "scenarios": [
                    {
                        "scenario": "Scenario",
                        "task": "Task",
                    }
                ]
            },
        }

        with pytest.raises(PydanticValidationError) as exc_info:
            LessonContentSchema(**lesson_data)
        assert "List should have at least 1 item" in str(exc_info.value)

    def test_invalid_tag_raises_error(self):
        """Test that invalid tag raises validation error."""
        lesson_data = {
            "title": "Test Lesson",
            "skill_level": "beginner",
            "tags": ["invalid_tag"],  # Invalid tag
            "theory_content": {"sections": [{"content": "Content"}]},
            "examples": {
                "comparisons": [
                    {
                        "bad": "Bad",
                        "bad_reason": "Reason",
                        "good": "Good",
                        "good_reason": "Reason",
                    }
                ]
            },
            "exercises": {
                "scenarios": [
                    {
                        "scenario": "Scenario",
                        "task": "Task",
                    }
                ]
            },
        }

        with pytest.raises(PydanticValidationError) as exc_info:
            LessonContentSchema(**lesson_data)
        assert "tags" in str(exc_info.value)

    def test_from_json_method(self):
        """Test from_json class method."""
        json_data = {
            "title": "Test Lesson",
            "skill_level": "beginner",
            "tags": ["general"],
            "theory_content": {"sections": [{"content": "Content"}]},
            "examples": {
                "comparisons": [
                    {
                        "bad": "Bad",
                        "bad_reason": "Reason",
                        "good": "Good",
                        "good_reason": "Reason",
                    }
                ]
            },
            "exercises": {
                "scenarios": [
                    {
                        "scenario": "Scenario",
                        "task": "Task",
                    }
                ]
            },
        }

        lesson = LessonContentSchema.from_json(json_data)
        assert lesson.title == "Test Lesson"
        assert isinstance(lesson, LessonContentSchema)

    def test_from_json_string_method(self):
        """Test from_json with JSON string."""
        json_string = json.dumps(
            {
                "title": "Test Lesson",
                "skill_level": "beginner",
                "tags": ["general"],
                "theory_content": {"sections": [{"content": "Content"}]},
                "examples": {
                    "comparisons": [
                        {
                            "bad": "Bad",
                            "bad_reason": "Reason",
                            "good": "Good",
                            "good_reason": "Reason",
                        }
                    ]
                },
                "exercises": {
                    "scenarios": [
                        {
                            "scenario": "Scenario",
                            "task": "Task",
                        }
                    ]
                },
            }
        )

        lesson = LessonContentSchema.from_json(json_string)
        assert lesson.title == "Test Lesson"
        assert isinstance(lesson, LessonContentSchema)

    def test_to_json_method(self):
        """Test to_json method."""
        lesson_data = {
            "title": "Test Lesson",
            "skill_level": "beginner",
            "tags": ["general"],
            "theory_content": {"sections": [{"content": "Content"}]},
            "examples": {
                "comparisons": [
                    {
                        "bad": "Bad",
                        "bad_reason": "Reason",
                        "good": "Good",
                        "good_reason": "Reason",
                    }
                ]
            },
            "exercises": {
                "scenarios": [
                    {
                        "scenario": "Scenario",
                        "task": "Task",
                    }
                ]
            },
        }

        lesson = LessonContentSchema(**lesson_data)
        json_str = lesson.to_json()

        # Parse back to verify
        parsed = json.loads(json_str)
        assert parsed["title"] == "Test Lesson"
        assert parsed["version"] is not None


class TestRealLessonValidation:
    """Test validation with real lesson JSON files."""

    @pytest.mark.parametrize(
        "lesson_file",
        [
            "01_introduction_to_prompt_engineering.json",
            "02_defining_ai_roles.json",
            "03_providing_context.json",
            "04_setting_clear_objectives.json",
            "05_specifying_output_format.json",
        ],
    )
    def test_beginner_lessons_validate(self, lesson_file):
        """Test that all beginner lessons validate successfully."""
        import os

        file_path = (
            f"/home/serj/dev/my-github-repos/promptheus-content/lessons/beginner/{lesson_file}"
        )

        if os.path.exists(file_path):
            with open(file_path, encoding="utf-8") as f:
                lesson_data = json.load(f)

            # Should not raise any validation errors
            lesson = LessonContentSchema.from_json(lesson_data)
            assert lesson.title is not None
            assert lesson.skill_level == SkillLevel.BEGINNER
            assert len(lesson.tags) > 0

    @pytest.mark.parametrize(
        "lesson_file",
        [
            "06_chain_of_thought_prompting.json",
        ],
    )
    def test_intermediate_lessons_validate(self, lesson_file):
        """Test that intermediate lessons validate successfully."""
        import os

        file_path = (
            f"/home/serj/dev/my-github-repos/promptheus-content/lessons/intermediate/{lesson_file}"
        )

        if os.path.exists(file_path):
            with open(file_path, encoding="utf-8") as f:
                lesson_data = json.load(f)

            # Should not raise any validation errors
            lesson = LessonContentSchema.from_json(lesson_data)
            assert lesson.title is not None
            assert lesson.skill_level == SkillLevel.INTERMEDIATE
            assert len(lesson.tags) > 0
