# Technical Task: Remove Order Index Dependency

## METADATA

**Task ID:** PRMT-203  
**Name:** Replace order_index with slug-based lesson identification  
**Created:** 2025-11-09  
**Priority:** Medium  
**Complexity Estimate:** 7/10  
**Estimated Time:** 6-8 hours

---

## BUSINESS CONTEXT

### Problem Description
Currently, lessons use `order_index` (integer) combined with `skill_level` to determine lesson sequence. This creates tight coupling with file naming (files must be numbered like `01_`, `02_`), makes reordering difficult (requires renumber all lessons), and creates fragility when adding lessons between existing ones. The system needs a more flexible identification scheme that decouples lesson identity from ordering.

### Business Goals
- Enable flexible lesson ordering without file renaming
- Allow inserting lessons between existing ones without disruption
- Support multiple lesson paths/tracks in the future
- Simplify content creation (no number management needed)
- Make lesson identification semantic and readable

### Target Audience
- **Primary:** Content creators managing lesson files
- **Secondary:** Backend developers maintaining lesson logic
- **Tertiary:** End users (transparent change, better UX for lesson navigation)

### Business Value
- Reduce content maintenance overhead (no renumbering needed)
- Enable richer learning path features (branching, prerequisites)
- Improve content discoverability with semantic slugs
- Reduce errors from manual number management

---

## TECHNICAL SPECIFICATION

### Functional Requirements

#### Main Functionality
As a system, I want to identify and order lessons using semantic slugs and directory position, so that lesson ordering is flexible and maintainable.

#### Detailed Requirements

1. **Slug Generation**
   - Description: Generate URL-safe slug from lesson title
   - Behavior:
     - Convert title to lowercase
     - Replace spaces with hyphens
     - Remove special characters (keep alphanumeric and hyphens)
     - Ensure uniqueness within skill level
     - Max length: 100 characters
   - Example: "Introduction to Prompt Engineering" → "introduction-to-prompt-engineering"

2. **File-Based Ordering**
   - Description: Determine lesson order from alphabetical file sort
   - Behavior:
     - Order lessons by filename (alphabetical) within skill level directory
     - Support prefixes for explicit ordering (e.g., `beginner-`, `advanced-`)
     - No number required in filename (but allowed for transition)
   - Example ordering:
     ```
     beginner/
       defining-ai-roles.json
       introduction-to-prompt-engineering.json
       providing-context.json
     ```
     Order: introduction → defining → providing (alphabetical)

3. **Database Schema Changes**
   - Description: Replace order_index with slug and position
   - Fields to add:
     - `slug`: String, unique per skill_level (indexed)
     - `position`: Integer, nullable (for explicit ordering if needed)
   - Fields to remove:
     - `order_index` (removed in same migration)
   - Migration strategy: Single migration (add new fields, migrate data, remove old field)

4. **Repository Updates**
   - Description: Update queries to use slug instead of order_index
   - Changes:
     - `find_by_slug(skill_level, slug)` - new method
     - `find_by_skill_level()` - order by filename/position instead of order_index
     - `find_next_lesson()` - use position or filename order
   - Constraints: Maintain backward compatibility during migration

5. **Lesson Navigation Updates**
   - Description: Update learning flow to use slugs
   - Changes:
     - User progress tracks slug instead of order_index
     - Next lesson logic uses position or alphabetical order
     - Lesson URLs use slug (more readable)
   - Constraints: No breaking changes to existing user progress

### Non-Functional Requirements

#### Performance
- Slug lookup should be <10ms (indexed query)
- Position-based ordering same performance as order_index
- Migration should complete in <1 minute for 1000 lessons

#### Reliability
- Slug uniqueness enforced by database constraint
- Slug generation is deterministic (same title → same slug)
- Migration is reversible via downgrade (recreates order_index from backup data)

#### Compatibility
- Migration preserves data integrity through proper sequencing
- Old order_index removed in same migration after data transfer
- API uses only slug and position after migration

---

## TECHNICAL CONTEXT

### System Architecture
```
┌──────────────────┐
│  Lesson Files    │
│  (Alphabetical)  │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐      ┌─────────────────┐
│ Slug Generator   │─────▶│  Database       │
│  - title_to_slug │      │  - slug (unique)│
│  - ensure_unique │      │  - position     │
└──────────────────┘      └─────────────────┘
         │
         ▼
┌──────────────────┐      ┌─────────────────┐
│ Repository Layer │─────▶│  Navigation     │
│  - find_by_slug  │      │  - next_lesson  │
│  - order_by_pos  │      │  - prev_lesson  │
└──────────────────┘      └─────────────────┘
```

### Technology Stack
- **Backend:** Python 3.11+, SQLAlchemy, Alembic
- **Database:** PostgreSQL with unique constraints
- **Migration:** Alembic for schema changes

### Project Structure
```
src/promptheus/
├── data/
│   ├── models.py                ← Modify: add slug, position
│   ├── async_repositories.py   ← Modify: slug-based queries
│   └── lesson_loader.py         ← Modify: generate slugs
└── core/
    ├── learning_flow_orchestrator.py  ← Modify: use slugs
    └── progress_tracker.py            ← Modify: track by slug

alembic/versions/
└── xxxx_add_lesson_slug.py      ← CREATE: migration

tests/
├── data/
│   └── test_lesson_slug.py      ← CREATE: slug generation tests
└── core/
    └── test_slug_navigation.py  ← Modify: test slug-based nav
```

### Files to Modify

1. **`src/promptheus/data/models.py`** (MODIFY)
   - Purpose: Add slug and position fields, remove order_index from Lesson model
   - Changes:
     - Add `slug = Column(String(100), nullable=False)`
     - Add `position = Column(Integer, nullable=True)`
     - Add `UniqueConstraint("skill_level", "slug")`
     - Add `Index("ix_lesson_skill_level_slug", "skill_level", "slug")`
     - Remove `order_index` column and its index completely

2. **`src/promptheus/data/async_repositories.py`** (MODIFY)
   - Purpose: Add slug-based query methods
   - Add methods:
     - `async def find_by_slug(skill_level, slug) -> Lesson | None`
     - Update `find_by_skill_level()` to order by position or slug
     - Update `find_next_lesson()` to use position
   - Deprecate: Methods using order_index

3. **`src/promptheus/data/lesson_loader.py`** (MODIFY)
   - Purpose: Generate slugs during lesson loading
   - Add method: `generate_slug(title: str) -> str`
   - Add validation: Ensure slug uniqueness within skill level
   - Update: Include slug in lesson data for upsert

4. **`alembic/versions/xxxx_add_lesson_slug.py`** (CREATE)
   - Purpose: Database migration to replace order_index with slug and position
   - Phase 1: Add new columns (nullable)
   - Phase 2: Populate slugs from titles and position from order_index
   - Phase 3: Make slug non-nullable, add constraints
   - Phase 4: Drop order_index column and its index

5. **`src/promptheus/core/learning_flow_orchestrator.py`** (MODIFY)
   - Purpose: Update navigation to use slugs
   - Changes:
     - Accept slug in lesson lookup
     - Return slug in lesson data
     - Use position-based next lesson logic

6. **`tests/data/test_lesson_slug.py`** (CREATE)
   - Purpose: Test slug generation and uniqueness
   - Test cases: Valid slugs, uniqueness, special characters, long titles

---

## EXAMPLES AND DOCUMENTATION

### Code Examples

#### Example 1: Slug generation
```python
import re

def generate_slug(title: str, max_length: int = 100) -> str:
    """Generate URL-safe slug from title.
    
    Args:
        title: Lesson title
        max_length: Maximum slug length
        
    Returns:
        URL-safe slug (lowercase, hyphens, alphanumeric)
        
    Example:
        >>> generate_slug("Introduction to Prompt Engineering")
        'introduction-to-prompt-engineering'
    """
    # Convert to lowercase
    slug = title.lower()
    
    # Replace spaces and underscores with hyphens
    slug = slug.replace(" ", "-").replace("_", "-")
    
    # Remove special characters (keep alphanumeric and hyphens)
    slug = re.sub(r"[^a-z0-9-]", "", slug)
    
    # Remove consecutive hyphens
    slug = re.sub(r"-+", "-", slug)
    
    # Trim hyphens from start/end
    slug = slug.strip("-")
    
    # Truncate to max length
    if len(slug) > max_length:
        slug = slug[:max_length].rstrip("-")
    
    return slug
```

#### Example 2: Database model with slug
```python
class Lesson(Base):
    """Lesson model with slug-based identification."""
    
    __tablename__ = "lesson"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False, unique=True)
    slug = Column(String(100), nullable=False)
    skill_level = Column(Enum(SkillLevel), nullable=False, index=True)
    position = Column(Integer, nullable=True)  # Explicit ordering
    
    __table_args__ = (
        UniqueConstraint("skill_level", "slug", name="uq_lesson_skill_level_slug"),
        Index("ix_lesson_skill_level_slug", "skill_level", "slug"),
    )
```

#### Example 3: Alembic migration (Phase 1)
```python
"""Add slug and position to lesson table

Revision ID: abc123def456
Revises: previous_revision
Create Date: 2025-11-09
"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    # Phase 1: Add columns (nullable for now)
    op.add_column('lesson', sa.Column('slug', sa.String(100), nullable=True))
    op.add_column('lesson', sa.Column('position', sa.Integer(), nullable=True))
    
    # Phase 2: Populate slugs from titles and position from order_index
    from promptheus.data.lesson_loader import generate_slug
    
    connection = op.get_bind()
    lessons = connection.execute(
        sa.text("SELECT id, title, order_index FROM lesson")
    ).fetchall()
    
    for lesson_id, title, order_index in lessons:
        slug = generate_slug(title)
        # Convert order_index to position (multiply by 10 for flexibility)
        position = order_index * 10 if order_index is not None else None
        connection.execute(
            sa.text("UPDATE lesson SET slug = :slug, position = :position WHERE id = :id"),
            {"slug": slug, "position": position, "id": lesson_id}
        )
    
    # Phase 3: Make slug non-nullable and add constraints
    op.alter_column('lesson', 'slug', nullable=False)
    op.create_unique_constraint(
        'uq_lesson_skill_level_slug', 
        'lesson', 
        ['skill_level', 'slug']
    )
    op.create_index(
        'ix_lesson_skill_level_slug', 
        'lesson', 
        ['skill_level', 'slug']
    )
    
    # Phase 4: Remove old order_index column and index
    op.drop_index('ix_lesson_skill_level_order_index', 'lesson')
    op.drop_constraint('uq_lesson_skill_level_order_index', 'lesson', type_='unique')
    op.drop_column('lesson', 'order_index')

def downgrade():
    # Reverse changes - recreate order_index from position
    op.add_column('lesson', sa.Column('order_index', sa.Integer(), nullable=True))
    
    connection = op.get_bind()
    lessons = connection.execute(
        sa.text("SELECT id, position FROM lesson")
    ).fetchall()
    
    for lesson_id, position in lessons:
        # Convert position back to order_index
        order_index = position // 10 if position is not None else None
        connection.execute(
            sa.text("UPDATE lesson SET order_index = :order_index WHERE id = :id"),
            {"order_index": order_index, "id": lesson_id}
        )
    
    op.alter_column('lesson', 'order_index', nullable=False)
    op.create_unique_constraint(
        'uq_lesson_skill_level_order_index',
        'lesson',
        ['skill_level', 'order_index']
    )
    op.create_index('ix_lesson_skill_level_order_index', 'lesson', ['skill_level', 'order_index'])
    
    # Drop new columns
    op.drop_index('ix_lesson_skill_level_slug', 'lesson')
    op.drop_constraint('uq_lesson_skill_level_slug', 'lesson', type_='unique')
    op.drop_column('lesson', 'position')
    op.drop_column('lesson', 'slug')
```

#### Example 4: Repository with slug lookup
```python
class AsyncLessonRepository:
    """Async repository with slug-based queries."""
    
    async def find_by_slug(
        self, skill_level: SkillLevel, slug: str
    ) -> Lesson | None:
        """Find lesson by slug within skill level.
        
        Args:
            skill_level: Skill level to search in
            slug: Lesson slug
            
        Returns:
            Lesson if found, None otherwise
        """
        logger.debug("Finding lesson by slug", skill_level=skill_level, slug=slug)
        async with self.session_maker() as session:
            stmt = select(Lesson).where(
                Lesson.skill_level == skill_level,
                Lesson.slug == slug
            )
            result = await session.execute(stmt)
            lesson = result.scalar_one_or_none()
            
            if lesson:
                logger.debug("Lesson found", lesson_id=lesson.id, slug=slug)
            else:
                logger.debug("Lesson not found", slug=slug)
            
            return lesson
    
    async def find_by_skill_level(
        self, skill_level: SkillLevel
    ) -> list[Lesson]:
        """Find lessons ordered by position or slug."""
        logger.debug("Finding lessons by skill level", skill_level=skill_level)
        async with self.session_maker() as session:
            # Order by position if set, fallback to slug alphabetically
            stmt = (
                select(Lesson)
                .where(Lesson.skill_level == skill_level)
                .order_by(
                    Lesson.position.asc().nulls_last(),
                    Lesson.slug.asc()
                )
            )
            result = await session.execute(stmt)
            lessons = result.scalars().all()
            logger.debug("Lessons found", count=len(lessons))
            return list(lessons)
```

### Documentation
- [SQLAlchemy UniqueConstraint](https://docs.sqlalchemy.org/en/20/core/constraints.html#unique-constraint)
- [Alembic Data Migrations](https://alembic.sqlalchemy.org/en/latest/cookbook.html#running-data-migrations)
- [URL Slug Best Practices](https://www.semrush.com/blog/url-slug/)

### Existing Patterns
- **Enum Types:** Reuse SkillLevel enum
- **Unique Constraints:** Follow pattern from existing constraints
- **Migration:** Use Alembic with data migration support
- **Repository:** Follow async repository pattern

### Known Pitfalls
⚠️ **Important:**
- **Slug collisions:** Ensure uniqueness check before insert
- **Unicode handling:** Slugify should handle non-ASCII characters (normalize first)
- **Migration timing:** Run during maintenance window (brief table lock)
- **Position gaps:** Allow gaps in position values (10, 20, 30) for easy insertion
- **Existing user progress:** Must migrate references from order_index to slug

---

## ACCEPTANCE CRITERIA

### Scenario Criteria (Given-When-Then)

#### Scenario 1: Slug generated from title
```gherkin
Given lesson title is "Introduction to Prompt Engineering"
When slug is generated
Then slug equals "introduction-to-prompt-engineering"
And slug contains only lowercase alphanumeric and hyphens
```

#### Scenario 2: Slug uniqueness enforced
```gherkin
Given database has lesson with slug "introduction-to-prompting" for beginner
When attempting to insert another beginner lesson with same slug
Then database constraint violation is raised
And error message indicates duplicate slug
```

#### Scenario 3: Lessons ordered by position
```gherkin
Given lessons have positions: [10, 30, 20]
When fetching lessons by skill level
Then lessons are returned in order: [10, 20, 30]
```

#### Scenario 4: Lessons without position fall back to slug order
```gherkin
Given lessons have slugs ["c-lesson", "a-lesson", "b-lesson"]
And no position values set
When fetching lessons by skill level
Then lessons are returned alphabetically: ["a-lesson", "b-lesson", "c-lesson"]
```

#### Scenario 5: Migration preserves existing data
```gherkin
Given database has lessons with order_index values
When migration runs
Then each lesson has slug generated from title
And position is calculated from order_index (order_index * 10)
And slugs are unique within skill level
And no data is lost
And order_index is removed after data transfer
```

#### Scenario 6: Next lesson navigation uses position
```gherkin
Given current lesson has position 20
And next lesson has position 30
When requesting next lesson
Then lesson with position 30 is returned
```

### Rules and Constraints
- [ ] Slug must be unique per skill_level (database constraint)
- [ ] Slug max length is 100 characters
- [ ] Position allows null values (optional explicit ordering)
- [ ] Slug generation is deterministic (same input → same output)
- [ ] Migration transfers order_index to position before removal
- [ ] Existing user progress migrated to use slugs
- [ ] order_index completely removed after migration

### Testing
- [ ] All unit tests pass successfully
- [ ] Migration tested with real database
- [ ] Test coverage >= 85% for slug generation
- [ ] Edge cases tested (unicode, special chars, collisions)

### Code Review
- [ ] Code conforms to project style guide (Ruff passes)
- [ ] Type hints on all functions (mypy passes)
- [ ] Migration includes both upgrade and downgrade
- [ ] Docstrings on all new methods

### Performance
- [ ] Slug lookup <10ms (indexed)
- [ ] Migration completes <1 minute for 1000 lessons
- [ ] No performance degradation in lesson queries

---

## IMPLEMENTATION PLAN

### Execution Stages

#### Stage 1: Implement slug generation utility
**Description:** Create slug generation function
**Tasks:**
- [ ] Create `generate_slug()` function in `lesson_loader.py`
- [ ] Handle lowercase conversion
- [ ] Replace spaces with hyphens
- [ ] Remove special characters
- [ ] Handle consecutive hyphens
- [ ] Truncate to max length
- [ ] Write unit tests for various inputs

**Validation:**
- Generates valid slugs for common titles
- Handles edge cases (unicode, special chars)

#### Stage 2: Update database model
**Description:** Add slug and position fields, remove order_index
**Tasks:**
- [ ] Open `src/promptheus/data/models.py`
- [ ] Add `slug = Column(String(100), nullable=False)`
- [ ] Add `position = Column(Integer, nullable=True)`
- [ ] Add `UniqueConstraint("skill_level", "slug")`
- [ ] Add `Index("ix_lesson_skill_level_slug")`
- [ ] Remove `order_index` column definition
- [ ] Remove `UniqueConstraint` and `Index` for order_index
- [ ] Update model docstring

**Validation:**
- Model definition is correct
- Type hints pass mypy
- No references to order_index remain

#### Stage 3: Create Alembic migration
**Description:** Database schema migration with data migration and order_index removal
**Tasks:**
- [ ] Generate migration: `uv run alembic revision -m "replace order_index with slug and position"`
- [ ] Implement upgrade():
  - [ ] Add slug column (nullable)
  - [ ] Add position column (nullable)
  - [ ] Run data migration loop (populate slugs from titles, position from order_index)
  - [ ] Make slug non-nullable
  - [ ] Add unique constraint and index for slug
  - [ ] Drop order_index index and constraint
  - [ ] Drop order_index column
- [ ] Implement downgrade():
  - [ ] Recreate order_index column
  - [ ] Populate order_index from position
  - [ ] Add constraints and index for order_index
  - [ ] Drop slug columns and constraints
- [ ] Test migration with test database

**Validation:**
- Migration runs successfully
- Downgrade works correctly
- Data preserved and converted properly
- order_index fully removed

#### Stage 4: Update lesson loader
**Description:** Generate slugs during loading
**Tasks:**
- [ ] Open `src/promptheus/data/lesson_loader.py`
- [ ] Add slug generation in `validate_lesson()`
- [ ] Add slug uniqueness check
- [ ] Include slug in lesson data dict
- [ ] Calculate position from file order (index + 1) * 10
- [ ] Update tests

**Validation:**
- Slugs generated correctly
- Uniqueness enforced

#### Stage 5: Add slug-based repository methods
**Description:** New query methods using slug
**Tasks:**
- [ ] Open `src/promptheus/data/async_repositories.py`
- [ ] Add `find_by_slug(skill_level, slug)` method
- [ ] Update `find_by_skill_level()` to order by position, then slug
- [ ] Update `find_next_lesson()` to use position comparison
- [ ] Add logging for new methods
- [ ] Write tests

**Validation:**
- All repository methods work with slugs
- Ordering is correct

#### Stage 6: Update learning flow orchestrator
**Description:** Use slugs in navigation logic
**Tasks:**
- [ ] Open `src/promptheus/core/learning_flow_orchestrator.py`
- [ ] Update `get_next_lesson()` to use position-based logic
- [ ] Return slug in lesson data dicts
- [ ] Update progress tracking to use slugs (if applicable)
- [ ] Update tests

**Validation:**
- Navigation works with slug-based system
- No breaking changes to user experience

#### Stage 7: Update Pydantic schema
**Description:** Add slug to lesson schema
**Tasks:**
- [ ] Open `src/promptheus/data/schemas.py`
- [ ] Add `slug: str = Field(max_length=100)` to LessonContentSchema
- [ ] Add optional `position: int | None = None`
- [ ] Update validator to generate slug if not provided
- [ ] Update tests

**Validation:**
- Schema validates slugs correctly
- Auto-generation works

#### Stage 8: Run migration and validate
**Description:** Execute migration in development
**Tasks:**
- [ ] Backup development database
- [ ] Run migration: `uv run alembic upgrade head`
- [ ] Verify slugs populated correctly
- [ ] Query lessons and check ordering
- [ ] Test application startup with new schema
- [ ] Verify next lesson navigation works

**Validation:**
- Migration successful
- All lessons have slugs
- Navigation works

#### Stage 9: Update all tests
**Description:** Ensure all tests use new schema
**Tasks:**
- [ ] Update test fixtures to include slugs
- [ ] Update repository tests for slug methods
- [ ] Update learning flow tests
- [ ] Update integration tests
- [ ] Run full test suite

**Validation:**
- All tests pass
- Coverage maintained

### Action Order
1. Implement slug generation (Stage 1)
2. Update database model (Stage 2)
3. Create migration (Stage 3)
4. Update lesson loader (Stage 4)
5. Add repository methods (Stage 5)
6. Update learning flow (Stage 6)
7. Update schema (Stage 7)
8. Run migration (Stage 8)
9. Update tests (Stage 9)
10. Validate end-to-end

### Dependencies
- **Blocks on:** Task PRMT-202 (lesson loader must exist)
- **Blocked by:** None
- **Required for:** Clean lesson ordering without file renaming

---

## TESTING AND VALIDATION

### Unit Tests
```python
import pytest
from promptheus.data.lesson_loader import generate_slug

def test_generate_slug_basic():
    # Given
    title = "Introduction to Prompt Engineering"
    
    # When
    slug = generate_slug(title)
    
    # Then
    assert slug == "introduction-to-prompt-engineering"

def test_generate_slug_removes_special_characters():
    # Given
    title = "Testing @ Special #Characters!"
    
    # When
    slug = generate_slug(title)
    
    # Then
    assert slug == "testing-special-characters"
    assert "#" not in slug
    assert "@" not in slug

def test_generate_slug_handles_consecutive_hyphens():
    # Given
    title = "Test   Multiple    Spaces"
    
    # When
    slug = generate_slug(title)
    
    # Then
    assert slug == "test-multiple-spaces"
    assert "--" not in slug

def test_generate_slug_truncates_long_titles():
    # Given
    title = "A" * 150
    
    # When
    slug = generate_slug(title, max_length=100)
    
    # Then
    assert len(slug) <= 100
    assert not slug.endswith("-")

@pytest.mark.asyncio
async def test_find_by_slug_returns_correct_lesson(lesson_repo):
    # Given
    skill_level = SkillLevel.BEGINNER
    slug = "introduction-to-prompting"
    
    # When
    lesson = await lesson_repo.find_by_slug(skill_level, slug)
    
    # Then
    assert lesson is not None
    assert lesson.slug == slug
    assert lesson.skill_level == skill_level

@pytest.mark.asyncio
async def test_lessons_ordered_by_position(lesson_repo):
    # Given: Lessons with positions [30, 10, 20]
    # (assume data setup in fixture)
    
    # When
    lessons = await lesson_repo.find_by_skill_level(SkillLevel.BEGINNER)
    
    # Then
    positions = [l.position for l in lessons if l.position is not None]
    assert positions == sorted(positions)  # [10, 20, 30]
```

### Commands to Run
```bash
# Run slug tests
uv run pytest tests/data/test_lesson_slug.py -v

# Run migration
uv run alembic upgrade head

# Check migration status
uv run alembic current

# Rollback if needed
uv run alembic downgrade -1

# Run full test suite
uv run pytest

# Check coverage
uv run pytest --cov=src/promptheus --cov-report=term
```

### Manual Testing Scenarios
1. **Scenario 1: Migration with existing data**
   - Steps:
     1. Ensure database has lessons with order_index
     2. Run migration: `uv run alembic upgrade head`
     3. Query database: `SELECT id, title, slug, position FROM lesson LIMIT 5;`
     4. Verify slugs generated correctly
   - Expected result: All lessons have slugs, data intact

2. **Scenario 2: Insert lesson with slug**
   - Steps:
     1. Start application
     2. Add new lesson JSON file with slug
     3. Restart application (triggers loader)
     4. Query database for new lesson
   - Expected result: Lesson inserted with correct slug

3. **Scenario 3: Lesson navigation by position**
   - Steps:
     1. Set positions for lessons (10, 20, 30)
     2. Navigate through lessons in app
     3. Verify order matches positions
   - Expected result: Navigation follows position order

---

## ADDITIONAL CONSIDERATIONS

### Risks
- **Risk 1:** Slug collisions from similar titles
  - **Mitigation:** Uniqueness constraint catches duplicates
  - **Mitigation:** Manual review of generated slugs during content creation
  
- **Risk 2:** Migration breaks existing user progress
  - **Mitigation:** Migrate user progress references before removing order_index
  - **Mitigation:** Thorough testing before production deployment
  - **Mitigation:** Database backup before migration
  
- **Risk 3:** Performance degradation from new indexes
  - **Mitigation:** Benchmark queries before/after
  - **Mitigation:** Use EXPLAIN ANALYZE to verify index usage

### Assumptions
- Lesson titles are relatively unique within skill level
- File naming doesn't need strict numbering (alphabetical ok)
- Position field migrated from order_index (order_index * 10 for gaps)
- Migration window available for brief table lock
- No need to preserve order_index after migration completes
- Downgrade path recreates order_index from position if needed

### Limitations
- Slug changes require manual intervention (not auto-detected)
- Historical slug references not tracked (consider for versioning later)
- Position gaps may grow over time (periodic compaction needed)

### Future Improvements
- Slug history tracking (for URL redirects)
- Automatic position compaction/rebalancing
- Slug preview in content validation
- Multi-language slug support (transliteration)

### Questions and Unresolved Issues
- [x] **RESOLVED:** Should we auto-generate position values or leave null initially?
  - **Decision:** Auto-generate from file order (index * 10) for flexibility, migrate from order_index (order_index * 10)
- [x] **RESOLVED:** Should old order_index be removed immediately or kept long-term?
  - **Decision:** Remove immediately in same migration after data transfer to position
- [ ] How to handle slug conflicts in multi-language scenarios?
  - **Decision:** Future enhancement, out of scope for now

---

## COMPLETION CHECKLIST

### Development
- [ ] Slug generation function implemented
- [ ] Database model updated with slug and position
- [ ] Alembic migration created and tested
- [ ] Lesson loader generates slugs
- [ ] Repository methods support slug lookup
- [ ] Learning flow uses slug-based navigation
- [ ] Pydantic schema includes slug

### Testing
- [ ] Unit tests for slug generation
- [ ] Repository tests for slug methods
- [ ] Migration tested with real data
- [ ] Integration tests updated
- [ ] All tests pass
- [ ] Code coverage >= 85%

### Documentation
- [ ] Docstrings on new methods
- [ ] Migration documented
- [ ] README updated with slug information
- [ ] Comments on deprecated order_index field

### Code Quality
- [ ] Ruff reports no errors
- [ ] Mypy reports no errors
- [ ] Migration includes upgrade and downgrade
- [ ] No breaking changes to public API

### Performance
- [ ] Slug queries benchmarked (<10ms)
- [ ] Migration tested with realistic data volume

### Finalization
- [ ] Changes committed: `feat(data): replace order_index with slug-based identification`
- [ ] Migration tested in development environment
- [ ] Rollback plan documented
- [ ] Task marked as "Ready for Review"

---

**Notes:**
- This task requires careful migration strategy due to database changes
- order_index removed immediately after data transfer to position (no transition period)
- Migration includes downgrade path that recreates order_index from position
- Database backup required before migration
- Consider running migration during maintenance window
- Ensure all user progress references are migrated before removing order_index
