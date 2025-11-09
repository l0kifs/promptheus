# Fix Issues 7.1-7.2: Content Chunking and Lesson Progress Tracking

## METADATA

**Task ID:** PRMT-071-072
**Name:** Implement proper content chunking and lesson progress state transitions
**Created:** 2025-11-08
**Priority:** High
**Complexity Estimate:** 7/10
**Estimated Time:** 6-8 hours

---

## BUSINESS CONTEXT

### Problem Description
The current implementation has two critical discrepancies with the documented behavior:

1. **Content Chunking (Issue 7.1)**: Theory content is not properly split into 50-80 word chunks for mobile-optimized delivery, potentially overwhelming users with long messages.

2. **Lesson Progress Tracking (Issue 7.2)**: Progress records are created immediately as "in_progress" instead of following the documented state transition: `not_started` → `in_progress` → `completed`.

### Business Goals
- Improve user experience with properly sized content chunks
- Ensure accurate progress tracking for analytics and user motivation
- Maintain consistency between implementation and documentation
- Support mobile-first learning approach

### Target Audience
- **Primary:** End users learning prompt engineering
- **Secondary:** Developers maintaining the codebase
- **Tertiary:** Product managers analyzing user progress metrics

### Business Value
- Better user retention through improved mobile experience
- Accurate progress analytics for product decisions
- Reduced user confusion and support requests
- Foundation for future features relying on correct progress states

---

## TECHNICAL SPECIFICATION

### Functional Requirements

#### Main Functionality

**Issue 7.1: Content Chunking**
As a user, I want theory content to be delivered in 50-80 word chunks so that I can easily consume information on mobile devices without scrolling through long messages.

**Issue 7.2: Progress State Transitions**
As a system, I want lesson progress to follow the correct state flow (not_started → in_progress → completed) so that progress tracking accurately reflects user engagement.

#### Detailed Requirements

1. **Content Word-Based Chunking**
   - Description: Split theory content into messages of 50-80 words each
   - Input data: Theory text from lesson.theory_content JSON
   - Output data: List of text chunks, each 50-80 words
   - Constraints:
     - Preserve sentence boundaries when possible
     - Handle edge cases (very short/long content)
     - Maintain readability and coherence
     - Support multiple languages (word-based splitting)

2. **Progress State Management**
   - Description: Implement proper state transitions for lesson progress
   - Input data: User actions (lesson selection, start, completion)
   - Output data: Updated progress status in database
   - Constraints:
     - `not_started`: When lesson is first shown in list
     - `in_progress`: When user clicks "Start" and begins theory
     - `completed`: When user finishes practice with AI feedback
     - `completed_at` timestamp set only on completion

### Non-Functional Requirements

#### Performance
- Content chunking: <100ms for typical lesson content
- Progress updates: <50ms database write operations
- No impact on existing response times (<3s total)

#### Reliability
- Content chunking handles edge cases (empty content, very long/short text)
- Progress state transitions are atomic and consistent
- Error handling prevents invalid state transitions

#### Compatibility
- Backward compatible with existing lesson content structure
- No breaking changes to existing user sessions
- Maintains existing API contracts

---

## TECHNICAL CONTEXT

### System Architecture
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Bot Handler   │───▶│ Content Delivery │───▶│  Message        │
│                 │    │   Manager        │    │  Formatter     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                        │
┌─────────────────┐    ┌──────────────────┐             │
│ Progress        │◀──▶│ Lesson Handlers  │◀────────────┘
│   Tracker       │    │                  │
└─────────────────┘    └──────────────────┘
```

### Technology Stack
- **Backend:** Python 3.11+, SQLAlchemy (async)
- **Database:** SQLite/PostgreSQL with async repositories
- **Bot Framework:** python-telegram-bot with async handlers
- **Content:** JSON-structured lesson data

### Project Structure
```
src/promptheus/
├── bot/
│   ├── lesson_handlers.py          ← Modify: theory delivery logic
│   └── message_formatter.py        ← Modify: add chunking logic
├── core/
│   ├── progress_tracker.py         ← Modify: state transition logic
│   └── learning_flow_orchestrator.py
├── data/
│   ├── async_repositories.py       ← Modify: progress creation
│   └── models.py                   ← Already correct
└── tests/
    └── [existing test structure]
```

### Files to Modify

1. **`src/promptheus/bot/message_formatter.py`**
   - Purpose: Format messages for Telegram delivery
   - Where to make changes: Add `chunk_text_by_words()` method
   - Notes: Pure utility function, easily testable

2. **`src/promptheus/bot/lesson_handlers.py`**
   - Purpose: Handle lesson navigation and content delivery
   - Where to make changes: 
     - `lesson_start_callback()`: Update progress status to IN_PROGRESS
     - Theory display methods: Use chunked content
   - Notes: Complex async handler logic, careful testing needed

3. **`src/promptheus/core/progress_tracker.py`**
   - Purpose: Manage user progress state
   - Where to make changes: 
     - `start_lesson()`: Create progress as NOT_STARTED
     - Add `mark_in_progress()` method
   - Notes: Core business logic, affects all progress operations

4. **`src/promptheus/data/async_repositories.py`**
   - Purpose: Database operations for progress
   - Where to make changes: `create()` method to use NOT_STARTED default
   - Notes: Database layer, migration may be needed

### Related Components
- **Lesson Content Structure**: JSON with theory sections (already exists)
- **Session Management**: Context data for current position (already exists)
- **Progress Analytics**: Depends on correct status values

---

## EXAMPLES AND DOCUMENTATION

### Code Examples

#### Example 1: Current Content Delivery (Problematic)
```python
# lesson_handlers.py - current implementation
theory_content = lesson.theory_content
sections = theory_content.get("sections", [])
first_section = sections[0]

await update.callback_query.edit_message_text(
    f"💡 *Theory* (1/{total_sections})\n\n{first_section['content']}",  # May be >80 words
    ...
)
```

#### Example 2: Desired Content Chunking
```python
# message_formatter.py - new implementation
@staticmethod
def chunk_text_by_words(text: str, min_words: int = 50, max_words: int = 80) -> list[str]:
    """Split text into chunks of specified word count."""
    words = text.split()
    chunks = []
    
    for i in range(0, len(words), max_words):
        chunk = words[i:i + max_words]
        if len(chunk) >= min_words or i + len(chunk) == len(words):  # Last chunk can be shorter
            chunks.append(' '.join(chunk))
    
    return chunks
```

#### Example 3: Progress State Transitions
```python
# progress_tracker.py - new implementation
async def start_lesson(self, user_id: int, lesson_id: int) -> None:
    """Create progress record as NOT_STARTED."""
    progress = await self.progress_repo.find_by_user_and_lesson(user_id, lesson_id)
    if not progress:
        await self.progress_repo.create(user_id, lesson_id)  # Creates as NOT_STARTED
        logger.info("Lesson progress initialized", user_id=user_id, lesson_id=lesson_id)

async def mark_in_progress(self, user_id: int, lesson_id: int) -> None:
    """Mark lesson as in progress when user starts reading."""
    await self.progress_repo.update_status(user_id, lesson_id, LessonStatus.IN_PROGRESS)
    logger.info("Lesson marked as in progress", user_id=user_id, lesson_id=lesson_id)
```

### Documentation
- [TRD §3.3: Content Delivery](docs/technical-requirements-document.md)
- [DDD §3.3: UserProgress Model](docs/database-design-document.md)
- [UXD §2.1: Message Formatting](docs/ux-design-specifications.md)

### Existing Patterns
- **Repository Pattern**: Async repositories with session management
- **Dependency Injection**: Handlers receive services via constructor
- **Session Context**: JSON storage for user state
- **Error Handling**: Try-catch with user-friendly messages

### Known Pitfalls
⚠️ **Important:**
- **Word boundary preservation**: Don't split in middle of sentences if possible
- **Database migration**: Existing progress records may need status updates
- **Backward compatibility**: Don't break existing user sessions
- **Performance**: Chunking should be fast, cache results if needed
- **Edge cases**: Handle very short content (<50 words), very long content
- **Internationalization**: Word-based splitting works for most languages

---

## ACCEPTANCE CRITERIA

### Scenario Criteria (Given-When-Then)

#### Scenario 1: Content properly chunked
```gherkin
Given a lesson with theory content longer than 80 words
When user starts the lesson
Then theory is split into multiple messages
And each message contains 50-80 words
And sentence boundaries are preserved when possible
```

#### Scenario 2: Progress state transitions correctly
```gherkin
Given user selects a lesson from the list
When system creates progress record
Then progress status is "not_started"
And no completed_at timestamp is set
```

#### Scenario 3: Lesson starts and status updates
```gherkin
Given user has "not_started" progress for a lesson
When user clicks "Start" button
Then progress status changes to "in_progress"
And user can navigate through theory sections
```

#### Scenario 4: Lesson completion
```gherkin
Given user has "in_progress" progress for a lesson
When user completes the final practice exercise
Then progress status changes to "completed"
And completed_at timestamp is set to current time
```

### Rules and Constraints
- [ ] Theory content must be split at 50-80 word boundaries
- [ ] Progress status must follow: not_started → in_progress → completed
- [ ] completed_at timestamp only set on final completion
- [ ] Content chunking preserves readability and coherence
- [ ] No breaking changes to existing user experience
- [ ] All existing tests continue to pass

### Testing
- [ ] Unit tests for text chunking function (>=90% coverage)
- [ ] Integration tests for progress state transitions
- [ ] Manual testing with various lesson content lengths
- [ ] Test edge cases: very short/long content, empty sections
- [ ] Verify backward compatibility with existing progress records

### Code Review
- [ ] Code follows existing patterns and style
- [ ] Type hints added for all new functions
- [ ] Docstrings in Google format
- [ ] No hardcoded values or magic numbers
- [ ] Error handling implemented consistently

### Performance
- [ ] Content chunking <50ms for typical lesson (200-500 words)
- [ ] Progress status updates <100ms
- [ ] No degradation in overall response times
- [ ] Memory usage remains reasonable

---

## IMPLEMENTATION PLAN

### Execution Stages

#### Stage 1: Implement content chunking utility
**Description:** Create word-based text chunking functionality
**Tasks:**
- [ ] Add `chunk_text_by_words()` method to `MessageFormatter`
- [ ] Implement word counting and boundary detection
- [ ] Handle edge cases (short content, sentence preservation)
- [ ] Write comprehensive unit tests

**Validation:**
- Unit tests pass with >=90% coverage
- Manual testing with sample content shows correct chunking

#### Stage 2: Update progress creation logic
**Description:** Fix progress record creation to use NOT_STARTED status
**Tasks:**
- [ ] Modify `AsyncProgressRepository.create()` to use NOT_STARTED default
- [ ] Update `ProgressTracker.start_lesson()` to not set IN_PROGRESS
- [ ] Add `ProgressTracker.mark_in_progress()` method
- [ ] Update lesson handlers to call mark_in_progress on start

**Validation:**
- New progress records created as NOT_STARTED
- Existing tests updated if needed
- No breaking changes to existing functionality

#### Stage 3: Integrate chunking into lesson delivery
**Description:** Update lesson handlers to use chunked content
**Tasks:**
- [ ] Modify theory display methods to use chunked content
- [ ] Update session context to track chunk position instead of section
- [ ] Ensure navigation works with variable number of chunks
- [ ] Test with various content lengths

**Validation:**
- Theory content properly split into 50-80 word chunks
- Navigation works correctly through chunks
- Session state maintains correct position

#### Stage 4: Testing and validation
**Description:** Comprehensive testing of both features
**Tasks:**
- [ ] Run full test suite to ensure no regressions
- [ ] Manual testing of lesson flow with chunking
- [ ] Test progress state transitions in various scenarios
- [ ] Performance testing of chunking algorithm

**Validation:**
- All acceptance criteria met
- No performance degradation
- Backward compatibility maintained

### Action Order
1. Implement content chunking utility (isolated, testable)
2. Fix progress state creation (database layer)
3. Add progress state transition methods (business logic)
4. Integrate chunking into lesson delivery (UI layer)
5. Comprehensive testing and validation

### Dependencies
- **Database schema**: Already supports correct status enum values
- **Lesson content**: JSON structure already supports theory sections
- **Session management**: Context data can be extended for chunk tracking

---

## TESTING AND VALIDATION

### Unit Tests
```python
# tests/bot/test_message_formatter.py
def test_chunk_text_by_words_typical_content():
    """Test chunking of normal-length content."""
    text = " ".join([f"word{i}" for i in range(150)])  # 150 words
    chunks = MessageFormatter.chunk_text_by_words(text)
    
    assert len(chunks) == 2
    assert 50 <= len(chunks[0].split()) <= 80
    assert 50 <= len(chunks[1].split()) <= 80

def test_chunk_text_by_words_short_content():
    """Test chunking of short content."""
    text = "This is a short piece of content with only thirty words."
    chunks = MessageFormatter.chunk_text_by_words(text)
    
    assert len(chunks) == 1  # Should not split short content
    assert len(chunks[0].split()) <= 80

def test_chunk_text_by_words_preserves_sentences():
    """Test that chunking tries to preserve sentence boundaries."""
    text = "First sentence. Second sentence with more words to reach the limit. Third sentence."
    chunks = MessageFormatter.chunk_text_by_words(text, max_words=10)
    
    # Should split at sentence boundaries when possible
    assert "." in chunks[0]  # First chunk ends with sentence
```

### Commands to Run
```bash
# Run specific tests
pytest tests/bot/test_message_formatter.py::test_chunk_text_by_words_typical_content -v

# Run progress tracker tests
pytest tests/core/test_progress_tracker.py -v

# Run integration tests
pytest tests/integration/test_lesson_flow.py -v

# Full test suite
pytest --cov --cov-report=html

# Manual testing
python -c "
from src.promptheus.bot.message_formatter import MessageFormatter
text = 'Your long theory content here...'
chunks = MessageFormatter.chunk_text_by_words(text)
print(f'Chunks: {len(chunks)}')
for i, chunk in enumerate(chunks):
    print(f'Chunk {i+1}: {len(chunk.split())} words')
"
```

### Manual Testing Scenarios

1. **Content Chunking**
   - Create lesson with 200-word theory content
   - Start lesson and verify 2-3 message chunks
   - Check each chunk is 50-80 words
   - Verify navigation between chunks works

2. **Progress States**
   - Select lesson → Check progress created as "not_started"
   - Click "Start" → Check progress changes to "in_progress"
   - Complete lesson → Check progress changes to "completed" with timestamp

3. **Edge Cases**
   - Very short theory (<50 words) → Single chunk
   - Very long theory (500+ words) → Multiple chunks
   - Empty theory content → Graceful handling

---

## ADDITIONAL CONSIDERATIONS

### Risks
- **Risk: Breaking existing user sessions**
  - Mitigation: Maintain backward compatibility, test with existing data
  
- **Risk: Performance impact of chunking**
  - Mitigation: Implement efficient algorithm, cache if needed
  
- **Risk: Database migration for existing progress**
  - Mitigation: Update existing IN_PROGRESS records appropriately

### Assumptions
- Lesson content is already structured in reasonable sections
- Users expect sequential reading of theory content
- Progress states are primarily for analytics, not user-facing features
- Word-based chunking works for the target languages

### Limitations
- Chunking is word-based, not context-aware
- May split compound sentences or technical terms
- Fixed word ranges may not be optimal for all content types
- No support for images or rich formatting within chunks

### Future Improvements
- [ ] Context-aware chunking (semantic boundaries)
- [ ] User-configurable chunk sizes
- [ ] Rich text support within chunks
- [ ] Chunking for examples and exercises
- [ ] Progress visualization improvements

---

## COMPLETION CHECKLIST

### Development
- [ ] `chunk_text_by_words()` method implemented in MessageFormatter
- [ ] Progress creation uses NOT_STARTED status by default
- [ ] `mark_in_progress()` method added to ProgressTracker
- [ ] Lesson handlers updated to use chunked content
- [ ] Lesson start callback updates progress to IN_PROGRESS
- [ ] Session context tracks chunk position correctly

### Testing
- [ ] Unit tests for text chunking (>=90% coverage)
- [ ] Unit tests for progress state transitions
- [ ] Integration tests for lesson flow with chunking
- [ ] Manual testing of various content lengths
- [ ] Performance tests for chunking algorithm
- [ ] Backward compatibility testing

### Documentation
- [ ] Code documented with docstrings
- [ ] Implementation notes added to relevant files
- [ ] Test cases documented
- [ ] Edge cases and limitations documented

### Code Quality
- [ ] Ruff linting passes
- [ ] mypy type checking passes
- [ ] No TODO/FIXME comments left
- [ ] Code review completed
- [ ] Follows existing project patterns

### Finalization
- [ ] All acceptance criteria verified
- [ ] No regressions in existing functionality
- [ ] Performance meets requirements
- [ ] Ready for production deployment
- [ ] Task documented in project changelog

---

## CONCLUSION

This implementation will resolve the documented discrepancies between the system design and current implementation, improving both user experience (content chunking) and data accuracy (progress tracking). The changes are focused, backward-compatible, and follow existing architectural patterns.

**Success Metrics:**
- ✅ Content delivered in appropriate chunks for mobile users
- ✅ Progress states accurately reflect user engagement
- ✅ No breaking changes to existing functionality
- ✅ Performance requirements met
- ✅ All tests passing

**Next Steps:**
1. Implement content chunking utility
2. Fix progress state transitions
3. Integrate into lesson delivery
4. Comprehensive testing and validation

---

**Document Version:** 1.0.0  
**Created:** 2025-11-08  
**Author:** AI Assistant  
**Review Status:** Ready for Implementation