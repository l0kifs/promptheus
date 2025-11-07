# Fix Score Calculation Implementation Plan
**Task**: Fix bug where practice scores below 7 are not saved to database

**Created**: November 7, 2025  
**Updated**: November 7, 2025 (Root cause found)  
**Status**: ⚠️ CRITICAL BUG - Scores not being saved!

---

## 📋 Problem Statement

### Current Behavior (BUGGY)
The system **only saves scores when they are >= 7**:
- User attempts lesson 1, gets score 2/10 → Score NOT saved ❌
- User attempts lesson 2, gets score 3/10 → Score NOT saved ❌
- User attempts lesson 3, gets score 8/10 → Score saved & lesson completed ✅
- Average shown: `8/1 = 8.0` ❌ (wrong - should include all 3 attempts)

### Expected Behavior (CORRECT)
The system should save **ALL scores regardless of value**:
- User attempts lesson 1, gets score 2/10 → Score saved ✅
- User attempts lesson 2, gets score 3/10 → Score saved ✅
- User attempts lesson 3, gets score 8/10 → Score saved & lesson completed ✅
- Average shown: `(2 + 3 + 8)/3 = 4.3` ✅

### Business Impact
- **User Progress Misrepresented**: Users who practice but score low see inflated averages
- **Demotivating**: Users don't see improvement over time (missing low scores)
- **Analytics Broken**: Cannot track which lessons are difficult (missing failure data)
- **Retention Risk**: Users may give up thinking they're not improving

---

## 🔍 Root Cause Analysis

### **ROOT CAUSE FOUND!**

**File**: `/home/kutvik/Documents/vscode/promptheus/src/promptheus/bot/practice_handlers.py`  
**Method**: `practice_submit_handler()`  
**Lines**: 266-283

```python
# Update progress using async progress tracker
await self.progress_tracker.increment_attempts(user_id, lesson_id)

# If score is good enough, mark as completed
score = feedback.get("score", 0)  # ... with parsing logic

if score >= 7:
    await self.progress_tracker.complete_lesson(user_id, lesson_id, score)
    # ^^^ Score is ONLY saved when >= 7!
```

### The Bug
**Scores below 7 are NEVER saved to the database!**

1. User submits practice prompt
2. AI evaluates and returns score (e.g., 2/10)
3. Attempts counter is incremented ✅
4. **IF score >= 7**: Lesson is completed AND score is saved ✅
5. **IF score < 7**: User gets feedback, but **score is NOT saved to DB** ❌

This means:
- User with scores 2, 3, 8 will only have score 8 in database
- Average shows 8/1 = 8.0 instead of (2+3+8)/3 = 4.3

### Why This Happened
The code assumes only "passing" scores (>= 7) need to be saved. But for progress tracking, ALL attempt scores should be recorded regardless of whether they pass or fail.

---

## 🛠️ Implementation Steps

### Step 1: Fix Score Recording in Practice Handler

**File**: `src/promptheus/bot/practice_handlers.py`  
**Method**: `practice_submit_handler()`  
**Line**: After 266

**Current Code** (BUGGY):
```python
# Update progress using async progress tracker
await self.progress_tracker.increment_attempts(user_id, lesson_id)

# If score is good enough, mark as completed
score = ... # parsing logic

if score >= 7:
    await self.progress_tracker.complete_lesson(user_id, lesson_id, score)
    logger.info("Lesson completed", user_id=user_id, lesson_id=lesson_id, score=score)
```

**Fixed Code**:
```python
# Update progress using async progress tracker
await self.progress_tracker.increment_attempts(user_id, lesson_id)

# Parse score safely
score = ... # existing parsing logic

# ALWAYS record the score, regardless of value
await self.progress_tracker.record_attempt(user_id, lesson_id, score)
logger.info("Score recorded", user_id=user_id, lesson_id=lesson_id, score=score)

# If score is good enough, ALSO mark as completed
if score >= 7:
    await self.progress_tracker.complete_lesson(user_id, lesson_id, score)
    logger.info("Lesson completed", user_id=user_id, lesson_id=lesson_id, score=score)
```

**Key Changes**:
1. Add call to `record_attempt()` BEFORE the score check
2. This saves the score for ALL attempts (both passing and failing)
3. Keep the existing `complete_lesson()` call for passing scores
4. Note: `record_attempt()` calls `update_score()` internally, so score is always saved

### Step 2: Fix Display Bug in Progress Handler (Bonus)

**File**: `src/promptheus/bot/progress_handlers.py`  
**Line**: 151

**Current Code** (BUGGY):
```python
status_emoji = "✅" if progress.status == "completed" else "📖"  # type: ignore
```

**Fixed Code**:
```python
from promptheus.data.models import LessonStatus

status_emoji = "✅" if progress.status == LessonStatus.COMPLETED else "📖"  # type: ignore
```

**Why**: Comparing enum with string will always be False. Need to compare with enum value.

### Step 3: Documentation Updates (Keep existing correct updates)

#### 3.1 Update User Stories (US-4.1)
**File**: `/home/kutvik/Documents/vscode/promptheus/docs/user-stories.md`
**Section**: US-4.1: View Progress
**Line**: 152

✅ Already updated correctly

#### 3.2 Update Technical Requirements Document
✅ Already updated correctly

#### 3.3 Update System Architecture Document
✅ Already updated correctly

#### 3.4 Update Database Design Document
✅ Already updated correctly

#### 3.5 Update UX Design Specifications
✅ Already updated correctly

**Note**: Documentation was already fixed in previous work. The actual code bug is now identified and needs fixing.

---

## 🧪 Testing Strategy

### Unit Tests to Add

**File**: `tests/test_practice_handlers.py` (or create if doesn't exist)

**Test Case 1**: Score is saved for failing attempts
```python
async def test_score_saved_for_low_scores():
    """Test that scores below 7 are saved to database."""
    # Setup: User starts lesson
    # Submit practice with score 2/10
    # Verify: last_score = 2 in database
    # Verify: status = IN_PROGRESS
    # Verify: attempts = 1
    
    progress = await progress_repo.find_by_user_and_lesson(user_id, lesson_id)
    assert progress.last_score == 2
    assert progress.status == LessonStatus.IN_PROGRESS
    assert progress.attempts == 1
```

**Test Case 2**: Score is saved and lesson completed for passing attempts
```python
async def test_score_saved_for_high_scores():
    """Test that scores >= 7 are saved AND lesson is completed."""
    # Setup: User starts lesson
    # Submit practice with score 8/10
    # Verify: last_score = 8 in database
    # Verify: status = COMPLETED
    # Verify: completed_at is set
    
    progress = await progress_repo.find_by_user_and_lesson(user_id, lesson_id)
    assert progress.last_score == 8
    assert progress.status == LessonStatus.COMPLETED
    assert progress.completed_at is not None
```

**Test Case 3**: Multiple attempts update last_score
```python
async def test_multiple_attempts_update_score():
    """Test that subsequent attempts update the last_score."""
    # Attempt 1: score 2
    # Attempt 2: score 5
    # Attempt 3: score 8
    # Verify: last_score = 8
    # Verify: attempts = 3
    # Verify: status = COMPLETED (because final score >= 7)
    
    progress = await progress_repo.find_by_user_and_lesson(user_id, lesson_id)
    assert progress.last_score == 8
    assert progress.attempts == 3
    assert progress.status == LessonStatus.COMPLETED
```

### Integration Tests

**File**: `tests/test_progress_tracker.py`

**Test Case 4**: Average includes all attempt scores
```python
async def test_average_score_includes_all_attempts():
    """Test that average score includes both passing and failing attempts."""
    # Setup: User with 3 lessons
    # - Lesson 1: score 2 (in_progress)
    # - Lesson 2: score 5 (in_progress)
    # - Lesson 3: score 8 (completed)
    
    summary = await progress_tracker.get_progress_summary(user_id)
    
    # Should average all three: (2 + 5 + 8) / 3 = 5.0
    assert summary['average_score'] == 5.0
    assert summary['completed'] == 1
    assert summary['total'] == 3
```

### Manual Testing Checklist

1. ✅ Start a lesson
2. ✅ Submit practice with score < 7 (e.g., 2/10)
3. ✅ Check database: `last_score` should be 2
4. ✅ View progress: Average should include the score of 2
5. ✅ Try again with score >= 7 (e.g., 8/10)
6. ✅ Check database: `last_score` updated to 8, status = COMPLETED
7. ✅ View progress: Average should be (2+8)/2 = 5.0 (from 2 attempts)

---

## 📝 Implementation Checklist

### Phase 1: Code Fix (Priority: HIGH)
- [x] Update `practice_handlers.py` to call `record_attempt()` for ALL scores ✅
- [x] Fix status comparison bug in `progress_handlers.py` (bonus fix) ✅
- [x] Add logging to track when scores are saved ✅
- [x] Test manually: submit practice with score < 7, verify it's saved ✅

### Phase 2: Testing (Priority: HIGH)
- [x] Write unit test: score saved for low scores (< 7) ✅
- [x] Write unit test: score saved for high scores (>= 7) ✅
- [x] Write unit test: score saved at threshold (= 7) ✅
- [x] Write unit test: multiple attempts update last_score ✅
- [x] Run all existing tests to ensure no regressions ✅
- [x] Manual testing with real bot interaction ✅

**Status**: ✅ **COMPLETE** - All 4 regression tests passing!

### Phase 3: Documentation (Priority: MEDIUM)
- [x] Update `user-stories.md` (US-4.1) - Already done
- [x] Update `technical-requirements-document.md` - Already done
- [x] Update `system-architecture-document.md` - Already done
- [x] Update `database-design-document.md` - Already done
- [x] Update `ux-design-specifications.md` - Already done

### Phase 4: Deployment (Priority: MEDIUM)
- [ ] Code review and approval
- [ ] Merge to develop branch
- [ ] Test in staging environment
- [ ] Deploy to production
- [ ] Monitor logs for score recording
- [ ] Verify with real users

---

## 🎯 Acceptance Criteria

### Functional
- ✅ Average score includes all lessons with `last_score IS NOT NULL`
- ✅ Both `in_progress` and `completed` lessons are counted
- ✅ Lessons without scores (not attempted) are excluded
- ✅ Progress display shows correct average in UI
- ✅ Calculation rounds to 1 decimal place

### Documentation
- ✅ All documents consistently describe correct behavior
- ✅ User stories reflect actual implementation
- ✅ Technical docs explain calculation logic
- ✅ Database docs clarify business rules

### Testing
- ✅ Unit tests cover all scenarios
- ✅ Integration tests verify UI display
- ✅ Edge cases handled correctly
- ✅ No performance degradation

---

## 📊 Expected Outcomes

### Current Behavior (BUGGY)
```
User attempts 3 lessons:
- Lesson 1: Practice submitted, score 2/10 → NOT SAVED ❌
- Lesson 2: Practice submitted, score 3/10 → NOT SAVED ❌  
- Lesson 3: Practice submitted, score 8/10 → Saved & completed ✅

Database state:
- Lesson 1: status=IN_PROGRESS, last_score=NULL
- Lesson 2: status=IN_PROGRESS, last_score=NULL
- Lesson 3: status=COMPLETED, last_score=8

Displayed: Average Score: 8.0/10 ❌
(Only counting lesson 3 because it's the only one with a score)
```

### After Fix (CORRECT)
```
User attempts 3 lessons:
- Lesson 1: Practice submitted, score 2/10 → SAVED ✅
- Lesson 2: Practice submitted, score 3/10 → SAVED ✅
- Lesson 3: Practice submitted, score 8/10 → SAVED & completed ✅

Database state:
- Lesson 1: status=IN_PROGRESS, last_score=2
- Lesson 2: status=IN_PROGRESS, last_score=3
- Lesson 3: status=COMPLETED, last_score=8

Displayed: Average Score: 4.3/10 ✅
Calculation: (2 + 3 + 8) / 3 = 4.33 → rounded to 4.3
```

---

## 🚨 Potential Issues & Mitigations

### Issue 1: Existing Users Have Skewed Averages
**Impact**: Users who completed many lessons will see average drop
**Mitigation**: 
- Add notification explaining change
- Show both metrics temporarily: "Average (All): 5.7/10, Average (Completed): 8.0/10"
- Gradual rollout to monitor user feedback

### Issue 2: Performance with Many Lessons
**Impact**: Calculating average from 100+ lessons might be slow
**Mitigation**:
- Current implementation already fetches all progress records
- No additional queries needed
- If needed, add database-level aggregation

### Issue 3: User Confusion About Metric Change
**Impact**: Users might not understand why their average changed
**Mitigation**:
- Update help text to explain calculation
- Add tooltip or explanation in progress view
- Include in changelog/release notes

---

## 📚 Related Documentation Files

### Files to Update
1. `/home/kutvik/Documents/vscode/promptheus/docs/user-stories.md`
2. `/home/kutvik/Documents/vscode/promptheus/docs/technical-requirements-document.md`
3. `/home/kutvik/Documents/vscode/promptheus/docs/system-architecture-document.md`
4. `/home/kutvik/Documents/vscode/promptheus/docs/database-design-document.md`
5. `/home/kutvik/Documents/vscode/promptheus/docs/ux-design-specifications.md`

### Code Files (If Changes Needed)
1. `/home/kutvik/Documents/vscode/promptheus/src/promptheus/core/progress_tracker.py`
2. `/home/kutvik/Documents/vscode/promptheus/src/promptheus/data/async_repositories.py`
3. `/home/kutvik/Documents/vscode/promptheus/tests/test_progress_tracker.py`

---

## 🎓 Learning Points

### Why This Matters
- Score calculation is a key user engagement metric
- Documentation accuracy is critical for team alignment
- Test coverage prevents regression
- Clear business rules guide implementation decisions

### Best Practices Applied
- Verify before implementing (code might be correct!)
- Update all documentation consistently
- Add comprehensive test coverage
- Consider user impact of metric changes
- Document reasoning for future reference

---

## ✅ Definition of Done

- [ ] Code verified/updated to calculate average from all attempted lessons
- [ ] All 5 documentation files updated with consistent behavior
- [ ] Unit tests added with 100% coverage of new logic
- [ ] Integration tests verify UI displays correct values
- [ ] All existing tests pass
- [ ] Manual testing completed with test scenarios
- [ ] Edge cases handled and tested
- [ ] Performance verified (no degradation)
- [ ] Code reviewed and approved
- [ ] Changes deployed to production
- [ ] Monitoring confirms correct behavior

---

**Next Steps**: Start with Phase 1 (Verification) to confirm if code changes are actually needed, or if this is purely a documentation fix.
