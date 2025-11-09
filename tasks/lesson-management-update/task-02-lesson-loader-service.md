# Technical Task: Lesson Loader Service

## METADATA

**Task ID:** PRMT-202  
**Name:** Implement lesson loader service for JSON file reading and validation  
**Created:** 2025-11-09  
**Priority:** High  
**Complexity Estimate:** 6/10  
**Estimated Time:** 5-6 hours

---

## BUSINESS CONTEXT

### Problem Description
Currently, lessons are loaded from JSON files via an external seeding script in the promptheus-content repository. This creates a disconnect between the application and its content, requires manual database seeding, and lacks integration with the application lifecycle. The system needs an organic way to load, validate, and manage lesson content directly from JSON files.

### Business Goals
- Make lesson loading an integral part of the application startup
- Enable automatic content discovery from configured directory
- Provide centralized error handling for content loading
- Support both initial loading and content updates without database reseeding

### Target Audience
- **Primary:** Backend developers maintaining the application
- **Secondary:** DevOps engineers deploying the application
- **Tertiary:** Content creators updating lesson files

### Business Value
- Eliminate manual seeding step in deployment process
- Reduce time-to-production for content updates (no database migration needed)
- Enable content validation before application starts (fail-fast principle)
- Simplify local development setup (no separate seeding script)

---

## TECHNICAL SPECIFICATION

### Functional Requirements

#### Main Functionality
As an application, I want to automatically load and validate lessons from JSON files on startup, so that content is always synchronized with the file system.

#### Detailed Requirements

1. **Directory Scanner**
   - Description: Scan lessons directory structure and discover all JSON files
   - Behavior:
     - Recursively scan `lessons/beginner/`, `lessons/intermediate/`, `lessons/advanced/`
     - Filter for `*.json` files only
     - Determine skill level from parent directory name
     - Sort files alphabetically within each skill level
   - Constraints: Handle missing directories gracefully (log warning, continue)

2. **JSON File Reader**
   - Description: Read and parse JSON files with error handling
   - Behavior:
     - Read file with UTF-8 encoding
     - Parse JSON to Python dict
     - Catch file I/O errors (missing file, permission denied)
     - Catch JSON parsing errors (malformed JSON)
   - Constraints: Return detailed error with filename and line number for debugging

3. **Content Validator**
   - Description: Validate lesson content using Pydantic schemas
   - Behavior:
     - Use `LessonContentSchema.model_validate()` from Task PRMT-201
     - Catch Pydantic ValidationError
     - Enrich error with filename context
   - Constraints: All validation errors must be logged before raising

4. **Lesson Mapper**
   - Description: Map validated schema to database model
   - Behavior:
     - Convert Pydantic model to dict for database insert
     - Infer order_index from file sort order (temporary, until Task PRMT-203)
     - Handle optional fields (version, timestamps)
   - Constraints: Preserve all content structure in JSON columns

5. **Batch Loader**
   - Description: Load all lessons in order
   - Behavior:
     - Load all lesson files for all skill levels
     - Validate each lesson
     - Collect all errors before failing (don't stop on first error)
     - Return list of validated lesson data ready for persistence
   - Constraints: Transaction-safe (all-or-nothing for database operations)

### Non-Functional Requirements

#### Performance
- Load and validate 50 lessons in <2 seconds
- Startup time impact <3 seconds for typical content volume
- Memory usage <50MB for all loaded content

#### Security
- Path traversal protection (validate paths are within lessons directory)
- File size limit (max 1MB per JSON file)
- No arbitrary code execution from JSON content

#### Reliability
- Clear error messages with filename, line number, validation issue
- Graceful degradation (log errors, don't crash app)
- Idempotent loading (can be run multiple times safely)

#### Compatibility
- Works with existing JSON structure from promptheus-content
- Compatible with async application initialization
- Supports both local filesystem and mounted volumes (Docker)

---

## TECHNICAL CONTEXT

### System Architecture
```
┌─────────────────────┐
│  Lessons Directory  │
│  /path/to/lessons   │
│  ├─ beginner/       │
│  ├─ intermediate/   │
│  └─ advanced/       │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐      ┌────────────────────┐
│ LessonLoaderService │─────▶│ Pydantic Schemas   │
│  - scan_directory() │      │  (Validation)      │
│  - load_lesson()    │      └────────────────────┘
│  - validate()       │
│  - batch_load()     │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐      ┌────────────────────┐
│ AsyncLessonRepo     │─────▶│  PostgreSQL        │
│  - create()         │      │  Database          │
│  - upsert()         │      └────────────────────┘
└─────────────────────┘
```

### Technology Stack
- **Backend:** Python 3.11+, asyncio
- **File I/O:** pathlib.Path, json
- **Validation:** Pydantic (from Task PRMT-201)
- **Database:** SQLAlchemy async, PostgreSQL
- **Configuration:** Pydantic Settings

### Project Structure
```
src/promptheus/
├── config/
│   └── settings.py            ← ADD: LESSONS_CONTENT_PATH
├── data/
│   ├── schemas.py             ← From Task PRMT-201
│   ├── models.py              ← Existing
│   ├── async_repositories.py ← Modify: add upsert_lesson()
│   └── lesson_loader.py       ← CREATE: LessonLoaderService
└── main.py                    ← Modify: call loader on startup

tests/
└── data/
    └── test_lesson_loader.py  ← CREATE: Loader tests

# Content repository (separate repo)
promptheus-content/
└── lessons/
    ├── beginner/
    ├── intermediate/
    └── advanced/
```

### Files to Modify

1. **`src/promptheus/data/lesson_loader.py`** (CREATE)
   - Purpose: Service for loading lessons from JSON files
   - Class: `LessonLoaderService`
   - Methods: `scan_directory()`, `load_lesson()`, `validate_lesson()`, `batch_load_all()`
   - Notes: Use async file I/O for scalability

2. **`src/promptheus/config/settings.py`** (MODIFY)
   - Purpose: Add configuration for lessons content path
   - Add field: `lessons_content_path: Path`
   - Default: `Path(__file__).parent.parent.parent.parent / "promptheus-content" / "lessons"`
   - Notes: Allow override via environment variable `LESSONS_CONTENT_PATH`

3. **`src/promptheus/data/async_repositories.py`** (MODIFY)
   - Purpose: Add upsert capability for lessons
   - Add method: `async def upsert_lesson()` to `AsyncLessonRepository`
   - Behavior: Insert if not exists, update if exists (by title uniqueness)
   - Notes: Use SQLAlchemy's `insert().on_conflict_do_update()`

4. **`src/promptheus/main.py`** (MODIFY)
   - Purpose: Initialize lesson loading on application startup
   - Add: `await lesson_loader.batch_load_all()` in startup hook
   - Notes: Use FastAPI lifespan context manager

5. **`tests/data/test_lesson_loader.py`** (CREATE)
   - Purpose: Unit and integration tests for loader service
   - Test fixtures: Create temporary lesson JSON files
   - Test cases: Valid load, invalid JSON, missing files, validation errors

---

## EXAMPLES AND DOCUMENTATION

### Code Examples

#### Example 1: Path scanning pattern
```python
from pathlib import Path

def scan_lessons_directory(base_path: Path) -> dict[str, list[Path]]:
    """Scan lessons directory and organize by skill level."""
    lessons_by_level = {}
    
    for skill_level in ["beginner", "intermediate", "advanced"]:
        level_dir = base_path / skill_level
        if not level_dir.exists():
            logger.warning(f"Directory not found: {level_dir}")
            lessons_by_level[skill_level] = []
            continue
        
        # Get all JSON files, sorted alphabetically
        json_files = sorted(level_dir.glob("*.json"))
        lessons_by_level[skill_level] = json_files
        logger.info(f"Found {len(json_files)} lessons in {skill_level}")
    
    return lessons_by_level
```

#### Example 2: JSON loading with error handling
```python
import json
from pathlib import Path

def load_json_file(file_path: Path) -> dict:
    """Load and parse JSON file with error handling."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError as e:
        raise FileNotFoundError(f"Lesson file not found: {file_path}") from e
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {file_path}: {e}") from e
    except Exception as e:
        raise RuntimeError(f"Error reading {file_path}: {e}") from e
```

#### Example 3: FastAPI startup pattern
```python
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Loading lessons from content repository")
    await lesson_loader.batch_load_all()
    logger.info("Lessons loaded successfully")
    yield
    # Shutdown (cleanup if needed)

app = FastAPI(lifespan=lifespan)
```

#### Example 4: SQLAlchemy upsert pattern
```python
from sqlalchemy.dialects.postgresql import insert

async def upsert_lesson(session: AsyncSession, lesson_data: dict) -> Lesson:
    """Insert or update lesson by title."""
    stmt = insert(Lesson).values(**lesson_data)
    stmt = stmt.on_conflict_do_update(
        index_elements=["title"],  # Unique constraint
        set_={
            "skill_level": stmt.excluded.skill_level,
            "tags": stmt.excluded.tags,
            "theory_content": stmt.excluded.theory_content,
            "examples": stmt.excluded.examples,
            "exercises": stmt.excluded.exercises,
        }
    )
    await session.execute(stmt)
    await session.commit()
```

### Documentation
- [Python pathlib](https://docs.python.org/3/library/pathlib.html)
- [Pydantic model_validate](https://docs.pydantic.dev/latest/concepts/models/#model_validate)
- [SQLAlchemy ON CONFLICT](https://docs.sqlalchemy.org/en/20/dialects/postgresql.html#insert-on-conflict-upsert)
- [FastAPI lifespan](https://fastapi.tiangolo.com/advanced/events/)

### Existing Patterns
- **Dependency Injection:** Use `DependencyContainer` for LessonLoaderService
- **Async Repositories:** Follow pattern in `AsyncLessonRepository`
- **Configuration:** Use Pydantic Settings pattern from `config/settings.py`
- **Logging:** Use loguru with structured context (user_id, lesson_id, etc.)

### Known Pitfalls
⚠️ **Important:**
- **Async file I/O:** Use `aiofiles` library for async file reading (add to dependencies)
- **Path traversal:** Validate all paths are within `lessons_content_path`
- **Order index:** Must maintain order during migration period (until Task PRMT-203)
- **Database transactions:** Wrap batch loading in transaction for atomicity
- **Relative imports:** Ensure paths work in Docker containers (use absolute paths)

---

## ACCEPTANCE CRITERIA

### Scenario Criteria (Given-When-Then)

#### Scenario 1: Successful batch loading on startup
```gherkin
Given lessons directory contains valid JSON files
And application is starting up
When LessonLoaderService.batch_load_all() is called
Then all lessons are loaded and validated
And lessons are inserted into database
And application startup completes successfully
And logs show "X lessons loaded successfully"
```

#### Scenario 2: Invalid JSON file detected
```gherkin
Given lessons directory contains a malformed JSON file
When LessonLoaderService.batch_load_all() is called
Then JSONDecodeError is caught
And error is logged with filename and line number
And application startup fails with clear error message
```

#### Scenario 3: Validation failure handled
```gherkin
Given lessons directory contains JSON with missing "title" field
When LessonLoaderService.load_lesson() is called
Then Pydantic ValidationError is raised
And error includes field name and validation reason
And error is logged with filename context
And loading continues for other lessons (collect all errors)
```

#### Scenario 4: Missing directory handled gracefully
```gherkin
Given "intermediate" directory does not exist
When LessonLoaderService.scan_directory() is called
Then warning is logged about missing directory
And loading continues for beginner and advanced
And no exception is raised
```

#### Scenario 5: Upsert updates existing lesson
```gherkin
Given database already contains lesson "Introduction to Prompting"
And JSON file for same lesson has updated content
When LessonLoaderService.batch_load_all() is called
Then existing lesson is updated (not duplicated)
And updated_at timestamp is refreshed
And content reflects latest JSON
```

### Rules and Constraints
- [ ] All validation errors include filename and field path
- [ ] Batch loading is atomic (all-or-nothing for database)
- [ ] Order of lessons is deterministic (alphabetical by filename)
- [ ] Startup fails if any critical lesson fails to load
- [ ] File size must be <1MB per lesson JSON
- [ ] Paths must be within configured lessons directory

### Testing
- [ ] All unit tests pass successfully
- [ ] Integration test with real lesson files passes
- [ ] Test coverage >= 85% for lesson_loader.py
- [ ] Edge cases tested (empty directory, malformed JSON, permission errors)

### Code Review
- [ ] Code conforms to project style guide (Ruff passes)
- [ ] Type hints on all functions (mypy passes)
- [ ] Docstrings on all public methods
- [ ] Error handling is comprehensive
- [ ] Logging provides clear operational visibility

### Performance
- [ ] Load 50 lessons in <2 seconds
- [ ] Startup time overhead <3 seconds
- [ ] Memory usage <50MB for loaded content

---

## IMPLEMENTATION PLAN

### Execution Stages

#### Stage 1: Configuration and setup
**Description:** Add configuration for lessons content path
**Tasks:**
- [ ] Update `src/promptheus/config/settings.py`
- [ ] Add `lessons_content_path: Path` field with validator
- [ ] Add environment variable `LESSONS_CONTENT_PATH`
- [ ] Set default path pointing to promptheus-content/lessons
- [ ] Add validation to ensure path exists and is directory

**Validation:**
- Settings loads successfully with default path
- Environment variable override works

#### Stage 2: Create LessonLoaderService skeleton
**Description:** Define service class and method signatures
**Tasks:**
- [ ] Create `src/promptheus/data/lesson_loader.py`
- [ ] Define `LessonLoaderService` class
- [ ] Add constructor with dependencies (settings, lesson_repo, schemas)
- [ ] Define method signatures:
  - `scan_directory() -> dict[str, list[Path]]`
  - `load_lesson_file(path: Path) -> dict`
  - `validate_lesson(data: dict, filepath: Path) -> LessonContentSchema`
  - `batch_load_all() -> int`
- [ ] Add type hints and docstrings

**Validation:**
- Class structure follows project patterns
- Type hints pass mypy checks

#### Stage 3: Implement directory scanning
**Description:** Scan and discover lesson files
**Tasks:**
- [ ] Implement `scan_directory()` method
- [ ] Use pathlib to scan beginner/intermediate/advanced subdirs
- [ ] Filter for *.json files
- [ ] Sort files alphabetically within each level
- [ ] Handle missing directories (log warning, continue)
- [ ] Add path traversal validation

**Validation:**
- Returns dict mapping skill_level to sorted file paths
- Missing directories don't crash

#### Stage 4: Implement file loading
**Description:** Read and parse JSON files
**Tasks:**
- [ ] Add `aiofiles` to project dependencies
- [ ] Implement `load_lesson_file()` async method
- [ ] Use async file I/O for reading
- [ ] Parse JSON to dict
- [ ] Catch FileNotFoundError, JSONDecodeError
- [ ] Log detailed errors with filename

**Validation:**
- Valid JSON loads successfully
- Malformed JSON raises clear error

#### Stage 5: Implement validation
**Description:** Validate lesson content with Pydantic
**Tasks:**
- [ ] Implement `validate_lesson()` method
- [ ] Call `LessonContentSchema.model_validate(data)`
- [ ] Catch Pydantic ValidationError
- [ ] Enrich error with filename context
- [ ] Log validation errors before raising

**Validation:**
- Valid lessons pass validation
- Invalid lessons fail with clear error

#### Stage 6: Implement batch loading
**Description:** Load all lessons and persist to database
**Tasks:**
- [ ] Implement `batch_load_all()` async method
- [ ] Call `scan_directory()` to get all files
- [ ] Loop through all skill levels and files
- [ ] For each file: load, validate, convert to dict
- [ ] Collect all validated lessons
- [ ] Call repository to upsert all lessons
- [ ] Return count of loaded lessons
- [ ] Handle errors (collect all, then fail if any critical)

**Validation:**
- All valid lessons loaded to database
- Returns correct count

#### Stage 7: Add upsert to repository
**Description:** Implement upsert capability in AsyncLessonRepository
**Tasks:**
- [ ] Open `src/promptheus/data/async_repositories.py`
- [ ] Add `async def upsert_lesson()` method
- [ ] Use SQLAlchemy's `insert().on_conflict_do_update()`
- [ ] Handle conflict on unique constraint (title)
- [ ] Update all fields except id and created_at
- [ ] Add logging for insert vs update

**Validation:**
- New lessons are inserted
- Existing lessons are updated

#### Stage 8: Integrate with application startup
**Description:** Call loader on FastAPI startup
**Tasks:**
- [ ] Open `src/promptheus/main.py`
- [ ] Create or update `lifespan` context manager
- [ ] Instantiate `LessonLoaderService` from container
- [ ] Call `await lesson_loader.batch_load_all()` on startup
- [ ] Log success/failure
- [ ] Add error handling (log and re-raise to prevent startup)

**Validation:**
- Application starts successfully with lessons loaded
- Startup logs show lesson count

#### Stage 9: Write comprehensive tests
**Description:** Unit and integration tests
**Tasks:**
- [ ] Create `tests/data/test_lesson_loader.py`
- [ ] Write test fixtures (temporary lesson JSON files)
- [ ] Test `scan_directory()` with various directory structures
- [ ] Test `load_lesson_file()` with valid/invalid JSON
- [ ] Test `validate_lesson()` with valid/invalid content
- [ ] Test `batch_load_all()` end-to-end
- [ ] Test error scenarios (missing files, permission errors)
- [ ] Test with real lesson files from promptheus-content

**Validation:**
- All tests pass
- Coverage >= 85%

### Action Order
1. Add configuration (Stage 1)
2. Create service skeleton (Stage 2)
3. Implement directory scanning (Stage 3)
4. Implement file loading (Stage 4)
5. Implement validation (Stage 5)
6. Implement batch loading (Stage 6)
7. Add repository upsert (Stage 7)
8. Integrate with startup (Stage 8)
9. Write tests (Stage 9)
10. Test with real lesson files
11. Validate startup behavior

### Dependencies
- **Blocks on:** Task PRMT-201 (Pydantic schemas must exist)
- **Blocked by:** None
- **Requires:** `aiofiles` package (add to pyproject.toml)

---

## TESTING AND VALIDATION

### Unit Tests
```python
import pytest
import json
from pathlib import Path
from promptheus.data.lesson_loader import LessonLoaderService

@pytest.fixture
def temp_lessons_dir(tmp_path):
    """Create temporary lessons directory structure."""
    lessons_dir = tmp_path / "lessons"
    beginner_dir = lessons_dir / "beginner"
    beginner_dir.mkdir(parents=True)
    
    # Create valid lesson file
    lesson_data = {
        "title": "Test Lesson",
        "skill_level": "beginner",
        "tags": ["test"],
        "theory_content": {"sections": [{"content": "Test content"}]},
        "examples": {"comparisons": [{
            "bad": "Bad", "bad_reason": "Reason",
            "good": "Good", "good_reason": "Reason"
        }]},
        "exercises": {"scenarios": [{"scenario": "Test", "task": "Test"}]}
    }
    
    lesson_file = beginner_dir / "test_lesson.json"
    lesson_file.write_text(json.dumps(lesson_data))
    
    return lessons_dir

@pytest.mark.asyncio
async def test_scan_directory_finds_all_lessons(temp_lessons_dir):
    # Given
    loader = LessonLoaderService(settings, lesson_repo)
    
    # When
    lessons_by_level = loader.scan_directory(temp_lessons_dir)
    
    # Then
    assert "beginner" in lessons_by_level
    assert len(lessons_by_level["beginner"]) == 1
    assert lessons_by_level["beginner"][0].name == "test_lesson.json"

@pytest.mark.asyncio
async def test_load_lesson_file_parses_valid_json(temp_lessons_dir):
    # Given
    loader = LessonLoaderService(settings, lesson_repo)
    lesson_path = temp_lessons_dir / "beginner" / "test_lesson.json"
    
    # When
    data = await loader.load_lesson_file(lesson_path)
    
    # Then
    assert data["title"] == "Test Lesson"
    assert data["skill_level"] == "beginner"

@pytest.mark.asyncio
async def test_load_lesson_file_raises_on_invalid_json(tmp_path):
    # Given
    invalid_file = tmp_path / "invalid.json"
    invalid_file.write_text("{invalid json")
    loader = LessonLoaderService(settings, lesson_repo)
    
    # When/Then
    with pytest.raises(ValueError, match="Invalid JSON"):
        await loader.load_lesson_file(invalid_file)

@pytest.mark.asyncio
async def test_validate_lesson_accepts_valid_content():
    # Given
    loader = LessonLoaderService(settings, lesson_repo)
    valid_data = {
        "title": "Test Lesson",
        "skill_level": "beginner",
        # ... full valid structure
    }
    
    # When
    lesson = loader.validate_lesson(valid_data, Path("test.json"))
    
    # Then
    assert lesson.title == "Test Lesson"

@pytest.mark.asyncio
async def test_validate_lesson_rejects_invalid_content():
    # Given
    loader = LessonLoaderService(settings, lesson_repo)
    invalid_data = {"title": "Test"}  # Missing required fields
    
    # When/Then
    with pytest.raises(ValueError, match="Validation failed"):
        loader.validate_lesson(invalid_data, Path("test.json"))

@pytest.mark.asyncio
async def test_batch_load_all_loads_all_lessons(temp_lessons_dir, mock_repo):
    # Given
    loader = LessonLoaderService(settings, mock_repo)
    loader.lessons_path = temp_lessons_dir
    
    # When
    count = await loader.batch_load_all()
    
    # Then
    assert count == 1
    mock_repo.upsert_lesson.assert_called_once()
```

### Commands to Run
```bash
# Run loader tests
uv run pytest tests/data/test_lesson_loader.py -v

# Check coverage
uv run pytest tests/data/test_lesson_loader.py --cov=src/promptheus/data/lesson_loader --cov-report=term

# Run full test suite
uv run pytest

# Test with real lessons (manual)
uv run python -m promptheus.data.lesson_loader

# Run application and check startup
uv run uvicorn promptheus.main:app --reload
```

### Manual Testing Scenarios
1. **Scenario 1: Fresh startup with valid lessons**
   - Steps:
     1. Clear database
     2. Start application with `uv run uvicorn promptheus.main:app`
     3. Check logs for "X lessons loaded successfully"
     4. Query database: `SELECT COUNT(*) FROM lesson;`
   - Expected result: All lessons loaded, count matches file count

2. **Scenario 2: Restart with existing lessons (upsert)**
   - Steps:
     1. Start application (lessons already in DB)
     2. Modify one lesson JSON file
     3. Restart application
     4. Check database for updated content
   - Expected result: Modified lesson updated, others unchanged

3. **Scenario 3: Startup with invalid lesson**
   - Steps:
     1. Create invalid lesson JSON (missing field)
     2. Start application
     3. Check logs for validation error
   - Expected result: Clear error message, application fails to start

---

## ADDITIONAL CONSIDERATIONS

### Risks
- **Risk 1:** Large content volume slows startup
  - **Mitigation:** Set file size limit (1MB per file)
  - **Mitigation:** Consider async parallel loading (future optimization)
  
- **Risk 2:** File permission issues in Docker
  - **Mitigation:** Ensure proper volume mounting in docker-compose
  - **Mitigation:** Add clear error message for permission errors
  
- **Risk 3:** Database unavailable during startup
  - **Mitigation:** Use retry logic with exponential backoff
  - **Mitigation:** Fail startup gracefully with clear message

### Assumptions
- Lesson JSON files are relatively small (<1MB each)
- Content repository is available as mounted volume or sibling directory
- Database is available during application startup
- Order index is still needed (temporary, until Task PRMT-203)

### Limitations
- Synchronous loading (one file at a time) - acceptable for <100 files
- Requires restart to reload content (until hot reload in Task PRMT-204)
- File-based only (no support for S3 or remote storage yet)

### Future Improvements
- Parallel loading for faster startup
- Incremental loading (only changed files)
- Support for remote content sources (S3, Git)
- Dry-run mode (validate without persisting)
- Progress reporting for large content sets

### Questions and Unresolved Issues
- [ ] Should we load all lessons into memory or stream to database?
  - **Decision:** Stream to database (lower memory footprint)
- [ ] What happens if lesson title changes in JSON (will create duplicate)?
  - **Decision:** Title is unique identifier, changing it creates new lesson
- [ ] Should we delete lessons not found in files?
  - **Decision:** No, loader only adds/updates (manual deletion required)

---

## COMPLETION CHECKLIST

### Development
- [ ] LessonLoaderService implemented with all methods
- [ ] Configuration added for lessons content path
- [ ] Upsert method added to AsyncLessonRepository
- [ ] Integrated with FastAPI startup lifecycle
- [ ] Error handling comprehensive and clear
- [ ] Logging provides operational visibility

### Testing
- [ ] Unit tests written for all service methods
- [ ] Integration test with temp filesystem
- [ ] Edge cases tested (errors, missing files, invalid JSON)
- [ ] Tested with real lesson files from promptheus-content
- [ ] All tests pass
- [ ] Code coverage >= 85%

### Documentation
- [ ] Docstrings on all methods (Google style)
- [ ] Configuration documented in settings
- [ ] README updated with content setup instructions
- [ ] Error messages are clear and actionable

### Code Quality
- [ ] Ruff reports no errors
- [ ] Mypy reports no errors
- [ ] Follows async patterns consistently
- [ ] No hardcoded paths

### Performance
- [ ] Startup time tested (<3 seconds overhead)
- [ ] Memory usage acceptable (<50MB)

### Finalization
- [ ] aiofiles added to pyproject.toml dependencies
- [ ] Changes committed: `feat(data): add lesson loader service for JSON content`
- [ ] Tested in local environment with real content
- [ ] Task marked as "Ready for Review"

---

**Notes:**
- This task depends on Task PRMT-201 (Pydantic schemas)
- Creates foundation for Task PRMT-204 (hot reload) and Task PRMT-205 (versioning)
- Order index handling is temporary - will be replaced in Task PRMT-203
