# Plan to Fix Database Schema Issues 4.1-4.4

## Overview
This plan addresses the database schema discrepancies identified in the documentation mismatches analysis. Issues 4.1-4.3 can be resolved by applying the existing migration `4c8d2abc8f95_add_constraints.py`, while issue 4.4 requires code changes for PostgreSQL compatibility.

## Current State Analysis
- **Database**: SQLite with initial schema applied, constraints migration not yet applied
- **Models**: Updated with constraints in code, but database not migrated
- **Migration Status**: `alembic check` shows database is not up to date

## Issues to Fix

### Issue 4.1: User Table Assessment Score Constraint
**Problem**: Missing CHECK constraint for `assessment_score` range (0-100)
**Current State**: Constraint exists in models.py but not in database
**Solution**: Apply existing migration

### Issue 4.2: Lesson Table Indexes
**Problem**: Missing UNIQUE constraint and composite index on `(skill_level, order_index)`
**Current State**: Constraints exist in models.py but not in database
**Solution**: Apply existing migration

### Issue 4.3: UserProgress Table Constraints
**Problem**: Missing UNIQUE constraint on `(user_id, lesson_id)` and composite index on `(user_id, status)`
**Current State**: Constraints exist in models.py but not in database
**Solution**: Apply existing migration

### Issue 4.4: Timestamp Handling for PostgreSQL
**Problem**: Using naive datetime (`datetime.utcnow`) instead of timezone-aware timestamps
**Current State**: Models use `datetime.utcnow` which may cause issues when migrating to PostgreSQL
**Solution**: Update models to use timezone-aware timestamps

## Detailed Implementation Plan

### Phase 1: Apply Existing Migration (Issues 4.1-4.3)

#### Step 1.1: Backup Database
- [ ] Create backup of current database: `cp data/promptheus.db data/promptheus_backup_$(date +%Y%m%d_%H%M%S).db`
- [ ] Verify backup integrity: `sqlite3 data/promptheus_backup.db ".schema"`

#### Step 1.2: Test Migration in Development
- [ ] Run tests to ensure current functionality works: `uv run pytest tests/ -v`
- [ ] Apply migration in dry-run mode: `uv run alembic upgrade head --sql > migration_preview.sql`
- [ ] Review SQL changes in `migration_preview.sql`

#### Step 1.3: Apply Migration to Database
- [ ] Apply migration: `uv run alembic upgrade head`
- [ ] Verify migration success: `uv run alembic check` (should pass)
- [ ] Run tests again to ensure no regressions: `uv run pytest tests/ -v`

#### Step 1.4: Validate Constraints
- [ ] Test assessment_score constraint:
  ```sql
  INSERT INTO user (telegram_id, skill_level, learning_goal, assessment_score)
  VALUES (999999, 'beginner', 'academic', 150); -- Should fail
  ```
- [ ] Test lesson uniqueness constraint:
  ```sql
  INSERT INTO lesson (title, skill_level, order_index, tags, theory_content, examples, exercises, created_at)
  VALUES ('Test Lesson', 'beginner', 1, '[]', '{}', '{}', '{}', datetime('now')); -- Should fail if order_index 1 exists
  ```
- [ ] Test user_progress uniqueness:
  ```sql
  INSERT INTO user_progress (user_id, lesson_id, status, attempts)
  VALUES (12345, 1, 'not_started', 0); -- Should fail if already exists
  ```

### Phase 2: Fix Timestamp Handling (Issue 4.4)

#### Step 2.1: Update Models for Timezone Awareness
- [ ] Modify `src/promptheus/data/models.py`:
  ```python
  from datetime import datetime, timezone
  
  # Replace datetime.utcnow with timezone-aware version
  created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
  updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
  completed_at = Column(DateTime(timezone=True), nullable=True)
  ```

#### Step 2.2: Create Migration for Timestamp Changes
- [ ] Generate new migration: `uv run alembic revision --autogenerate -m "Add timezone support to timestamps"`
- [ ] Review generated migration for correctness
- [ ] Apply migration: `uv run alembic upgrade head`

#### Step 2.3: Update Application Code
- [ ] Update any code that creates datetime objects to use timezone-aware versions
- [ ] Update settings and configuration to handle timezone-aware datetimes
- [ ] Test date serialization/deserialization in JSON responses

#### Step 2.4: Test PostgreSQL Compatibility
- [ ] Create test PostgreSQL database
- [ ] Run migrations against PostgreSQL
- [ ] Test data insertion and retrieval with timezone-aware timestamps
- [ ] Verify timezone conversion works correctly

## Testing and Validation

### Automated Tests
- [ ] Add tests for database constraints:
  ```python
  def test_assessment_score_constraint():
      # Test that invalid scores are rejected
      pass
  
  def test_lesson_uniqueness_constraint():
      # Test that duplicate skill_level+order_index is rejected
      pass
  
  def test_user_progress_uniqueness():
      # Test that duplicate user_id+lesson_id is rejected
      pass
  ```

### Integration Tests
- [ ] Test constraint violations in application code
- [ ] Test timezone handling in date operations
- [ ] Test migration rollback scenarios

### Performance Validation
- [ ] Measure query performance with new indexes
- [ ] Validate that constraints don't impact insert/update performance significantly

## Rollback Plan

### If Migration Fails
1. **Immediate Rollback**: `uv run alembic downgrade -1`
2. **Data Recovery**: Restore from backup if data corruption occurred
3. **Root Cause Analysis**: Review migration logs and database state
4. **Fix and Retry**: Correct migration script and reapply

### If Application Breaks
1. **Code Rollback**: Revert model changes
2. **Database Rollback**: `uv run alembic downgrade fa961e7f0ed3`
3. **Alternative Fix**: Implement constraints at application level instead of DB level

## Success Criteria

### Technical Criteria
- [ ] `alembic check` passes without errors
- [ ] All database constraints are active and enforced
- [ ] Timestamps are stored as timezone-aware in PostgreSQL
- [ ] All existing tests pass
- [ ] New constraint tests pass

### Functional Criteria
- [ ] User onboarding works with score validation
- [ ] Lesson ordering is properly constrained
- [ ] Progress tracking prevents duplicates
- [ ] Date operations work correctly across timezones

### Quality Criteria
- [ ] No performance degradation (>10% slower queries)
- [ ] Migration is reversible (downgrade works)
- [ ] Code follows existing patterns and standards
- [ ] Documentation updated to reflect changes

## Timeline and Dependencies

### Dependencies
- **Database Access**: Need write access to production database
- **Testing Environment**: Separate test database for validation
- **Code Review**: Changes require peer review before deployment

### Timeline
- **Phase 1 (Migration Application)**: 2-4 hours
- **Phase 2 (Timestamp Updates)**: 4-6 hours
- **Testing and Validation**: 2-3 hours
- **Deployment**: 1 hour (with monitoring)

### Risk Assessment
- **Low Risk**: Migration adds constraints (non-breaking for valid data)
- **Medium Risk**: Timestamp changes may affect date serialization
- **High Risk**: Database corruption if migration fails mid-execution

## Monitoring and Follow-up

### Post-Deployment Monitoring
- [ ] Monitor application logs for constraint violation errors
- [ ] Track database performance metrics
- [ ] Monitor user onboarding completion rates
- [ ] Watch for timezone-related bugs

### Documentation Updates
- [ ] Update database schema documentation
- [ ] Update deployment procedures
- [ ] Update troubleshooting guides for constraint errors

## Alternative Approaches

### Option 1: Application-Level Constraints
Instead of database constraints, implement validation in application code:
- Pros: Easier to change, no migration needed
- Cons: Race conditions possible, data integrity not guaranteed

### Option 2: Partial Migration
Apply only critical constraints first, defer timestamp changes:
- Pros: Smaller change set, lower risk
- Cons: Incomplete fix, future migration still needed

## Conclusion

This plan provides a systematic approach to resolving the identified database schema issues. The existing migration addresses most problems, while the timestamp issue requires code changes for future PostgreSQL compatibility. The phased approach minimizes risk while ensuring data integrity and application stability.</content>
<parameter name="filePath">/home/serj/dev/my-github-repos/promptheus/tasks/fix_documentation_mismatches/fix-issues-4-plan.md