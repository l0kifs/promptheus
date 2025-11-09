# Technical Task: Pydantic Lesson Content Schemas

## METADATA

**Task ID:** PRMT-201  
**Name:** Implement Pydantic schemas for lesson content validation  
**Created:** 2025-11-09  
**Priority:** High  
**Complexity Estimate:** 4/10  
**Estimated Time:** 3-4 hours

---

## BUSINESS CONTEXT

### Problem Description
Currently, lesson JSON files are loaded without validation, which can lead to runtime errors if content structure is incorrect. The application stores JSON data in `Column(JSON)` fields without type safety or structure validation. This creates risks of malformed content causing bot failures during user interactions.

### Business Goals
- Ensure all lesson content follows a consistent, validated structure
- Catch content errors at load time rather than runtime
- Provide clear validation error messages for content creators
- Enable IDE autocomplete and type hints for lesson manipulation

### Target Audience
- **Primary:** Backend developers working with lesson content
- **Secondary:** Content creators adding new lessons
- **Tertiary:** QA engineers validating lesson content

### Business Value
- Reduce runtime errors caused by malformed content (prevent user-facing failures)
- Improve developer experience with type safety
- Enable automated content validation in CI/CD pipeline
- Faster content creation with validation feedback

---

## TECHNICAL SPECIFICATION

### Functional Requirements

#### Main Functionality
As a developer, I want Pydantic schemas that validate lesson JSON structure, so that malformed content is caught before reaching production.

#### Detailed Requirements

1. **Theory Content Schema**
   - Description: Validate theory sections structure
   - Fields:
     - `sections`: List of content blocks with `content` (string, 1-500 chars)
   - Constraints: At least 1 section, no empty content strings

2. **Examples Schema**
   - Description: Validate example comparisons
   - Fields:
     - `comparisons`: List of comparison objects
       - `bad`: String (bad example prompt)
       - `bad_reason`: String (explanation why bad)
       - `good`: String (good example prompt)
       - `good_reason`: String (explanation why good)
   - Constraints: At least 1 comparison, all fields required

3. **Exercises Schema**
   - Description: Validate practice scenarios
   - Fields:
     - `scenarios`: List of exercise objects
       - `scenario`: String (context description)
       - `task`: String (what user should do)
   - Constraints: At least 1 scenario, both fields required

4. **Main Lesson Schema**
   - Description: Top-level lesson structure
   - Fields:
     - `title`: String (1-255 chars, unique identifier)
     - `skill_level`: Enum (beginner, intermediate, advanced)
     - `tags`: List of Tag enum values (academic, professional, creative, general)
     - `theory_content`: TheoryContent object
     - `examples`: Examples object
     - `exercises`: Exercises object
     - `version`: String (semantic version, auto-generated from content hash if not provided, default "1.0.0")
     - `created_at`: Datetime (auto-generated)
     - `updated_at`: Datetime (auto-generated)
   - Constraints: All required fields must be present, tags validated against enum

### Non-Functional Requirements

#### Performance
- Schema validation should complete in <10ms per lesson
- Minimal memory overhead for validation

#### Reliability
- Clear, actionable error messages for validation failures
- Should identify exact field and reason for validation error
- No silent failures - all validation errors must be reported

#### Compatibility
- Pydantic v2.x compatible (project uses pydantic>=2.0)
- Compatible with existing JSON structure (backward compatible)
- Must work with both file-based and database-stored JSON

---

## TECHNICAL CONTEXT

### System Architecture
```
┌─────────────────┐
│  JSON Files     │
│  (Content Repo) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐      ┌──────────────────┐
│ Pydantic Schema │─────▶│  Validated Data  │
│   Validation    │      │   (Type-Safe)    │
└─────────────────┘      └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │ Repository Layer │
                         │  (Database)      │
                         └──────────────────┘
```

### Technology Stack
- **Backend:** Python 3.11+, Pydantic 2.x
- **Data Validation:** Pydantic BaseModel, Field validators
- **Testing:** pytest, pytest-asyncio

### Project Structure
```
src/promptheus/
├── data/
│   ├── models.py              ← SQLAlchemy models (existing)
│   └── schemas.py             ← CREATE: Pydantic schemas
└── core/
    └── exceptions.py          ← Use ValidationError

tests/
└── data/
    └── test_lesson_schemas.py ← CREATE: Schema validation tests
```

### Files to Modify

1. **`src/promptheus/data/schemas.py`** (CREATE)
   - Purpose: Define Pydantic schemas for lesson content validation
   - Location: New file in data layer
   - Notes: Keep separate from SQLAlchemy models.py

2. **`src/promptheus/core/exceptions.py`** (EXISTING)
   - Purpose: ValidationError already exists, reuse for schema validation errors
   - Modification: None needed, just import and use

3. **`tests/data/test_lesson_schemas.py`** (CREATE)
   - Purpose: Unit tests for schema validation
   - Location: Mirror structure in tests/

---

## EXAMPLES AND DOCUMENTATION

### Code Examples

#### Example 1: Existing JSON structure
```json
{
  "title": "Introduction to Prompt Engineering",
  "skill_level": "beginner",
  "tags": ["general", "academic"],
  "theory_content": {
    "sections": [
      {
        "content": "Prompt engineering is the art of crafting effective instructions for AI."
      }
    ]
  },
  "examples": {
    "comparisons": [
      {
        "bad": "Tell me about Python",
        "bad_reason": "Too vague - what aspect?",
        "good": "Explain Python list comprehensions to a beginner",
        "good_reason": "Specific topic and audience"
      }
    ]
  },
  "exercises": {
    "scenarios": [
      {
        "scenario": "You need help learning a new concept",
        "task": "Write a prompt asking AI to explain OOP"
      }
    ]
  }
}
```

#### Example 2: Pydantic schema pattern (reference)
```python
from datetime import datetime
from enum import Enum
from hashlib import sha256
import json
from pydantic import BaseModel, Field, field_validator, model_validator

class Tag(str, Enum):
    """Valid lesson tags."""
    ACADEMIC = "academic"
    PROFESSIONAL = "professional"
    CREATIVE = "creative"
    GENERAL = "general"

class ExampleModel(BaseModel):
    """Example Pydantic model with auto-generation."""
    
    name: str = Field(..., min_length=1, max_length=100)
    tags: list[Tag] = Field(..., min_length=1)
    version: str = Field(default="1.0.0")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    @field_validator("name")
    @classmethod
    def validate_name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Name cannot be empty or whitespace")
        return v.strip()
    
    @model_validator(mode="before")
    @classmethod
    def generate_version(cls, data: dict) -> dict:
        """Auto-generate version from content hash if not provided."""
        if "version" not in data or not data["version"]:
            # Generate hash from content for versioning
            content = json.dumps(data, sort_keys=True)
            content_hash = sha256(content.encode()).hexdigest()[:8]
            data["version"] = f"1.0.0-{content_hash}"
        return data
```

#### Example 3: Existing ValidationError usage
```python
from promptheus.core.exceptions import ValidationError

# From models.py
raise ValidationError(
    f"Invalid skill level: {skill_level}",
    details={
        "field": "skill_level",
        "value": skill_level,
        "valid_values": [e.value for e in SkillLevel],
    },
)
```

### Documentation
- [Pydantic v2 Documentation](https://docs.pydantic.dev/latest/)
- [Pydantic Field Validators](https://docs.pydantic.dev/latest/concepts/validators/)
- [Promptheus Data Models](../docs/database-design-document.md)

### Existing Patterns
- **Validation Errors:** Use `ValidationError` from `core/exceptions.py` with structured details
- **Enum Types:** Reuse `SkillLevel` enum from `data/models.py`
- **Field Constraints:** Use Pydantic's `Field()` for length and value constraints
- **Type Hints:** Use Python 3.11+ syntax (`list[str]`, not `List[str]`)

### Known Pitfalls
⚠️ **Important:**
- Don't confuse SQLAlchemy models (`data/models.py`) with Pydantic schemas (`data/schemas.py`)
- Pydantic v2 uses `@field_validator` decorator (not v1's `@validator`)
- JSON fields in database are stored as dict - schema should accept dict/JSON
- Use `model_validate()` for dictionary input, not direct instantiation with validation
- Field names must match JSON keys exactly (case-sensitive)
- Tags must be validated against Tag enum - update existing JSON files if they contain invalid tags
- Version field should be auto-generated using content hash - don't require it in JSON files

---

## ACCEPTANCE CRITERIA

### Scenario Criteria (Given-When-Then)

#### Scenario 1: Valid lesson validates successfully
```gherkin
Given a valid lesson JSON matching the expected structure
When the JSON is validated against LessonContentSchema
Then validation succeeds without errors
And all fields are properly typed and accessible
```

#### Scenario 2: Invalid lesson structure raises error
```gherkin
Given a lesson JSON with missing required field "title"
When the JSON is validated against LessonContentSchema
Then ValidationError is raised
And error message clearly indicates missing "title" field
```

#### Scenario 3: Invalid skill level rejected
```gherkin
Given a lesson JSON with skill_level "expert"
When the JSON is validated against LessonContentSchema
Then ValidationError is raised
And error message lists valid skill_level values
```

#### Scenario 4: Empty sections list rejected
```gherkin
Given a lesson JSON with theory_content.sections = []
When the JSON is validated against TheoryContentSchema
Then ValidationError is raised
And error message indicates "at least 1 section required"
```

### Rules and Constraints
- [ ] All existing lesson JSON files pass validation
- [ ] Schema supports optional versioning fields
- [ ] Error messages include field path (e.g., "theory_content.sections[0].content")
- [ ] Validation performance <10ms per lesson
- [ ] No breaking changes to existing JSON structure

### Testing
- [ ] All unit tests pass successfully
- [ ] Test coverage >= 90% for schemas.py
- [ ] Edge cases tested (empty strings, null values, extra fields)
- [ ] Performance test validates <10ms validation time

### Code Review
- [ ] Code conforms to project style guide (Ruff passes)
- [ ] Type hints on all functions (mypy passes)
- [ ] Docstrings on all schemas and validators
- [ ] No hardcoded values (use constants/enums)

### Documentation
- [ ] Docstrings follow Google style
- [ ] Schema fields documented with Field(description=...)
- [ ] Example usage in module docstring

---

## IMPLEMENTATION PLAN

### Execution Stages

#### Stage 1: Create base Pydantic schemas
**Description:** Implement schemas for theory, examples, exercises
**Tasks:**
- [ ] Create `src/promptheus/data/schemas.py`
- [ ] Import Pydantic BaseModel, Field, field_validator
- [ ] Define `TheorySection` model
- [ ] Define `TheoryContent` model with sections list
- [ ] Define `ExampleComparison` model
- [ ] Define `Examples` model with comparisons list
- [ ] Define `ExerciseScenario` model
- [ ] Define `Exercises` model with scenarios list

**Validation:**
- All models have proper type hints
- Field constraints defined (min_length, max_length)

#### Stage 2: Create main lesson schema
**Description:** Top-level schema combining all parts
**Tasks:**
- [ ] Define `Tag` enum (academic, professional, creative, general)
- [ ] Define `LessonContentSchema` model
- [ ] Add title field (str, 1-255 chars)
- [ ] Add skill_level field (SkillLevel enum)
- [ ] Add tags field (list[Tag])
- [ ] Add theory_content, examples, exercises (nested schemas)
- [ ] Add version field with default_factory for auto-generation
- [ ] Add created_at, updated_at fields with default_factory=datetime.utcnow
- [ ] Import SkillLevel from data.models

**Validation:**
- Schema matches existing JSON structure
- All required fields validated
- Tags validated against Tag enum

#### Stage 3: Add field validators
**Description:** Custom validation logic
**Tasks:**
- [ ] Add validator for non-empty title (strip whitespace)
- [ ] Add validator for tags list (at least 1 tag, all values must be valid Tag enum)
- [ ] Add validator for sections (at least 1 section)
- [ ] Add validator for comparisons (at least 1 comparison)
- [ ] Add validator for scenarios (at least 1 scenario)
- [ ] Add validator for content strings (no empty after strip)
- [ ] Add model_validator for auto-generating version from content hash if not provided
- [ ] Add model_validator for auto-generating created_at/updated_at if not provided

**Validation:**
- All validators catch invalid data
- Error messages are clear and actionable
- Version auto-generation works correctly

#### Stage 4: Write comprehensive tests
**Description:** Unit tests for all validation scenarios
**Tasks:**
- [ ] Create `tests/data/test_lesson_schemas.py`
- [ ] Test valid lesson passes validation
- [ ] Test missing required fields raise errors
- [ ] Test invalid skill_level raises error
- [ ] Test empty sections/comparisons/scenarios raise errors
- [ ] Test whitespace-only strings rejected
- [ ] Test field length constraints
- [ ] Test with real lesson JSON files from promptheus-content

**Validation:**
- All tests pass
- Coverage >= 90%

### Action Order
1. Create schemas.py file and define base models
2. Implement main LessonContentSchema
3. Add all field validators
4. Write and run tests
5. Validate with real lesson JSON files
6. Run Ruff and mypy for code quality

### Dependencies
- No blocking dependencies
- Requires Pydantic 2.x (already in pyproject.toml)
- Requires access to promptheus-content repo for test data

---

## TESTING AND VALIDATION

### Unit Tests
```python
import pytest
from pydantic import ValidationError as PydanticValidationError
from promptheus.data.schemas import LessonContentSchema

def test_valid_lesson_passes_validation():
    # Given
    valid_data = {
        "title": "Introduction to Prompt Engineering",
        "skill_level": "beginner",
        "tags": ["general"],
        "theory_content": {
            "sections": [{"content": "Test content here"}]
        },
        "examples": {
            "comparisons": [{
                "bad": "Bad example",
                "bad_reason": "Reason",
                "good": "Good example",
                "good_reason": "Reason"
            }]
        },
        "exercises": {
            "scenarios": [{"scenario": "Test", "task": "Test task"}]
        }
    }
    
    # When
    lesson = LessonContentSchema.model_validate(valid_data)
    
    # Then
    assert lesson.title == "Introduction to Prompt Engineering"
    assert lesson.skill_level == "beginner"

def test_missing_title_raises_validation_error():
    # Given
    invalid_data = {
        "skill_level": "beginner",
        "tags": ["general"],
        # ... other fields
    }
    
    # When/Then
    with pytest.raises(PydanticValidationError) as exc_info:
        LessonContentSchema.model_validate(invalid_data)
    
    assert "title" in str(exc_info.value)

def test_invalid_skill_level_raises_validation_error():
    # Given
    invalid_data = {
        "title": "Test",
        "skill_level": "expert",  # Invalid
        # ... other fields
    }
    
    # When/Then
    with pytest.raises(PydanticValidationError) as exc_info:
        LessonContentSchema.model_validate(invalid_data)
    
    assert "skill_level" in str(exc_info.value)

def test_empty_sections_raises_validation_error():
    # Given
    invalid_data = {
        "title": "Test",
        "skill_level": "beginner",
        "tags": ["general"],
        "theory_content": {"sections": []},  # Empty
        # ... other fields
    }
    
    # When/Then
    with pytest.raises(PydanticValidationError) as exc_info:
        LessonContentSchema.model_validate(invalid_data)
    
    assert "sections" in str(exc_info.value)
```

### Commands to Run
```bash
# Run schema tests
uv run pytest tests/data/test_lesson_schemas.py -v

# Check coverage
uv run pytest tests/data/test_lesson_schemas.py --cov=src/promptheus/data/schemas --cov-report=term

# Run linter
uv run ruff check src/promptheus/data/schemas.py

# Run type checker
uv run mypy src/promptheus/data/schemas.py
```

### Manual Testing Scenarios
1. **Scenario 1: Validate existing lessons**
   - Steps:
     1. Load JSON from `promptheus-content/lessons/beginner/01_introduction_to_prompt_engineering.json`
     2. Parse JSON with `json.load()`
     3. Validate with `LessonContentSchema.model_validate(data)`
   - Expected result: Validation succeeds, no errors

2. **Scenario 2: Test error messages**
   - Steps:
     1. Create invalid lesson dict (missing title)
     2. Try to validate
     3. Catch PydanticValidationError
     4. Print error messages
   - Expected result: Clear message indicating "title" field missing

---

## ADDITIONAL CONSIDERATIONS

### Risks
- **Risk 1:** Existing JSON files may not match expected structure
  - **Mitigation:** Test with all real lesson files before finalizing schema
  - **Mitigation:** Make schema flexible where needed (optional fields)
  
- **Risk 2:** Pydantic v2 API differences from v1
  - **Mitigation:** Follow Pydantic v2 documentation strictly
  - **Mitigation:** Use `model_validate()` instead of direct instantiation

### Assumptions
- All lesson JSON files in promptheus-content follow similar structure
- SkillLevel enum values are stable (beginner, intermediate, advanced)
- Tags are validated against fixed Tag enum (academic, professional, creative, general)
- Version field is auto-generated from content hash, not required in JSON files
- Existing JSON files may need tag updates to match enum values

### Limitations
- Schema validation is synchronous (not async) - acceptable for file loading
- Does not validate semantic correctness (e.g., whether content makes sense)
- Does not check for duplicate titles across files (handled by database uniqueness)

### Future Improvements
- Add content quality validators (min word count for theory)
- Validate tag consistency against predefined list
- Add schema versioning for backward compatibility
- Generate JSON Schema for external validation tools

### Questions and Unresolved Issues
- [x] **RESOLVED:** Tags will be validated against fixed Tag enum (academic, professional, creative, general)
- [x] **RESOLVED:** Version field will be auto-generated from content hash if not provided in JSON
- [ ] Do we need min/max word count for content fields?

---

## COMPLETION CHECKLIST

### Development
- [ ] schemas.py created with all Pydantic models
- [ ] All field validators implemented
- [ ] Error handling uses clear messages
- [ ] Type hints on all schemas and validators
- [ ] Docstrings on all models and fields

### Testing
- [ ] Unit tests written for all schemas
- [ ] Edge cases tested (empty, null, invalid types)
- [ ] Tests use real lesson JSON files
- [ ] All tests pass
- [ ] Code coverage >= 90%

### Documentation
- [ ] Docstrings follow Google style
- [ ] Schema fields have Field(description=...)
- [ ] Module-level docstring with examples
- [ ] README section added (if needed)

### Code Quality
- [ ] Ruff reports no errors
- [ ] Mypy reports no errors
- [ ] No hardcoded values
- [ ] Follows project naming conventions

### Finalization
- [ ] Changes committed with clear message: `feat(data): add Pydantic schemas for lesson validation`
- [ ] All existing lesson JSON files validated successfully
- [ ] Task marked as "Ready for Review"

---

**Notes:**
- This task is independent and can be completed without dependencies on other tasks
- Schema validation will be used by subsequent tasks (lesson loader service)
- Keep schemas flexible enough to support future content structure evolution
