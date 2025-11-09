# Technical Task: Lesson Content Versioning

## METADATA

**Task ID:** PRMT-205  
**Name:** Implement lesson content versioning with metadata tracking  
**Created:** 2025-11-09  
**Priority:** Low  
**Complexity Estimate:** 6/10  
**Estimated Time:** 5-7 hours

---

## BUSINESS CONTEXT

### Problem Description
Currently, there's no tracking of lesson content changes over time. When content is updated, the previous version is lost, making it impossible to revert changes, understand evolution, or A/B test different versions. Content creators need visibility into what changed and when, and the system needs to support gradual rollouts and rollback capabilities.

### Business Goals
- Track all lesson content changes with timestamps and metadata
- Enable reverting to previous content versions
- Support A/B testing different lesson versions
- Provide audit trail for content evolution
- Enable gradual rollout of content updates

### Target Audience
- **Primary:** Content creators tracking and managing changes
- **Secondary:** Product managers analyzing content performance
- **Tertiary:** Backend developers debugging content issues

### Business Value
- Confidence to experiment with content (easy rollback)
- Data-driven content optimization (version comparison)
- Compliance and audit requirements (change history)
- Reduced risk in content updates (gradual rollout)

---

## TECHNICAL SPECIFICATION

### Functional Requirements

#### Main Functionality
As a system, I want to track all versions of lesson content with metadata, so that changes can be reviewed, compared, and reverted.

#### Detailed Requirements

1. **Version Metadata**
   - Description: Track version information for each lesson
   - Fields:
     - `version`: Semantic version string (e.g., "1.2.0")
     - `created_at`: Timestamp of version creation
     - `created_by`: Author/system that created version
     - `change_description`: Optional description of changes
     - `is_active`: Boolean flag for currently active version
   - Constraints: Version string must follow semver format

2. **Content Hashing**
   - Description: Generate hash of content for change detection
   - Behavior:
     - Hash entire lesson content (theory + examples + exercises)
     - Use SHA-256 for uniqueness
     - Compare hashes to detect actual content changes
     - Store hash with each version
   - Constraints: Identical content must produce identical hash

3. **Version Storage**
   - Description: Store lesson versions in database
   - Approach: New table `lesson_version` with foreign key to `lesson`
   - Fields:
     - `id`: Primary key
     - `lesson_id`: Foreign key to lesson table
     - `version`: Semantic version string
     - `content_hash`: SHA-256 hash of content
     - `theory_content`, `examples`, `exercises`: JSON content snapshot
     - `created_at`, `created_by`, `change_description`: Metadata
     - `is_active`: Boolean (only one active version per lesson)
   - Constraints: Unique constraint on (lesson_id, version)

4. **Automatic Versioning**
   - Description: Auto-increment version on content changes
   - Rules:
     - Patch increment (x.y.Z+1) for minor content tweaks
     - Minor increment (x.Y+1.0) for new examples or exercises
     - Major increment (X+1.0.0) for theory rewrites
     - Auto-detect change type by comparing content
   - Behavior: Create new version row on hot reload if content hash changed

5. **Version Comparison**
   - Description: Compare two versions of same lesson
   - Behavior:
     - Accept two version identifiers
     - Return diff of content (added/removed/changed sections)
     - Highlight changes in theory, examples, exercises
   - Output: Structured diff with field-level granularity

6. **Version Rollback**
   - Description: Activate previous version as current
   - Behavior:
     - Accept version identifier
     - Set specified version as `is_active=True`
     - Set all other versions as `is_active=False`
     - Update cache with rolled-back content
     - Log rollback event
   - Constraints: Atomic operation (all-or-nothing)

### Non-Functional Requirements

#### Performance
- Version creation: <50ms overhead on hot reload
- Version lookup: <10ms (indexed query)
- Version comparison: <100ms for typical lesson
- Storage overhead: ~5MB per 100 versions (compressed JSON)

#### Reliability
- Version data immutable (never update, only insert)
- Active version flag managed transactionally
- Content hash collisions virtually impossible (SHA-256)
- Rollback is atomic and reversible

#### Compatibility
- Backward compatible (existing lessons get version "1.0.0")
- Integrates with hot reload from Task PRMT-204
- Works with slug-based identification from Task PRMT-203

---

## TECHNICAL CONTEXT

### System Architecture
```
┌─────────────────────┐
│  Lesson Content     │
│  (JSON File)        │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐      ┌────────────────────┐
│  Content Hasher     │─────▶│  SHA-256 Hash      │
│  - hash_content()   │      │  (Change Detection)│
└─────────────────────┘      └────────────────────┘
           │
           ▼
┌─────────────────────┐
│  Version Manager    │
│  - detect_changes() │
│  - create_version() │
│  - rollback()       │
└──────────┬──────────┘
           │
           ├────────────┐
           ▼            ▼
┌─────────────────┐  ┌──────────────────┐
│  lesson table   │  │  lesson_version  │
│  (current)      │  │  (history)       │
└─────────────────┘  └──────────────────┘
```

### Technology Stack
- **Backend:** Python 3.11+, SQLAlchemy
- **Hashing:** hashlib (SHA-256)
- **Versioning:** semver library for version comparison
- **Database:** PostgreSQL with JSON columns

### Project Structure
```
src/promptheus/
├── data/
│   ├── models.py                 ← Modify: add LessonVersion model
│   ├── async_repositories.py    ← Modify: add version methods
│   ├── lesson_loader.py          ← Modify: version on reload
│   └── version_manager.py        ← CREATE: VersionManager service
├── api/
│   └── admin.py                  ← Add: version endpoints
└── schemas/
    └── version_schemas.py        ← CREATE: Pydantic schemas

alembic/versions/
└── xxxx_add_lesson_versions.py   ← CREATE: migration

tests/
└── data/
    └── test_version_manager.py   ← CREATE: version tests
```

### Files to Modify

1. **`src/promptheus/data/models.py`** (MODIFY)
   - Purpose: Add LessonVersion model
   - New model: `LessonVersion`
   - Fields: id, lesson_id, version, content_hash, content snapshots, metadata
   - Relationships: Foreign key to Lesson
   - Constraints: Unique (lesson_id, version), one active version per lesson

2. **`src/promptheus/data/version_manager.py`** (CREATE)
   - Purpose: Service for version management
   - Class: `VersionManager`
   - Methods:
     - `hash_content(lesson_data) -> str`
     - `detect_change_type(old_hash, new_hash, old_content, new_content) -> str`
     - `create_version(lesson, content, change_type) -> LessonVersion`
     - `get_version(lesson_id, version) -> LessonVersion | None`
     - `get_all_versions(lesson_id) -> list[LessonVersion]`
     - `compare_versions(v1, v2) -> dict`
     - `rollback_to_version(lesson_id, version) -> None`

3. **`src/promptheus/data/async_repositories.py`** (MODIFY)
   - Purpose: Add version repository methods
   - Add: `AsyncLessonVersionRepository` class
   - Methods: CRUD for lesson versions
   - Integration: Call version manager on lesson updates

4. **`src/promptheus/data/lesson_loader.py`** (MODIFY)
   - Purpose: Create versions on hot reload
   - Modify: `reload_lesson()` to check content hash and create version
   - Add: Version manager dependency

5. **`src/promptheus/api/admin.py`** (MODIFY)
   - Purpose: Version management endpoints
   - Add endpoints:
     - `GET /admin/lessons/{lesson_id}/versions` - List versions
     - `GET /admin/lessons/{lesson_id}/versions/{version}` - Get specific version
     - `POST /admin/lessons/{lesson_id}/versions/{version}/activate` - Rollback
     - `GET /admin/lessons/{lesson_id}/versions/compare` - Compare versions

6. **`alembic/versions/xxxx_add_lesson_versions.py`** (CREATE)
   - Purpose: Database migration for version table
   - Create: `lesson_version` table
   - Migrate: Existing lessons to version "1.0.0"

---

## EXAMPLES AND DOCUMENTATION

### Code Examples

#### Example 1: Content hashing
```python
import hashlib
import json

def hash_content(lesson_data: dict) -> str:
    """Generate SHA-256 hash of lesson content.
    
    Args:
        lesson_data: Lesson content dictionary
        
    Returns:
        Hex string of content hash
    """
    # Extract content fields (exclude metadata like timestamps)
    content_fields = {
        "theory_content": lesson_data.get("theory_content"),
        "examples": lesson_data.get("examples"),
        "exercises": lesson_data.get("exercises"),
    }
    
    # Serialize to deterministic JSON (sorted keys)
    content_json = json.dumps(
        content_fields,
        sort_keys=True,
        ensure_ascii=False,
    )
    
    # Hash with SHA-256
    hash_obj = hashlib.sha256(content_json.encode("utf-8"))
    return hash_obj.hexdigest()
```

#### Example 2: LessonVersion model
```python
class LessonVersion(Base):
    """Lesson version history model."""
    
    __tablename__ = "lesson_version"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    lesson_id = Column(Integer, ForeignKey("lesson.id"), nullable=False, index=True)
    version = Column(String(20), nullable=False)
    content_hash = Column(String(64), nullable=False)  # SHA-256 hex
    
    # Content snapshot
    theory_content = Column(JSON, nullable=False)
    examples = Column(JSON, nullable=False)
    exercises = Column(JSON, nullable=False)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(UTC))
    created_by = Column(String(100), nullable=True)  # System or user
    change_description = Column(String(500), nullable=True)
    is_active = Column(Boolean, nullable=False, default=False)
    
    __table_args__ = (
        UniqueConstraint("lesson_id", "version", name="uq_lesson_version"),
        Index("ix_lesson_version_lesson_id_active", "lesson_id", "is_active"),
    )
    
    # Relationships
    lesson = relationship("Lesson", back_populates="versions")

# Add to Lesson model
class Lesson(Base):
    # ... existing fields
    
    # Relationships
    versions = relationship("LessonVersion", back_populates="lesson", cascade="all, delete-orphan")
```

#### Example 3: VersionManager service
```python
import semver
from loguru import logger

class VersionManager:
    """Service for lesson version management."""
    
    def __init__(self, version_repo):
        """Initialize with version repository."""
        self.version_repo = version_repo
    
    def hash_content(self, lesson_data: dict) -> str:
        """Generate content hash."""
        # Implementation from Example 1
        pass
    
    async def create_version(
        self,
        lesson_id: int,
        content: dict,
        change_type: str = "patch",
        created_by: str = "system",
        description: str | None = None,
    ) -> LessonVersion:
        """Create new version for lesson.
        
        Args:
            lesson_id: Lesson ID
            content: Lesson content dictionary
            change_type: Type of change (major/minor/patch)
            created_by: Author identifier
            description: Change description
            
        Returns:
            Created version object
        """
        logger.info("Creating version", lesson_id=lesson_id, change_type=change_type)
        
        # Get latest version
        latest = await self.version_repo.get_latest_version(lesson_id)
        
        # Calculate new version number
        if latest:
            current_ver = semver.VersionInfo.parse(latest.version)
            if change_type == "major":
                new_ver = current_ver.bump_major()
            elif change_type == "minor":
                new_ver = current_ver.bump_minor()
            else:  # patch
                new_ver = current_ver.bump_patch()
            version_str = str(new_ver)
        else:
            version_str = "1.0.0"
        
        # Calculate content hash
        content_hash = self.hash_content(content)
        
        # Create version record
        version = await self.version_repo.create(
            lesson_id=lesson_id,
            version=version_str,
            content_hash=content_hash,
            theory_content=content["theory_content"],
            examples=content["examples"],
            exercises=content["exercises"],
            created_by=created_by,
            change_description=description,
            is_active=True,  # New version is active
        )
        
        # Deactivate other versions
        await self.version_repo.deactivate_other_versions(lesson_id, version.id)
        
        logger.success("Version created", lesson_id=lesson_id, version=version_str)
        return version
    
    async def rollback_to_version(
        self, lesson_id: int, version_str: str
    ) -> LessonVersion:
        """Rollback lesson to specific version.
        
        Args:
            lesson_id: Lesson ID
            version_str: Target version string
            
        Returns:
            Activated version
        """
        logger.info("Rolling back", lesson_id=lesson_id, version=version_str)
        
        # Find target version
        target = await self.version_repo.get_version(lesson_id, version_str)
        if not target:
            raise ValueError(f"Version {version_str} not found")
        
        # Activate target version
        await self.version_repo.activate_version(lesson_id, target.id)
        
        # Update main lesson table with target content
        await self.lesson_repo.update_content(
            lesson_id,
            theory_content=target.theory_content,
            examples=target.examples,
            exercises=target.exercises,
        )
        
        logger.success("Rollback complete", lesson_id=lesson_id, version=version_str)
        return target
    
    async def compare_versions(
        self, lesson_id: int, v1_str: str, v2_str: str
    ) -> dict:
        """Compare two versions of same lesson.
        
        Args:
            lesson_id: Lesson ID
            v1_str: First version string
            v2_str: Second version string
            
        Returns:
            Diff dictionary with changes
        """
        v1 = await self.version_repo.get_version(lesson_id, v1_str)
        v2 = await self.version_repo.get_version(lesson_id, v2_str)
        
        if not v1 or not v2:
            raise ValueError("One or both versions not found")
        
        # Simple diff (can be enhanced with difflib)
        diff = {
            "v1": v1_str,
            "v2": v2_str,
            "content_hash_changed": v1.content_hash != v2.content_hash,
            "theory_changed": v1.theory_content != v2.theory_content,
            "examples_changed": v1.examples != v2.examples,
            "exercises_changed": v1.exercises != v2.exercises,
        }
        
        return diff
```

#### Example 4: Integration with hot reload
```python
# In lesson_loader.py
async def reload_lesson(
    self, filepath: Path, change_type: str, skill_level_str: str
) -> None:
    """Hot reload with versioning."""
    # ... existing loading logic
    
    # Check if content actually changed
    old_lesson = await self.lesson_repo.find_by_slug(skill_level, slug)
    if old_lesson:
        old_hash = self.version_manager.hash_content({
            "theory_content": old_lesson.theory_content,
            "examples": old_lesson.examples,
            "exercises": old_lesson.exercises,
        })
        new_hash = self.version_manager.hash_content({
            "theory_content": lesson_schema.theory_content,
            "examples": lesson_schema.examples,
            "exercises": lesson_schema.exercises,
        })
        
        if old_hash == new_hash:
            logger.debug("Content unchanged, skipping versioning", slug=slug)
            return
        
        # Content changed - create new version
        change_type_detected = "patch"  # Can be smarter based on content diff
        await self.version_manager.create_version(
            lesson_id=old_lesson.id,
            content={
                "theory_content": lesson_schema.theory_content,
                "examples": lesson_schema.examples,
                "exercises": lesson_schema.exercises,
            },
            change_type=change_type_detected,
            created_by="hot-reload",
            description=f"Auto-reload from {filepath.name}",
        )
    
    # ... continue with upsert logic
```

### Documentation
- [Semantic Versioning](https://semver.org/)
- [SHA-256 Hash](https://en.wikipedia.org/wiki/SHA-2)
- [SQLAlchemy Relationships](https://docs.sqlalchemy.org/en/20/orm/basic_relationships.html)

### Existing Patterns
- **Foreign Keys:** Follow pattern from UserProgress
- **Timestamps:** Use UTC with timezone
- **JSON Storage:** Follow pattern from Lesson model
- **Repositories:** Async repository pattern

### Known Pitfalls
⚠️ **Important:**
- **JSON serialization order:** Use `sort_keys=True` for deterministic hashing
- **Active version flag:** Only one version can be active per lesson (enforce with logic)
- **Hash collisions:** Extremely unlikely with SHA-256, but log hash for debugging
- **Timezone handling:** Always use UTC for `created_at`
- **Version string format:** Validate semver format before storing

---

## ACCEPTANCE CRITERIA

### Scenario Criteria (Given-When-Then)

#### Scenario 1: Version created on content change
```gherkin
Given lesson content is modified in JSON file
And content hash is different from previous version
When hot reload triggers
Then new version is created with incremented version number
And new version is marked as active
And previous version is marked as inactive
```

#### Scenario 2: No version created if content unchanged
```gherkin
Given lesson JSON file is modified (e.g., formatting change)
And content hash is identical to previous version
When hot reload triggers
Then no new version is created
And existing active version remains unchanged
```

#### Scenario 3: List all versions for lesson
```gherkin
Given lesson has multiple versions (1.0.0, 1.1.0, 2.0.0)
When requesting versions via API
Then all versions are returned in chronological order
And each version includes metadata (created_at, created_by)
And active version is indicated
```

#### Scenario 4: Rollback to previous version
```gherkin
Given lesson is at version 2.0.0
And version 1.1.0 exists in history
When rollback to version 1.1.0 is triggered
Then version 1.1.0 is marked as active
And version 2.0.0 is marked as inactive
And main lesson content is updated with 1.1.0 content
And cache is updated with rolled-back content
```

#### Scenario 5: Compare two versions
```gherkin
Given lesson has versions 1.0.0 and 2.0.0
When comparing versions via API
Then diff shows which fields changed
And content hashes are compared
And specific changes are highlighted
```

### Rules and Constraints
- [ ] Only one version can be active per lesson at a time
- [ ] Version strings follow semver format (X.Y.Z)
- [ ] Content hash is SHA-256 (64 hex characters)
- [ ] Version records are immutable (never updated, only created)
- [ ] Rollback is atomic (content + active flag + cache)
- [ ] Version metadata includes created_at and created_by

### Testing
- [ ] All unit tests pass successfully
- [ ] Version creation tested with content changes
- [ ] Rollback tested end-to-end
- [ ] Version comparison tested
- [ ] Test coverage >= 85% for version manager

### Code Review
- [ ] Code conforms to project style guide (Ruff passes)
- [ ] Type hints on all functions (mypy passes)
- [ ] Docstrings on all public methods
- [ ] Transaction safety for rollback
- [ ] Hash algorithm documented

### Performance
- [ ] Version creation <50ms
- [ ] Version lookup <10ms
- [ ] Storage overhead acceptable (~5MB per 100 versions)

---

## IMPLEMENTATION PLAN

### Execution Stages

#### Stage 1: Create LessonVersion model
**Description:** Define database model for version storage
**Tasks:**
- [ ] Open `src/promptheus/data/models.py`
- [ ] Define `LessonVersion` class
- [ ] Add all fields (id, lesson_id, version, content_hash, content snapshots, metadata)
- [ ] Add foreign key relationship to Lesson
- [ ] Add unique constraint on (lesson_id, version)
- [ ] Add index on (lesson_id, is_active)
- [ ] Add `versions` relationship to Lesson model

**Validation:**
- Model structure is correct
- Relationships defined properly

#### Stage 2: Create Alembic migration
**Description:** Database migration for version table
**Tasks:**
- [ ] Generate migration: `uv run alembic revision -m "add lesson version table"`
- [ ] Implement upgrade():
  - [ ] Create lesson_version table
  - [ ] Create indexes and constraints
  - [ ] Migrate existing lessons to version "1.0.0"
- [ ] Implement downgrade()
- [ ] Test migration with test database

**Validation:**
- Migration runs successfully
- Existing lessons have initial version

#### Stage 3: Implement VersionManager
**Description:** Core versioning logic
**Tasks:**
- [ ] Create `src/promptheus/data/version_manager.py`
- [ ] Implement `hash_content()` method
- [ ] Implement `create_version()` method
- [ ] Implement `get_version()` method
- [ ] Implement `get_all_versions()` method
- [ ] Implement `compare_versions()` method
- [ ] Implement `rollback_to_version()` method
- [ ] Add semver validation
- [ ] Write unit tests

**Validation:**
- All methods work correctly
- Semver logic correct

#### Stage 4: Create version repository
**Description:** Database operations for versions
**Tasks:**
- [ ] Open `src/promptheus/data/async_repositories.py`
- [ ] Create `AsyncLessonVersionRepository` class
- [ ] Implement CRUD methods:
  - [ ] `create()` - Create version
  - [ ] `get_version(lesson_id, version)` - Get specific version
  - [ ] `get_latest_version(lesson_id)` - Get latest version
  - [ ] `get_all_versions(lesson_id)` - Get all versions
  - [ ] `activate_version(lesson_id, version_id)` - Set active
  - [ ] `deactivate_other_versions(lesson_id, version_id)` - Deactivate others
- [ ] Write tests

**Validation:**
- All repository methods work
- Active flag logic correct

#### Stage 5: Integrate with hot reload
**Description:** Create versions on content changes
**Tasks:**
- [ ] Open `src/promptheus/data/lesson_loader.py`
- [ ] Add `version_manager` dependency
- [ ] Modify `reload_lesson()`:
  - [ ] Check if content hash changed
  - [ ] Create new version if changed
  - [ ] Skip versioning if unchanged
- [ ] Update tests

**Validation:**
- Versions created on content changes
- No versions for unchanged content

#### Stage 6: Add version API endpoints
**Description:** Admin endpoints for version management
**Tasks:**
- [ ] Open or create `src/promptheus/api/admin.py`
- [ ] Add `GET /admin/lessons/{lesson_id}/versions` endpoint
- [ ] Add `GET /admin/lessons/{lesson_id}/versions/{version}` endpoint
- [ ] Add `POST /admin/lessons/{lesson_id}/versions/{version}/activate` endpoint
- [ ] Add `GET /admin/lessons/{lesson_id}/versions/compare` endpoint
- [ ] Add authentication (admin only)
- [ ] Write API tests

**Validation:**
- All endpoints work correctly
- Authentication enforced

#### Stage 7: Add version to Pydantic schema
**Description:** Include version in lesson schema
**Tasks:**
- [ ] Open `src/promptheus/data/schemas.py`
- [ ] Add `version: str` field to LessonContentSchema
- [ ] Add validator for semver format
- [ ] Default to "1.0.0" if not provided
- [ ] Update tests

**Validation:**
- Schema validates version strings
- Default works correctly

#### Stage 8: Integrate with cache
**Description:** Update cache on rollback
**Tasks:**
- [ ] Modify `version_manager.rollback_to_version()`
- [ ] Add cache update after rollback
- [ ] Ensure atomic operation
- [ ] Test rollback with cached content

**Validation:**
- Cache updated on rollback
- Users see rolled-back content immediately

#### Stage 9: Comprehensive testing
**Description:** Integration and edge case tests
**Tasks:**
- [ ] Test version creation flow
- [ ] Test rollback flow
- [ ] Test version comparison
- [ ] Test with multiple concurrent changes
- [ ] Test migration with existing data
- [ ] Run full test suite

**Validation:**
- All tests pass
- Coverage >= 85%

### Action Order
1. Create model (Stage 1)
2. Create migration (Stage 2)
3. Implement VersionManager (Stage 3)
4. Create repository (Stage 4)
5. Integrate with hot reload (Stage 5)
6. Add API endpoints (Stage 6)
7. Update schema (Stage 7)
8. Integrate with cache (Stage 8)
9. Comprehensive testing (Stage 9)

### Dependencies
- **Blocks on:** Task PRMT-202 (lesson loader), Task PRMT-204 (cache for rollback)
- **Optional:** Task PRMT-203 (slug makes version lookup easier)
- **Requires:** semver library (add to dependencies)

---

## TESTING AND VALIDATION

### Unit Tests
```python
import pytest
from promptheus.data.version_manager import VersionManager

def test_hash_content_deterministic():
    # Given
    content = {
        "theory_content": {"sections": [{"content": "Test"}]},
        "examples": {"comparisons": []},
        "exercises": {"scenarios": []},
    }
    vm = VersionManager(mock_repo)
    
    # When
    hash1 = vm.hash_content(content)
    hash2 = vm.hash_content(content)
    
    # Then
    assert hash1 == hash2
    assert len(hash1) == 64  # SHA-256 hex length

def test_hash_content_changes_with_content():
    # Given
    content1 = {"theory_content": {"sections": [{"content": "A"}]}}
    content2 = {"theory_content": {"sections": [{"content": "B"}]}}
    vm = VersionManager(mock_repo)
    
    # When
    hash1 = vm.hash_content(content1)
    hash2 = vm.hash_content(content2)
    
    # Then
    assert hash1 != hash2

@pytest.mark.asyncio
async def test_create_version_increments_patch():
    # Given
    vm = VersionManager(mock_repo)
    mock_repo.get_latest_version.return_value = MockVersion(version="1.0.0")
    
    # When
    version = await vm.create_version(
        lesson_id=1,
        content={"theory_content": {}, "examples": {}, "exercises": {}},
        change_type="patch",
    )
    
    # Then
    assert version.version == "1.0.1"

@pytest.mark.asyncio
async def test_rollback_activates_target_version():
    # Given
    vm = VersionManager(mock_repo, lesson_repo, cache)
    target_version = MockVersion(id=2, version="1.0.0", content={})
    mock_repo.get_version.return_value = target_version
    
    # When
    await vm.rollback_to_version(lesson_id=1, version_str="1.0.0")
    
    # Then
    mock_repo.activate_version.assert_called_once_with(1, 2)
    lesson_repo.update_content.assert_called_once()
```

### Commands to Run
```bash
# Add semver dependency
uv add semver

# Run migration
uv run alembic upgrade head

# Run version tests
uv run pytest tests/data/test_version_manager.py -v

# Run API tests
uv run pytest tests/api/test_admin.py::test_version_endpoints -v

# Check coverage
uv run pytest --cov=src/promptheus --cov-report=term

# Run full test suite
uv run pytest
```

### Manual Testing Scenarios
1. **Scenario 1: Version creation on content update**
   - Steps:
     1. Start application
     2. Modify lesson JSON file (change theory content)
     3. Wait for hot reload (1-2 seconds)
     4. Query versions: `GET /admin/lessons/1/versions`
     5. Verify new version created
   - Expected result: New version with incremented number

2. **Scenario 2: Rollback to previous version**
   - Steps:
     1. Note current version (e.g., 2.0.0)
     2. Call rollback: `POST /admin/lessons/1/versions/1.0.0/activate`
     3. Request lesson content
     4. Verify content matches version 1.0.0
   - Expected result: Content rolled back, users see old version

---

## ADDITIONAL CONSIDERATIONS

### Risks
- **Risk 1:** Version table grows large over time
  - **Mitigation:** Implement version retention policy (keep last N versions)
  - **Mitigation:** Archive old versions to separate storage
  
- **Risk 2:** Rollback during active user session causes confusion
  - **Mitigation:** Log rollback events prominently
  - **Mitigation:** Consider staging/production separation for content
  
- **Risk 3:** Content hash collisions (extremely unlikely)
  - **Mitigation:** Log hash for debugging
  - **Mitigation:** SHA-256 collision probability is negligible

### Assumptions
- Lesson content changes are infrequent (not every second)
- Version history doesn't need to be kept forever
- Rollback is manual admin operation (not automatic)
- Content validation happens before versioning

### Limitations
- No automatic version type detection (always defaults to patch)
- No diff visualization (only field-level comparison)
- No branch/merge concept (linear version history)
- No per-user version rollout (future A/B testing feature)

### Future Improvements
- Automatic version type detection (analyze content diff)
- Detailed diff with line-by-line changes (difflib integration)
- Version retention policy (auto-archive old versions)
- A/B testing support (different versions for different users)
- Version approval workflow (review before activate)

### Questions and Unresolved Issues
- [ ] How long should versions be kept?
  - **Decision:** Keep all versions for now, add retention policy in future
- [ ] Should rollback require approval/confirmation?
  - **Decision:** Yes, require admin authentication
- [ ] What about version conflicts in multi-instance deployments?
  - **Decision:** Last-write-wins, acceptable for MVP

---

## COMPLETION CHECKLIST

### Development
- [ ] LessonVersion model created
- [ ] VersionManager service implemented
- [ ] Version repository created
- [ ] Integrated with hot reload
- [ ] API endpoints for version management
- [ ] Version added to Pydantic schema
- [ ] Cache updated on rollback
- [ ] semver added to dependencies

### Testing
- [ ] Unit tests for version manager
- [ ] Repository tests for versions
- [ ] Integration test for rollback
- [ ] API endpoint tests
- [ ] All tests pass
- [ ] Code coverage >= 85%

### Documentation
- [ ] Docstrings on all methods
- [ ] API endpoints documented
- [ ] Version schema explained
- [ ] Rollback process documented

### Code Quality
- [ ] Ruff reports no errors
- [ ] Mypy reports no errors
- [ ] Version string validation
- [ ] Transaction safety for rollback

### Performance
- [ ] Version creation <50ms
- [ ] Version lookup <10ms
- [ ] Storage overhead acceptable

### Finalization
- [ ] Changes committed: `feat(data): add lesson content versioning system`
- [ ] Migration tested with existing data
- [ ] Rollback tested in development
- [ ] Task marked as "Ready for Review"

---

**Notes:**
- This feature provides foundation for content experimentation and safety
- Version retention policy should be added as follow-up task
- Consider integration with CI/CD for automated content deployment
- A/B testing capability can be built on top of versioning system
