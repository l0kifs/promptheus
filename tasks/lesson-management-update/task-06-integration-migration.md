# Technical Task: Final Integration and Migration

## METADATA

**Task ID:** PRMT-206  
**Name:** Integrate new lesson management system and deprecate seed script  
**Created:** 2025-11-09  
**Priority:** High  
**Complexity Estimate:** 5/10  
**Estimated Time:** 4-6 hours

---

## BUSINESS CONTEXT

### Problem Description
After implementing all individual lesson management components (Tasks PRMT-201 through PRMT-205), the system needs final integration testing, documentation updates, and migration from the old seed script approach. The promptheus-content repository should be cleaned up to contain only lesson JSON files and documentation, with all application logic moved to the main promptheus repository.

### Business Goals
- Complete transition to new organic lesson management system
- Remove dependency on external seeding script
- Ensure smooth deployment with zero data loss
- Provide clear documentation for content creators
- Validate all components work together seamlessly

### Target Audience
- **Primary:** DevOps engineers deploying the system
- **Secondary:** Content creators using the new workflow
- **Tertiary:** Backend developers maintaining the system

### Business Value
- Simplified deployment process (no separate seeding step)
- Reduced risk of deployment failures (integrated system)
- Better developer experience (all logic in one place)
- Clear documentation for future maintenance

---

## TECHNICAL SPECIFICATION

### Functional Requirements

#### Main Functionality
As a deployment process, I want to integrate all lesson management components and migrate from the old seed script, so that the system operates seamlessly with the new architecture.

#### Detailed Requirements

1. **End-to-End Integration**
   - Description: Ensure all components work together
   - Components to integrate:
     - Pydantic schemas (PRMT-201)
     - Lesson loader service (PRMT-202)
     - Slug-based identification (PRMT-203)
     - Cache with hot reload (PRMT-204)
     - Versioning system (PRMT-205)
   - Validation: Full user journey from file to bot response

2. **Database Migration Strategy**
   - Description: Migrate existing production data to new schema
   - Phases:
     - Phase 1: Run all pending migrations (slug, version table)
     - Phase 2: Populate slugs from titles
     - Phase 3: Create initial versions for existing lessons
     - Phase 4: Validate data integrity
   - Rollback: Plan for reverting if issues detected

3. **Seed Script Deprecation**
   - Description: Remove old seeding script from promptheus-content
   - Actions:
     - Delete `scripts/seed_lessons.py`
     - Update promptheus-content README with new workflow
     - Add deprecation notice in promptheus-content
   - Transition: Document how to use new system instead

4. **Configuration Updates**
   - Description: Ensure proper configuration for production
   - Settings to verify:
     - `LESSONS_CONTENT_PATH` points to correct location
     - Database connection configured
     - Cache settings appropriate for production
     - File watcher enabled in production
   - Environment: Document required environment variables

5. **Documentation Updates**
   - Description: Update all relevant documentation
   - Documents to update:
     - Main README with new lesson management workflow
     - Deployment guide with migration steps
     - Content creator guide for lesson updates
     - Architecture documentation
   - Examples: Provide concrete examples of new workflow

6. **Testing and Validation**
   - Description: Comprehensive testing of integrated system
   - Test scenarios:
     - Fresh installation (no existing data)
     - Migration from old system (with existing data)
     - Hot reload functionality
     - Version rollback
     - Cache invalidation
   - Validation: All critical paths work correctly

### Non-Functional Requirements

#### Performance
- Complete migration in <5 minutes for 100 lessons
- Application startup time <10 seconds with lessons loaded
- No performance degradation vs old system

#### Reliability
- Zero data loss during migration
- Rollback plan tested and ready
- All migrations reversible
- Clear error messages for issues

#### Compatibility
- Works with both local development and Docker deployment
- Compatible with existing database schema
- Backward compatible API (during transition)

---

## TECHNICAL CONTEXT

### System Architecture
```
┌─────────────────────────────────────────────────────┐
│  Promptheus-Content Repository (Simplified)         │
│  ├── lessons/                                       │
│  │   ├── beginner/*.json                           │
│  │   ├── intermediate/*.json                       │
│  │   └── advanced/*.json                           │
│  └── docs/                                          │
│      └── lesson-catalog.md                         │
└─────────────────────────────────────────────────────┘
                        │
                        │ (mounted or sibling dir)
                        ▼
┌─────────────────────────────────────────────────────┐
│  Promptheus Application (Integrated System)         │
│  ┌───────────────────────────────────────────────┐  │
│  │  Application Startup                          │  │
│  │  1. Load config (lessons path)                │  │
│  │  2. Run migrations (slug + versions)          │  │
│  │  3. Initialize cache                          │  │
│  │  4. Load lessons from JSON (validate)         │  │
│  │  5. Start file watcher                        │  │
│  │  6. Start bot/API                             │  │
│  └───────────────────────────────────────────────┘  │
│                                                      │
│  Components:                                         │
│  ├── Pydantic Schemas (validation)                  │
│  ├── LessonLoaderService (loading)                  │
│  ├── LessonCache (performance)                      │
│  ├── FileWatcher (hot reload)                       │
│  ├── VersionManager (history)                       │
│  └── Repositories (persistence)                     │
└─────────────────────────────────────────────────────┘
```

### Technology Stack
- **Backend:** Python 3.11+, FastAPI, SQLAlchemy
- **Database:** PostgreSQL
- **Migration:** Alembic
- **Deployment:** Docker, docker-compose

### Project Structure
```
promptheus/
├── alembic/versions/
│   ├── xxx_add_lesson_slug.py         ← From PRMT-203
│   └── xxx_add_lesson_versions.py     ← From PRMT-205
├── docs/
│   ├── deployment-plan.md             ← Update
│   ├── system-architecture-document.md ← Update
│   └── content-creation-guide.md      ← Create
├── src/promptheus/
│   ├── data/
│   │   ├── schemas.py                 ← From PRMT-201
│   │   ├── lesson_loader.py           ← From PRMT-202
│   │   ├── lesson_cache.py            ← From PRMT-204
│   │   ├── file_watcher.py            ← From PRMT-204
│   │   └── version_manager.py         ← From PRMT-205
│   └── main.py                        ← Integrated startup
├── scripts/
│   └── migrate_from_old_system.py     ← Create migration helper
└── README.md                          ← Update

promptheus-content/
├── lessons/                           ← Keep
│   ├── beginner/
│   ├── intermediate/
│   └── advanced/
├── docs/                              ← Keep
│   ├── lesson-catalog.md
│   └── content-workflow.md            ← Create
├── scripts/                           ← Delete
│   └── seed_lessons.py                ← Remove
└── README.md                          ← Update
```

### Files to Modify

1. **`promptheus/src/promptheus/main.py`** (VERIFY)
   - Purpose: Ensure all components initialized correctly
   - Check: Startup sequence calls all necessary initialization
   - Notes: Should already be done in individual tasks

2. **`promptheus/scripts/migrate_from_old_system.py`** (CREATE)
   - Purpose: Helper script for one-time migration
   - Functionality: Populate slugs, create initial versions
   - Notes: Idempotent (can run multiple times safely)

3. **`promptheus/docs/deployment-plan.md`** (UPDATE)
   - Purpose: Document new deployment process
   - Add: Migration steps from old system
   - Add: Configuration requirements

4. **`promptheus/docs/content-creation-guide.md`** (CREATE)
   - Purpose: Guide for content creators
   - Content: How to add/update lessons, JSON format, best practices
   - Examples: Sample lesson JSON, slug naming

5. **`promptheus/README.md`** (UPDATE)
   - Purpose: Update main documentation
   - Remove: References to old seed script
   - Add: New lesson management workflow

6. **`promptheus-content/README.md`** (UPDATE)
   - Purpose: Simplify content repository documentation
   - Remove: Seed script instructions
   - Add: Reference to main repo's content guide

7. **`promptheus-content/docs/content-workflow.md`** (CREATE)
   - Purpose: Document content creation workflow
   - Content: JSON format, file naming, hot reload behavior

8. **`promptheus-content/scripts/seed_lessons.py`** (DELETE)
   - Purpose: Remove deprecated script
   - Add: Deprecation notice in commit message

---

## EXAMPLES AND DOCUMENTATION

### Code Examples

#### Example 1: Migration helper script
```python
"""One-time migration from old system to new lesson management.

This script:
1. Ensures all lessons have slugs
2. Creates initial version (1.0.0) for each lesson
3. Validates data integrity

Run once after deploying new system.
"""
import asyncio
from pathlib import Path

from loguru import logger
from promptheus.data.async_repositories import (
    AsyncLessonRepository,
    AsyncLessonVersionRepository,
)
from promptheus.data.database import AsyncSessionLocal
from promptheus.data.lesson_loader import generate_slug
from promptheus.data.version_manager import VersionManager


async def migrate_lessons() -> None:
    """Migrate existing lessons to new system."""
    logger.info("Starting migration from old system")
    
    lesson_repo = AsyncLessonRepository(AsyncSessionLocal)
    version_repo = AsyncLessonVersionRepository(AsyncSessionLocal)
    version_manager = VersionManager(version_repo, lesson_repo)
    
    # Get all lessons
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Lesson))
        lessons = result.scalars().all()
    
    logger.info(f"Found {len(lessons)} lessons to migrate")
    
    for lesson in lessons:
        # 1. Ensure slug exists
        if not lesson.slug:
            slug = generate_slug(lesson.title)
            logger.info(f"Generating slug for '{lesson.title}': {slug}")
            async with AsyncSessionLocal() as session:
                lesson_obj = await session.get(Lesson, lesson.id)
                lesson_obj.slug = slug
                await session.commit()
        
        # 2. Create initial version if doesn't exist
        existing_versions = await version_repo.get_all_versions(lesson.id)
        if not existing_versions:
            logger.info(f"Creating initial version for '{lesson.title}'")
            await version_manager.create_version(
                lesson_id=lesson.id,
                content={
                    "theory_content": lesson.theory_content,
                    "examples": lesson.examples,
                    "exercises": lesson.exercises,
                },
                change_type="major",  # Initial version
                created_by="migration",
                description="Initial version from migration",
            )
    
    logger.success("Migration complete!")


async def validate_migration() -> None:
    """Validate migration results."""
    logger.info("Validating migration")
    
    lesson_repo = AsyncLessonRepository(AsyncSessionLocal)
    version_repo = AsyncLessonVersionRepository(AsyncSessionLocal)
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Lesson))
        lessons = result.scalars().all()
    
    errors = []
    
    for lesson in lessons:
        # Check slug
        if not lesson.slug:
            errors.append(f"Lesson {lesson.id} missing slug")
        
        # Check versions
        versions = await version_repo.get_all_versions(lesson.id)
        if not versions:
            errors.append(f"Lesson {lesson.id} has no versions")
        
        # Check active version
        active_versions = [v for v in versions if v.is_active]
        if len(active_versions) != 1:
            errors.append(f"Lesson {lesson.id} has {len(active_versions)} active versions (should be 1)")
    
    if errors:
        logger.error("Validation failed!")
        for error in errors:
            logger.error(f"  - {error}")
        raise ValueError("Migration validation failed")
    else:
        logger.success("Validation passed!")


if __name__ == "__main__":
    asyncio.run(migrate_lessons())
    asyncio.run(validate_migration())
```

#### Example 2: Updated deployment steps (for docs)
```markdown
## Deployment Process

### Prerequisites
- PostgreSQL database accessible
- Promptheus-content repository cloned or mounted at configured path
- Environment variables configured (see Configuration section)

### Deployment Steps

#### 1. Database Migrations
```bash
# Run all pending migrations
uv run alembic upgrade head

# This includes:
# - Adding slug and position fields (PRMT-203)
# - Creating lesson_version table (PRMT-205)
```

#### 2. Data Migration (One-time)
```bash
# For existing installations only
# Populates slugs and creates initial versions
uv run python scripts/migrate_from_old_system.py
```

#### 3. Start Application
```bash
# The application will:
# - Load configuration
# - Initialize cache
# - Load lessons from JSON files (with validation)
# - Start file watcher for hot reload
# - Start API/bot services

uv run uvicorn promptheus.main:app --host 0.0.0.0 --port 8000
```

#### 4. Verify Deployment
```bash
# Check health endpoint
curl http://localhost:8000/health

# Should show:
# - Database connected
# - Cache loaded with X lessons
# - File watcher active

# Check lesson count
curl http://localhost:8000/admin/cache/stats
```

### Rollback Plan

If issues are detected:

1. **Stop application**
2. **Revert database migrations**
   ```bash
   uv run alembic downgrade -1  # Revert one migration
   ```
3. **Restore from backup** (if data corruption)
4. **Deploy previous application version**

### Configuration

Required environment variables:
- `DATABASE_URL`: PostgreSQL connection string
- `LESSONS_CONTENT_PATH`: Path to lessons directory
- `TELEGRAM_BOT_TOKEN`: Bot token (for bot mode)
- `OPENROUTER_API_KEY`: AI API key

Optional:
- `LOG_LEVEL`: Logging level (default: INFO)
- `CACHE_SIZE_LIMIT`: Max cache size (default: unlimited)
```

#### Example 3: Content creation guide
```markdown
# Content Creation Guide

## Lesson JSON Format

Each lesson is defined in a JSON file in the appropriate skill level directory:
- `lessons/beginner/`
- `lessons/intermediate/`
- `lessons/advanced/`

### File Naming

Files are ordered alphabetically, so use prefixes for explicit ordering:
- ✅ `introduction-to-prompting.json`
- ✅ `defining-ai-roles.json`
- ✅ `providing-context.json`

**No number prefixes needed!** The system automatically determines order.

### JSON Structure

```json
{
  "title": "Introduction to Prompt Engineering",
  "slug": "introduction-to-prompt-engineering",
  "skill_level": "beginner",
  "tags": ["general", "academic"],
  "version": "1.0.0",
  "theory_content": {
    "sections": [
      {
        "content": "Prompt engineering is the art of crafting effective instructions."
      }
    ]
  },
  "examples": {
    "comparisons": [
      {
        "bad": "Tell me about Python",
        "bad_reason": "Too vague",
        "good": "Explain Python list comprehensions to a beginner",
        "good_reason": "Specific and clear"
      }
    ]
  },
  "exercises": {
    "scenarios": [
      {
        "scenario": "You need help with a new concept",
        "task": "Write a prompt asking AI to explain OOP"
      }
    ]
  }
}
```

### Making Changes

1. **Edit JSON file** in your local editor
2. **Save the file**
3. **Wait 1-2 seconds** - the system detects changes automatically
4. **Test in bot/API** - changes are live immediately!

### Versioning

- Each content change creates a new version automatically
- Version format: `MAJOR.MINOR.PATCH` (e.g., "1.2.3")
- Previous versions are stored for rollback if needed

### Best Practices

✅ **Do:**
- Use clear, descriptive titles
- Keep slugs lowercase with hyphens
- Write concise theory sections (50-80 words)
- Provide at least 2 example comparisons
- Include practical exercise scenarios

❌ **Don't:**
- Use special characters in slugs
- Make theory sections too long (>200 words)
- Forget to validate JSON syntax
- Use duplicate titles across skill levels
```

### Documentation
- [Alembic Migrations](https://alembic.sqlalchemy.org/en/latest/tutorial.html)
- [Docker Compose](https://docs.docker.com/compose/)
- [Deployment Best Practices](https://12factor.net/)

### Existing Patterns
- **Migration Scripts:** Follow Alembic patterns
- **Documentation:** Follow project docs style
- **Error Handling:** Comprehensive logging

### Known Pitfalls
⚠️ **Important:**
- **Migration order:** Run in sequence, don't skip versions
- **Data backup:** Always backup before running migration
- **Volume mounting:** Ensure lessons path correctly mounted in Docker
- **File permissions:** Lessons directory must be readable
- **Environment variables:** All required vars must be set

---

## ACCEPTANCE CRITERIA

### Scenario Criteria (Given-When-Then)

#### Scenario 1: Fresh installation works end-to-end
```gherkin
Given database is empty
And lesson JSON files exist in content repository
When application starts
Then all migrations run successfully
And lessons are loaded and validated
And cache is populated
And file watcher starts
And application is ready to serve requests
```

#### Scenario 2: Migration from old system successful
```gherkin
Given database has lessons with order_index but no slugs
And no version records exist
When migration script runs
Then slugs are generated from titles
And initial versions (1.0.0) are created for all lessons
And all lessons have exactly one active version
And no data is lost
```

#### Scenario 3: Hot reload works after integration
```gherkin
Given application is running
And lesson is cached
When lesson JSON file is modified
Then file change is detected within 1 second
And lesson is reloaded and validated
And new version is created
And cache is updated
And users see updated content
```

#### Scenario 4: Seed script removed
```gherkin
Given promptheus-content repository
When checking scripts directory
Then seed_lessons.py does not exist
And README mentions new workflow
And deprecation notice in git history
```

#### Scenario 5: Documentation complete
```gherkin
Given all documentation files
When reviewing deployment guide
Then migration steps are clear
And configuration requirements documented
And rollback plan explained
And content creation workflow documented
```

### Rules and Constraints
- [ ] All migrations are reversible
- [ ] Zero data loss during migration
- [ ] Application startup succeeds with all components
- [ ] Old seed script removed from content repo
- [ ] All documentation updated and accurate
- [ ] Test coverage maintained (>=80%)

### Testing
- [ ] Fresh installation tested (empty database)
- [ ] Migration tested with real data
- [ ] Hot reload tested end-to-end
- [ ] Version creation and rollback tested
- [ ] Cache invalidation tested
- [ ] All integration tests pass

### Code Review
- [ ] Migration script reviewed and tested
- [ ] Documentation clear and accurate
- [ ] No hardcoded values
- [ ] Error handling comprehensive
- [ ] Rollback plan tested

### Performance
- [ ] Migration completes in <5 minutes for 100 lessons
- [ ] Application startup <10 seconds
- [ ] No performance regression

---

## IMPLEMENTATION PLAN

### Execution Stages

#### Stage 1: Verify all components integrated
**Description:** Ensure previous tasks complete and work together
**Tasks:**
- [ ] Verify Pydantic schemas (PRMT-201) complete
- [ ] Verify lesson loader (PRMT-202) complete
- [ ] Verify slug migration (PRMT-203) complete
- [ ] Verify cache/hot reload (PRMT-204) complete
- [ ] Verify versioning (PRMT-205) complete
- [ ] Check all migrations exist in alembic/versions/
- [ ] Run full test suite

**Validation:**
- All individual tasks complete
- Tests pass

#### Stage 2: Create migration helper script
**Description:** Script for one-time data migration
**Tasks:**
- [ ] Create `scripts/migrate_from_old_system.py`
- [ ] Implement slug population logic
- [ ] Implement initial version creation
- [ ] Add validation checks
- [ ] Make idempotent (safe to run multiple times)
- [ ] Add comprehensive logging
- [ ] Test with realistic data

**Validation:**
- Script runs successfully
- Data integrity maintained

#### Stage 3: Test end-to-end integration
**Description:** Comprehensive integration testing
**Tasks:**
- [ ] Test fresh installation (empty DB)
- [ ] Test migration from old system
- [ ] Test hot reload workflow
- [ ] Test version creation on changes
- [ ] Test rollback functionality
- [ ] Test cache invalidation
- [ ] Test in Docker environment
- [ ] Load test with many lessons

**Validation:**
- All scenarios work correctly
- Performance acceptable

#### Stage 4: Update documentation
**Description:** Update all relevant docs
**Tasks:**
- [ ] Update `promptheus/README.md`:
  - [ ] Remove seed script references
  - [ ] Add new lesson workflow
  - [ ] Update architecture section
- [ ] Update `promptheus/docs/deployment-plan.md`:
  - [ ] Add migration steps
  - [ ] Document configuration
  - [ ] Add rollback plan
- [ ] Create `promptheus/docs/content-creation-guide.md`:
  - [ ] JSON format specification
  - [ ] File naming conventions
  - [ ] Hot reload behavior
  - [ ] Best practices
- [ ] Update `promptheus-content/README.md`:
  - [ ] Remove seed script instructions
  - [ ] Add reference to main repo guide
  - [ ] Simplify to content-only focus
- [ ] Create `promptheus-content/docs/content-workflow.md`:
  - [ ] Quick reference for content creators
  - [ ] Example JSON with annotations

**Validation:**
- All documentation clear and accurate
- No broken links

#### Stage 5: Remove old seed script
**Description:** Clean up deprecated code
**Tasks:**
- [ ] Delete `promptheus-content/scripts/seed_lessons.py`
- [ ] Delete `promptheus-content/scripts/` directory if empty
- [ ] Add deprecation notice in git commit
- [ ] Update CHANGELOG in promptheus-content
- [ ] Tag content repo version

**Validation:**
- Seed script no longer exists
- Git history preserved

#### Stage 6: Final validation
**Description:** Comprehensive testing before release
**Tasks:**
- [ ] Run all tests (unit, integration, e2e)
- [ ] Test in development environment
- [ ] Test in staging environment (if available)
- [ ] Verify performance benchmarks
- [ ] Check all documentation links
- [ ] Review all code changes
- [ ] Run security scan
- [ ] Verify Docker build

**Validation:**
- All tests pass
- Performance meets requirements
- Security checks pass

#### Stage 7: Prepare deployment
**Description:** Final preparation for production
**Tasks:**
- [ ] Create deployment checklist
- [ ] Prepare rollback plan
- [ ] Schedule maintenance window (if needed)
- [ ] Backup production database
- [ ] Notify stakeholders of changes
- [ ] Prepare monitoring/alerts

**Validation:**
- Deployment plan ready
- Rollback tested
- Team prepared

### Action Order
1. Verify integration (Stage 1)
2. Create migration script (Stage 2)
3. Test end-to-end (Stage 3)
4. Update documentation (Stage 4)
5. Remove old code (Stage 5)
6. Final validation (Stage 6)
7. Prepare deployment (Stage 7)

### Dependencies
- **Blocks on:** ALL previous tasks (PRMT-201 through PRMT-205)
- **Blocked by:** None (final task)

---

## TESTING AND VALIDATION

### Integration Tests
```python
import pytest
from promptheus.main import app
from fastapi.testclient import TestClient

@pytest.mark.integration
def test_fresh_installation_flow(clean_database, lesson_files):
    """Test complete flow from scratch."""
    # Given: Clean database and lesson files
    assert database_is_empty()
    
    # When: Application starts
    with TestClient(app) as client:
        # Startup triggers lesson loading
        
        # Then: Lessons loaded
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["cache"]["size"] > 0
        
        # Can retrieve lesson
        response = client.get("/api/lessons/beginner/introduction-to-prompting")
        assert response.status_code == 200

@pytest.mark.integration
async def test_migration_from_old_system():
    """Test migration script with old data."""
    # Given: Database with old schema (order_index, no slugs)
    await populate_old_schema_data()
    
    # When: Migration runs
    from scripts.migrate_from_old_system import migrate_lessons, validate_migration
    await migrate_lessons()
    
    # Then: Validation passes
    await validate_migration()  # Raises if issues

@pytest.mark.integration
async def test_hot_reload_end_to_end(running_app, temp_lesson_file):
    """Test hot reload after integration."""
    # Given: Application running with lesson loaded
    # ... modify lesson file
    # Wait for reload
    await asyncio.sleep(2)
    # Then: Updated content served
    # ... assert changes visible
```

### Commands to Run
```bash
# Run full test suite
uv run pytest

# Run integration tests specifically
uv run pytest -m integration

# Run migration script
uv run python scripts/migrate_from_old_system.py

# Validate migration
uv run python scripts/migrate_from_old_system.py --validate-only

# Start application
uv run uvicorn promptheus.main:app --reload

# Check health
curl http://localhost:8000/health

# Build Docker image
docker build -t promptheus:latest .

# Run with docker-compose
docker-compose up
```

### Manual Testing Scenarios
1. **Scenario 1: Deploy to fresh environment**
   - Steps:
     1. Set up clean database
     2. Mount lessons directory
     3. Start application
     4. Check health endpoint
     5. Test lesson retrieval
     6. Test hot reload
   - Expected result: Everything works

2. **Scenario 2: Migrate existing production data**
   - Steps:
     1. Backup production database
     2. Run migration script on copy
     3. Validate results
     4. Deploy updated application
     5. Smoke test critical paths
   - Expected result: Zero data loss, all features work

3. **Scenario 3: Content creator workflow**
   - Steps:
     1. Content creator edits lesson JSON
     2. Saves file
     3. Waits 2 seconds
     4. Tests in bot/API
     5. Sees updated content
   - Expected result: Seamless experience

---

## ADDITIONAL CONSIDERATIONS

### Risks
- **Risk 1:** Migration fails mid-process
  - **Mitigation:** Idempotent migration script
  - **Mitigation:** Database backup before migration
  - **Mitigation:** Comprehensive validation step
  
- **Risk 2:** Performance issues in production
  - **Mitigation:** Load testing before deployment
  - **Mitigation:** Monitoring and alerts configured
  - **Mitigation:** Rollback plan ready
  
- **Risk 3:** Documentation gaps cause confusion
  - **Mitigation:** Peer review of all documentation
  - **Mitigation:** Test documentation by following steps

### Assumptions
- All previous tasks (PRMT-201 to PRMT-205) are complete
- Production has database backup capability
- Lessons content repository is accessible
- Maintenance window available for migration

### Limitations
- Migration is one-way (no automatic rollback)
- Requires brief downtime for database migration
- Content repository must be accessible during runtime

### Future Improvements
- Automated integration testing in CI/CD
- Canary deployment support
- Automated rollback triggers
- Content validation in pre-commit hooks

### Questions and Unresolved Issues
- [ ] Do we need maintenance window for migration?
  - **Decision:** Brief window recommended for safety (5-10 minutes)
- [ ] Should migration be manual or automated in CI/CD?
  - **Decision:** Manual for initial deployment, automate later
- [ ] How to handle migration in multi-instance deployments?
  - **Decision:** Run migration once, then deploy updated code

---

## COMPLETION CHECKLIST

### Development
- [ ] All previous tasks (PRMT-201 to PRMT-205) verified complete
- [ ] Migration helper script created and tested
- [ ] All components integrated in main.py
- [ ] Error handling comprehensive

### Testing
- [ ] Fresh installation tested
- [ ] Migration from old system tested
- [ ] End-to-end hot reload tested
- [ ] Version creation/rollback tested
- [ ] Cache invalidation tested
- [ ] Performance benchmarks met
- [ ] All integration tests pass

### Documentation
- [ ] Main README updated
- [ ] Deployment plan updated
- [ ] Content creation guide created
- [ ] Content repo README updated
- [ ] Workflow guide created
- [ ] All links verified

### Code Quality
- [ ] Old seed script removed
- [ ] Code review completed
- [ ] Security scan passed
- [ ] No hardcoded values

### Deployment
- [ ] Deployment checklist created
- [ ] Rollback plan documented and tested
- [ ] Database backup plan confirmed
- [ ] Monitoring configured
- [ ] Team notified

### Finalization
- [ ] All changes committed with clear messages
- [ ] Tagged release version
- [ ] Deployment guide reviewed
- [ ] Task marked as "Complete"

---

**Notes:**
- This is the final task that ties everything together
- Success depends on completion of all previous tasks
- Comprehensive testing is critical before production deployment
- Clear documentation ensures smooth operation and maintenance
- Migration script should be kept for reference even after use
