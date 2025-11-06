# Feature Implementation Guide: Skill Level Progression System
## Promptheus - Telegram Bot for Prompt Engineering Education

**Document Version**: 1.0  
**Feature**: Skill Level Progression System  
**Status**: Implementation Ready  
**Estimated Effort**: 4-5 days  

---

## Table of Contents
1. [Feature Overview](#1-feature-overview)
2. [Architecture & Design Decisions](#2-architecture--design-decisions)
3. [Prerequisites & Dependencies](#3-prerequisites--dependencies)
4. [Implementation Phases](#4-implementation-phases)
5. [Detailed Implementation Steps](#5-detailed-implementation-steps)
6. [Testing Strategy](#6-testing-strategy)
7. [Deployment Plan](#7-deployment-plan)
8. [Monitoring & Success Metrics](#8-monitoring--success-metrics)
9. [Rollback Plan](#9-rollback-plan)
10. [Future Enhancements](#10-future-enhancements)

---

## 1. Feature Overview

### 1.1 Problem Statement
Currently, when users complete all lessons in their skill level (Beginner/Intermediate/Advanced), they receive a congratulations message but have **no way to progress to the next level**. The system has the architecture for level management but lacks the business logic and UI flow for progression.

**Impact**: Users get "stuck" after completing all beginner lessons with no path forward, even though intermediate and advanced content exists.

### 1.2 Solution Summary
Implement a skill level progression system that:
- Enforces minimum score requirement (≥7/10) for lesson completion
- Automatically detects level completion
- Calculates eligibility based on average performance (≥7/10 average)
- Provides user choice to advance or retry
- Celebrates achievements with meaningful statistics
- Updates user's skill level in database
- Displays new level content

### 1.3 Research Foundation
This implementation follows best practices from:
- **Mastery Learning Literature**: 70-80% competency threshold before advancement (Bloom, 1968)
- **Duolingo/Khan Academy**: User choice + competency-based progression
- **Self-Determination Theory**: Autonomy, Competence, Relatedness for motivation
- **Gamification Research**: Progressive disclosure, achievement celebration

### 1.4 Key Benefits
- **User Experience**: Clear progression path, reduced confusion
- **Learning Outcomes**: Ensures mastery before advancement
- **Motivation**: Achievement celebration, autonomy in decisions
- **Retention**: Meaningful milestones increase engagement
- **Scalability**: No database schema changes required

---

## 2. Architecture & Design Decisions

### 2.1 Layered Architecture Integration

```
┌─────────────────────────────────────────────────────────────┐
│                    Bot Interface Layer                      │
│  • lesson_handlers.py (level completion callbacks)          │
│  • practice_handlers.py (score validation)                  │
│  • progress_handlers.py (multi-level display)               │
│  • message_formatter.py (new message templates)             │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│                   Application Core Layer                    │
│  • ProgressTracker (eligibility check, level stats)         │
│  • LearningFlowOrchestrator (completion detection)          │
└─────────────┬──────────────────────────────┬────────────────┘
              │                              │
    ┌─────────▼──────────┐         ┌─────────▼──────────┐
    │   AI Integration   │         │   Data Access      │
    │  (score eval)      │         │  • User Repository │
    │                    │         │  • Progress Repo   │
    └────────────────────┘         └────────────────────┘
```

### 2.2 Key Design Decisions

| Decision | Rationale | Alternative Considered |
|----------|-----------|------------------------|
| **7/10 Minimum Score** | Aligns with 70% mastery learning standard | 6/10 (too lenient), 8/10 (too strict) |
| **User Choice on Advancement** | Supports autonomy (Self-Determination Theory) | Automatic advancement (less engaging) |
| **No Schema Changes** | Leverages existing `User.skill_level` field | Add separate progression table (over-engineering) |
| **Average Score Calculation** | Simple, transparent metric | Weighted average (too complex for MVP) |
| **Hybrid Flow (Auto-qualify + Manual Advance)** | Best of both worlds | Pure manual or pure automatic |

### 2.3 Component Dependencies

**New Methods Required**:
```python
# ProgressTracker (core/progress_tracker.py)
async def check_level_eligibility(user_id: int, current_level: SkillLevel) -> dict

# MessageFormatter (bot/message_formatter.py)
def format_level_complete(level: SkillLevel, eligible: bool, stats: dict) -> str
def format_score_insufficient(score: int, improvements: list[str]) -> str

# LessonHandlers (bot/lesson_handlers.py)
async def handle_level_completion(...)
async def advance_to_next_level_callback(...)
```

**Existing Methods Used** (No Changes Needed):
```python
# AsyncUserRepository (already exists!)
async def update_skill_level(telegram_id: int, skill_level: SkillLevel)
async def update_current_lesson(telegram_id: int, lesson_id: int | None)

# AsyncLessonRepository
async def find_by_skill_level(skill_level: SkillLevel)
async def find_next_lesson(current_level: SkillLevel, order_index: int)
```

---

## 3. Prerequisites & Dependencies

### 3.1 System Requirements
- ✅ Python 3.11+
- ✅ SQLAlchemy async repositories in place
- ✅ Dependency injection container configured
- ✅ Telegram bot handlers using constructor injection
- ✅ User, Lesson, UserProgress models defined
- ✅ SkillLevel enum with BEGINNER, INTERMEDIATE, ADVANCED

### 3.2 External Dependencies
- ✅ OpenRouter API for score evaluation
- ✅ Telegram Bot API for message delivery
- ✅ Existing lesson content in all 3 levels (from promptheus-content repo)

### 3.3 Development Environment
```bash
# Ensure all dependencies are installed
uv pip install -e ".[dev]"

# Run tests to verify baseline
pytest

# Check database is up to date
alembic upgrade head
```

---

## 4. Implementation Phases

### Phase 1: Minimum Score Enforcement (Day 1)
**Goal**: Prevent lesson completion with score < 7/10

**Scope**:
- Update `practice_handlers.py` score validation
- Add "retry required" message formatting
- Modify button display logic
- Unit tests

**Success Criteria**:
- Users with score < 7 cannot mark lesson complete
- Clear message explains 7/10 threshold
- "Try Again" button offered with hints

---

### Phase 2: Level Eligibility Check (Day 1-2)
**Goal**: Calculate and check average score for level

**Scope**:
- Add `check_level_eligibility()` to ProgressTracker
- Calculate average across completed lessons
- Return structured eligibility data
- Unit tests for edge cases

**Success Criteria**:
- Accurate average calculation
- Handles missing scores gracefully
- Correctly identifies qualified vs. unqualified users

---

### Phase 3: Level Completion Detection & Flow (Day 2-3)
**Goal**: Detect last lesson completion and route to appropriate flow

**Scope**:
- Modify `lesson_complete_callback()` in lesson_handlers
- Add `handle_level_completion()` method
- Implement qualified vs. retry message flows
- Integration tests

**Success Criteria**:
- System detects last lesson in level
- Qualified users see advancement option
- Unqualified users see retry encouragement
- Advanced level completion shows final message

---

### Phase 4: Advancement Logic (Day 3)
**Goal**: Update skill level and display new content

**Scope**:
- Create `advance_to_next_level_callback()`
- Update user's skill_level in database
- Clear current_lesson_id
- Show new level lesson list
- Register callback in main.py
- E2E tests

**Success Criteria**:
- Skill level updates correctly
- New lessons displayed
- User can resume with new level
- Database changes persist

---

### Phase 5: Message Formatting & UX Polish (Day 4)
**Goal**: Engaging, motivating user messages

**Scope**:
- Add formatted messages to MessageFormatter
- Include celebration elements (emojis, stats)
- Mobile-optimized layouts
- Visual hierarchy

**Success Criteria**:
- Messages fit mobile screens
- Stats are accurate and meaningful
- Tone is encouraging and celebratory

---

### Phase 6: Multi-Level Progress Display (Day 4)
**Goal**: Show progress across all levels

**Scope**:
- Update `progress_callback()` in progress_handlers
- Group progress by skill level
- Display current level indicator
- Show stats per level

**Success Criteria**:
- All levels visible in progress view
- Current level clearly marked
- Per-level and overall stats accurate

---

### Phase 7: Testing & Bug Fixes (Day 5)
**Goal**: Comprehensive test coverage

**Scope**:
- Unit tests (>80% coverage)
- Integration tests for all flows
- E2E test for complete progression path
- Edge case testing

**Success Criteria**:
- All tests pass
- Coverage >80%
- No regressions in existing features

---

## 5. Detailed Implementation Steps

### Step 1: Minimum Score Enforcement

#### File: `src/promptheus/bot/practice_handlers.py`

**Location**: Update the method that handles practice exercise evaluation (after AI returns score)

```python
async def handle_practice_evaluation(self, update: Update, context: ContextTypes.DEFAULT_TYPE, score: int, feedback: dict) -> None:
    """Handle practice evaluation with minimum score enforcement."""
    
    user_id = update.effective_user.id
    lesson_id = context.user_data.get('current_lesson_id')
    
    # Record the attempt
    await self.progress_tracker.record_attempt(user_id, lesson_id, score)
    
    # Check if score meets threshold
    if score >= 7:
        # Score is sufficient for completion
        message = self.message_formatter.format_score_sufficient(score, feedback)
        keyboard = [
            [InlineKeyboardButton("✅ Lesson Complete", callback_data=f"lesson_complete_{lesson_id}")],
            [InlineKeyboardButton("🔄 Try for 10/10", callback_data=f"practice_retry_{lesson_id}")],
            [InlineKeyboardButton("📋 All Lessons", callback_data="lesson_list")]
        ]
    else:
        # Score below threshold - retry required
        message = self.message_formatter.format_score_insufficient(score, feedback.get('improvements', []))
        keyboard = [
            [InlineKeyboardButton("🔄 Try Again", callback_data=f"practice_retry_{lesson_id}")],
            [InlineKeyboardButton("💡 Show Hint", callback_data=f"practice_hint_{lesson_id}")],
            [InlineKeyboardButton("📖 Review Theory", callback_data=f"lesson_theory_{lesson_id}")]
        ]
    
    await update.message.reply_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
```

#### File: `src/promptheus/bot/message_formatter.py`

**Add new methods**:

```python
@staticmethod
def format_score_insufficient(score: int, improvements: list[str]) -> str:
    """Format message when score is below 7/10 threshold."""
    message = f"📝 *Score: {score}/10*\n\n"
    message += "Good effort! To master this lesson, aim for at least 7/10.\n\n"
    
    if improvements:
        message += "💡 *What to improve:*\n"
        for improvement in improvements[:3]:  # Max 3 items for mobile
            message += f"• {improvement}\n"
    
    message += "\n⚠️ Complete this lesson with 7/10+ to continue your progress."
    
    return message

@staticmethod
def format_score_sufficient(score: int, feedback: dict) -> str:
    """Format message when score meets or exceeds threshold."""
    message = f"✅ *Score: {score}/10*\n\n"
    
    if score == 10:
        message += "🎉 *Perfect!* You've mastered this lesson!\n\n"
    else:
        message += "Great work! You've reached the completion threshold.\n\n"
    
    # Show what was good
    if 'strengths' in feedback:
        message += "💪 *Your strengths:*\n"
        for strength in feedback['strengths'][:2]:
            message += f"• {strength}\n"
        message += "\n"
    
    # Optional improvements for higher score
    if score < 10 and 'improvements' in feedback:
        message += "💡 *Could improve:*\n"
        for improvement in feedback['improvements'][:2]:
            message += f"• {improvement}\n"
    
    return message
```

#### Tests: `tests/test_practice_handlers.py`

```python
@pytest.mark.asyncio
async def test_practice_evaluation_below_threshold():
    """Test practice evaluation with score below 7/10."""
    # Setup: User submits prompt, AI returns score of 5
    # Assert: "Try Again" button shown, no "Complete" button
    # Assert: Message explains 7/10 threshold
    pass

@pytest.mark.asyncio
async def test_practice_evaluation_meets_threshold():
    """Test practice evaluation with score 7-9/10."""
    # Setup: User submits prompt, AI returns score of 8
    # Assert: Both "Complete" and "Try Again" buttons shown
    # Assert: Encouraging message displayed
    pass

@pytest.mark.asyncio
async def test_practice_evaluation_perfect_score():
    """Test practice evaluation with score 10/10."""
    # Setup: User submits prompt, AI returns score of 10
    # Assert: "Complete" button prominent
    # Assert: Celebration message displayed
    pass
```

---

### Step 2: Level Eligibility Check

#### File: `src/promptheus/core/progress_tracker.py`

**Add new method**:

```python
async def check_level_eligibility(self, user_id: int, current_level: SkillLevel) -> dict:
    """
    Check if user is eligible to advance to next level.
    
    Args:
        user_id: User's telegram ID
        current_level: Current skill level to evaluate
        
    Returns:
        Dictionary with eligibility data:
        {
            'eligible': bool,
            'average_score': float,
            'completed': int,
            'total': int,
            'min_threshold': float,
            'lessons_below_threshold': list[dict]  # For targeted retry suggestions
        }
    """
    logger.info("Checking level eligibility", user_id=user_id, level=current_level.value)
    
    # Get all progress for user
    progress_records = await self.progress_repo.find_by_user(user_id)
    
    # Filter for current level completed lessons
    from promptheus.data.models import LessonStatus
    
    current_level_progress = []
    for progress in progress_records:
        # Need to fetch lesson to check skill level
        lesson = progress.lesson  # Assuming relationship is loaded
        if lesson and lesson.skill_level == current_level and progress.status == LessonStatus.COMPLETED:
            current_level_progress.append(progress)
    
    # Calculate average score
    scores = [p.last_score for p in current_level_progress if p.last_score is not None]
    avg_score = sum(scores) / len(scores) if scores else 0.0
    
    # Find lessons below threshold for retry suggestions
    lessons_below_threshold = []
    for progress in current_level_progress:
        if progress.last_score and progress.last_score < 7:
            lesson = progress.lesson
            lessons_below_threshold.append({
                'lesson_id': lesson.id,
                'title': lesson.title,
                'score': progress.last_score
            })
    
    # Sort by score (lowest first) for prioritized retry
    lessons_below_threshold.sort(key=lambda x: x['score'])
    
    result = {
        'eligible': avg_score >= 7.0,
        'average_score': round(avg_score, 1),
        'completed': len(current_level_progress),
        'total': len(current_level_progress),
        'min_threshold': 7.0,
        'lessons_below_threshold': lessons_below_threshold[:3]  # Max 3 for display
    }
    
    logger.info(
        "Level eligibility checked",
        user_id=user_id,
        level=current_level.value,
        eligible=result['eligible'],
        avg_score=result['average_score']
    )
    
    return result
```

#### Tests: `tests/test_progress_tracker.py`

```python
@pytest.mark.asyncio
async def test_check_level_eligibility_qualified():
    """Test user with avg ≥7/10 is eligible for advancement."""
    # Setup: User with 5 completed lessons, scores [8, 9, 7, 8, 9] (avg 8.2)
    # Assert: eligible=True, average_score=8.2
    # Assert: lessons_below_threshold is empty
    pass

@pytest.mark.asyncio
async def test_check_level_eligibility_not_qualified():
    """Test user with avg <7/10 is not eligible."""
    # Setup: User with 5 completed lessons, scores [6, 5, 7, 8, 6] (avg 6.4)
    # Assert: eligible=False, average_score=6.4
    # Assert: lessons_below_threshold contains lessons with scores 5, 6, 6
    pass

@pytest.mark.asyncio
async def test_check_level_eligibility_exact_threshold():
    """Test user with exactly 7.0 average."""
    # Setup: User with scores that average to exactly 7.0
    # Assert: eligible=True (≥ not just >)
    pass

@pytest.mark.asyncio
async def test_check_level_eligibility_no_completed_lessons():
    """Test user with no completed lessons."""
    # Setup: User with no completed lessons in level
    # Assert: eligible=False, average_score=0.0
    pass
```

---

### Step 3: Level Completion Detection

#### File: `src/promptheus/bot/lesson_handlers.py`

**Update existing callback**:

```python
async def lesson_complete_callback(
    self, 
    update: Update, 
    context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle lesson completion with level progression detection."""
    
    if not update.effective_user or not update.callback_query:
        return
    
    await update.callback_query.answer()
    
    user_id = update.effective_user.id
    lesson_id = int(update.callback_query.data.split("_")[-1])
    
    # Get current lesson details
    lesson = await self.learning_orchestrator.lesson_repo.find_by_id(lesson_id)
    if not lesson:
        await update.callback_query.edit_message_text("❌ Lesson not found.")
        return
    
    # Mark lesson as completed (score should already be recorded)
    progress = await self.learning_orchestrator.progress_tracker.progress_repo.find_by_user_and_lesson(
        user_id, lesson_id
    )
    if progress and progress.last_score and progress.last_score >= 7:
        await self.learning_orchestrator.progress_tracker.mark_completed(
            user_id, lesson_id, progress.last_score
        )
    else:
        await update.callback_query.edit_message_text(
            "⚠️ Cannot complete lesson: minimum score of 7/10 required."
        )
        return
    
    # Check if this was the last lesson in the level
    next_lesson = await self.learning_orchestrator.lesson_repo.find_next_lesson(
        lesson.skill_level,
        lesson.order_index
    )
    
    if next_lesson is None:
        # No more lessons in this level = level complete!
        await self.handle_level_completion(
            update, 
            context, 
            user_id, 
            lesson.skill_level
        )
    else:
        # Show normal "next lesson" flow
        await self.show_lesson_complete_normal(update, lesson, next_lesson)
```

**Add new method**:

```python
async def handle_level_completion(
    self, 
    update: Update, 
    context: ContextTypes.DEFAULT_TYPE,
    user_id: int,
    completed_level: SkillLevel
) -> None:
    """Handle level completion with eligibility check and user choice."""
    
    logger.info("Handling level completion", user_id=user_id, level=completed_level.value)
    
    # Check eligibility for next level
    eligibility = await self.learning_orchestrator.progress_tracker.check_level_eligibility(
        user_id, 
        completed_level
    )
    
    # Determine next level
    next_level = self._get_next_skill_level(completed_level)
    
    if next_level is None:
        # Completed Advanced (final level)
        await self.show_final_level_completion(update, eligibility, completed_level)
        return
    
    if eligibility['eligible']:
        # Qualified to advance
        await self.show_qualified_advancement(
            update, 
            completed_level, 
            next_level, 
            eligibility
        )
    else:
        # Need to retry for better scores
        await self.show_retry_required(
            update, 
            completed_level, 
            next_level,
            eligibility
        )

def _get_next_skill_level(self, current: SkillLevel) -> SkillLevel | None:
    """Get next skill level or None if at max."""
    level_order = {
        SkillLevel.BEGINNER: SkillLevel.INTERMEDIATE,
        SkillLevel.INTERMEDIATE: SkillLevel.ADVANCED,
        SkillLevel.ADVANCED: None
    }
    return level_order.get(current)
```

---

### Step 4: Advancement Flows

#### File: `src/promptheus/bot/lesson_handlers.py`

**Add flow methods**:

```python
async def show_qualified_advancement(
    self,
    update: Update,
    current_level: SkillLevel,
    next_level: SkillLevel,
    stats: dict
) -> None:
    """Show advancement option for qualified users."""
    
    message = self.message_formatter.format_level_complete(
        level=current_level,
        eligible=True,
        stats=stats,
        next_level=next_level
    )
    
    keyboard = [
        [InlineKeyboardButton(
            f"🚀 Advance to {next_level.value.title()}", 
            callback_data=f"advance_to_{next_level.value}"
        )],
        [InlineKeyboardButton(
            "🔄 Retry for Perfection", 
            callback_data=f"retry_level_{current_level.value}"
        )],
        [InlineKeyboardButton("📊 View Progress", callback_data="progress")],
    ]
    
    await update.callback_query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def show_retry_required(
    self,
    update: Update,
    current_level: SkillLevel,
    next_level: SkillLevel,
    stats: dict
) -> None:
    """Show retry encouragement for users below threshold."""
    
    message = self.message_formatter.format_level_complete(
        level=current_level,
        eligible=False,
        stats=stats,
        next_level=next_level
    )
    
    keyboard = [
        [InlineKeyboardButton(
            "🔄 Retry Lessons", 
            callback_data=f"retry_level_{current_level.value}"
        )],
        [InlineKeyboardButton("📊 View Progress", callback_data="progress")],
        [InlineKeyboardButton("📚 Main Menu", callback_data="menu")],
    ]
    
    await update.callback_query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def show_final_level_completion(
    self,
    update: Update,
    stats: dict,
    final_level: SkillLevel
) -> None:
    """Show final completion message for Advanced level."""
    
    message = "🏆 *Congratulations, Prompt Master!*\n\n"
    message += "You've completed ALL levels!\n\n"
    message += f"📊 *Final Performance:*\n"
    message += f"• Average Score: {stats['average_score']}/10\n"
    message += f"• Total Lessons: {stats['completed']}/{stats['total']} ✅\n\n"
    message += "🎓 You're now a Prompt Engineering Expert!\n\n"
    message += "*What's next?*\n"
    message += "• Review any lesson to stay sharp\n"
    message += "• Help others learn prompt engineering\n"
    message += "• Apply these skills to real projects"
    
    keyboard = [
        [InlineKeyboardButton("📋 Review All Lessons", callback_data="lesson_list")],
        [InlineKeyboardButton("📊 Final Statistics", callback_data="progress")],
    ]
    
    await update.callback_query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
```

#### File: `src/promptheus/bot/message_formatter.py`

**Add level completion formatter**:

```python
@staticmethod
def format_level_complete(
    level: SkillLevel,
    eligible: bool,
    stats: dict,
    next_level: SkillLevel | None = None
) -> str:
    """Format level completion message based on eligibility."""
    
    level_emoji = {
        SkillLevel.BEGINNER: "🌱",
        SkillLevel.INTERMEDIATE: "📈",
        SkillLevel.ADVANCED: "🚀"
    }
    
    level_name = level.value.title()
    emoji = level_emoji.get(level, "📘")
    
    if not eligible:
        # Below threshold - retry required
        message = f"{emoji} *{level_name} Level Complete!*\n\n"
        message += f"📊 *Your Performance:*\n"
        message += f"• Completed: {stats['completed']}/{stats['total']} lessons ✅\n"
        message += f"• Average Score: {stats['average_score']}/10\n\n"
        message += f"⚠️ *Almost There!*\n\n"
        
        if next_level:
            message += f"To unlock {next_level.value.title()} level, "
            message += f"aim for an average of {stats['min_threshold']}/10 or higher.\n\n"
        
        if stats.get('lessons_below_threshold'):
            message += f"💡 *Focus on improving:*\n"
            for lesson in stats['lessons_below_threshold']:
                message += f"• {lesson['title']}: {lesson['score']}/10\n"
        
        return message
    
    if next_level is None:
        # Final level complete - already handled separately
        return ""
    
    # Qualified to advance
    message = f"🎉 *{level_name} Level Complete!*\n\n"
    message += f"📊 *Your Performance:*\n"
    message += f"• Completed: {stats['completed']}/{stats['total']} lessons ✅\n"
    message += f"• Average Score: {stats['average_score']}/10\n\n"
    message += f"🏆 *Achievement Unlocked:*\n"
    message += f'"{level_name} Prompt Engineering Master"\n\n'
    message += f"You're ready for {next_level.value.title()} level!"
    
    return message
```

---

### Step 5: Advancement Callback

#### File: `src/promptheus/bot/lesson_handlers.py`

**Add callback method**:

```python
async def advance_to_next_level_callback(
    self, 
    update: Update, 
    context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle user choosing to advance to next level."""
    
    if not update.effective_user or not update.callback_query:
        return
    
    await update.callback_query.answer("🚀 Advancing to next level...")
    
    user_id = update.effective_user.id
    next_level_str = update.callback_query.data.split("_")[-1]  # e.g., "intermediate"
    next_level = SkillLevel(next_level_str)
    
    logger.info("User advancing to next level", user_id=user_id, next_level=next_level.value)
    
    # Update user's skill level
    await self.learning_orchestrator.user_repo.update_skill_level(
        user_id, 
        next_level
    )
    
    # Clear current lesson (fresh start in new level)
    await self.learning_orchestrator.user_repo.update_current_lesson(
        user_id, 
        None
    )
    
    # Get lessons for new level
    lessons = await self.learning_orchestrator.lesson_repo.find_by_skill_level(next_level)
    
    if not lessons:
        await update.callback_query.edit_message_text(
            "⚠️ New level content coming soon! Check back later.\n\n"
            "Your progress has been saved."
        )
        return
    
    # Show new level intro
    level_emoji = {
        SkillLevel.BEGINNER: "🌱",
        SkillLevel.INTERMEDIATE: "📈",
        SkillLevel.ADVANCED: "🚀"
    }
    
    message = f"{level_emoji[next_level]} *{next_level.value.title()} Level Unlocked!*\n\n"
    message += f"Welcome to the next stage of your learning journey.\n\n"
    message += f"📚 *Available Lessons ({len(lessons)}):*\n\n"
    
    for i, lesson in enumerate(lessons[:5], 1):
        message += f"{i}. {lesson.title}\n"
    
    if len(lessons) > 5:
        message += f"\n... and {len(lessons) - 5} more lessons"
    
    keyboard = [
        [InlineKeyboardButton(
            f"▶️ Start Lesson 1", 
            callback_data=f"lesson_{lessons[0].id}"
        )],
        [InlineKeyboardButton("📋 View All Lessons", callback_data="lesson_list")],
        [InlineKeyboardButton("📊 My Progress", callback_data="progress")],
    ]
    
    await update.callback_query.edit_message_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    
    logger.info("Level advancement complete", user_id=user_id, new_level=next_level.value)
```

#### File: `src/promptheus/main.py`

**Register new callback**:

```python
# In the application setup section, add:
application.add_handler(
    CallbackQueryHandler(
        handlers.advance_to_next_level_callback, 
        pattern="^advance_to_"
    )
)
```

---

### Step 6: Multi-Level Progress Display

#### File: `src/promptheus/bot/progress_handlers.py`

**Update progress callback**:

```python
async def progress_callback(
    self, 
    update: Update, 
    context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Enhanced progress view with multi-level support."""
    
    if not update.effective_user or not update.callback_query:
        return
    
    await update.callback_query.answer()
    
    user_id = update.effective_user.id
    user = await self.learning_orchestrator.user_repo.find_by_telegram_id(user_id)
    
    if not user:
        await update.callback_query.edit_message_text("❌ User not found.")
        return
    
    # Get all progress records
    progress_records = await self.learning_orchestrator.progress_tracker.progress_repo.find_by_user(user_id)
    
    # Group by skill level
    from collections import defaultdict
    levels_progress = defaultdict(list)
    
    for progress in progress_records:
        lesson = progress.lesson
        if lesson:
            levels_progress[lesson.skill_level].append(progress)
    
    # Build message
    level_emoji = {
        SkillLevel.BEGINNER: "🌱",
        SkillLevel.INTERMEDIATE: "📈",
        SkillLevel.ADVANCED: "🚀"
    }
    
    progress_text = "📊 *Your Learning Journey*\n\n"
    progress_text += f"Current Level: {level_emoji[user.skill_level]} *{user.skill_level.value.title()}*\n\n"
    
    # Show stats for each level
    for level in [SkillLevel.BEGINNER, SkillLevel.INTERMEDIATE, SkillLevel.ADVANCED]:
        progress_list = levels_progress.get(level, [])
        
        if not progress_list and level != user.skill_level:
            # Skip levels with no progress unless it's current level
            continue
        
        from promptheus.data.models import LessonStatus
        completed = sum(1 for p in progress_list if p.status == LessonStatus.COMPLETED)
        total = len(progress_list) if progress_list else 5  # Default to 5 lessons per level
        scores = [p.last_score for p in progress_list if p.last_score is not None]
        avg_score = sum(scores) / len(scores) if scores else 0.0
        
        # Status indicator
        if level == user.skill_level:
            status = "⏳ In Progress"
        elif completed == total and total > 0:
            status = "✅ Complete"
        elif completed > 0:
            status = f"⏳ {completed}/{total}"
        else:
            status = "🔒 Locked"
        
        progress_text += f"{level_emoji[level]} *{level.value.title()}* {status}\n"
        
        if progress_list:
            progress_text += f"   Lessons: {completed}/{total} | Avg: {avg_score:.1f}/10\n"
        
        progress_text += "\n"
    
    # Overall statistics
    all_completed = sum(
        1 for p in progress_records 
        if p.status == LessonStatus.COMPLETED
    )
    all_scores = [p.last_score for p in progress_records if p.last_score is not None]
    overall_avg = sum(all_scores) / len(all_scores) if all_scores else 0.0
    
    progress_text += f"*Overall Progress:*\n"
    progress_text += f"• Total Completed: {all_completed}/15 lessons\n"
    progress_text += f"• Overall Average: {overall_avg:.1f}/10\n"
    
    # Buttons
    keyboard = [
        [InlineKeyboardButton("▶️ Continue Learning", callback_data="lesson_continue")],
        [InlineKeyboardButton("📋 All Lessons", callback_data="lesson_list")],
        [InlineKeyboardButton("📚 Main Menu", callback_data="menu")],
    ]
    
    await update.callback_query.edit_message_text(
        progress_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
```

---

## 6. Testing Strategy

### 6.1 Unit Tests

#### Test Coverage Target: >80%

**File**: `tests/test_progress_tracker.py`
```python
class TestLevelEligibility:
    @pytest.mark.asyncio
    async def test_eligible_with_high_scores(self):
        """User with all scores ≥7 should be eligible."""
        # Setup: scores [8, 9, 7, 8, 9]
        # Assert: eligible=True, avg=8.2
    
    @pytest.mark.asyncio
    async def test_not_eligible_with_low_average(self):
        """User with average <7 should not be eligible."""
        # Setup: scores [6, 5, 7, 8, 6]
        # Assert: eligible=False, avg=6.4
    
    @pytest.mark.asyncio
    async def test_eligible_at_exact_threshold(self):
        """User with exactly 7.0 average should be eligible."""
        # Setup: scores that average to 7.0
        # Assert: eligible=True
    
    @pytest.mark.asyncio
    async def test_identifies_low_scoring_lessons(self):
        """Should identify lessons below threshold for retry."""
        # Setup: mixed scores including some below 7
        # Assert: lessons_below_threshold contains correct lessons
```

**File**: `tests/test_lesson_handlers.py`
```python
class TestLevelCompletion:
    @pytest.mark.asyncio
    async def test_detects_last_lesson_completion(self):
        """Should detect when completing last lesson in level."""
        # Setup: User completes 5th lesson in beginner
        # Assert: handle_level_completion called
    
    @pytest.mark.asyncio
    async def test_qualified_shows_advance_option(self):
        """Qualified user should see advance button."""
        # Setup: User avg=8.2, completes last lesson
        # Assert: "Advance to Intermediate" button present
    
    @pytest.mark.asyncio
    async def test_not_qualified_shows_retry(self):
        """Unqualified user should see retry encouragement."""
        # Setup: User avg=6.3, completes last lesson
        # Assert: "Retry Lessons" button, no "Advance" button
    
    @pytest.mark.asyncio
    async def test_final_level_shows_completion(self):
        """Advanced level completion shows final message."""
        # Setup: User completes last advanced lesson
        # Assert: "Prompt Master" message, no advance option
```

**File**: `tests/test_practice_handlers.py`
```python
class TestScoreEnforcement:
    @pytest.mark.asyncio
    async def test_score_below_seven_prevents_completion(self):
        """Score <7 should prevent lesson completion."""
        # Setup: AI returns score of 5
        # Assert: No "Complete" button, only "Try Again"
    
    @pytest.mark.asyncio
    async def test_score_seven_allows_completion(self):
        """Score ≥7 should allow completion."""
        # Setup: AI returns score of 7
        # Assert: "Complete" button present
    
    @pytest.mark.asyncio
    async def test_perfect_score_shows_celebration(self):
        """Perfect score should have celebration message."""
        # Setup: AI returns score of 10
        # Assert: Celebration emoji and text present
```

### 6.2 Integration Tests

**File**: `tests/integration/test_level_progression_flow.py`

```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_complete_level_and_advance():
    """Test full flow: complete level → check eligibility → advance."""
    # 1. User completes 5 beginner lessons with scores [8,9,7,8,9]
    # 2. On 5th completion, level complete message shown
    # 3. Eligibility check returns qualified
    # 4. User clicks "Advance to Intermediate"
    # 5. Skill level updated in database
    # 6. Intermediate lessons displayed
    pass

@pytest.mark.integration
@pytest.mark.asyncio
async def test_complete_level_but_need_retry():
    """Test flow when user needs to retry for better scores."""
    # 1. User completes 5 beginner lessons with scores [6,5,7,8,6]
    # 2. Level complete message shows retry required
    # 3. No "Advance" button shown
    # 4. Lessons below 7 listed for retry
    pass

@pytest.mark.integration
@pytest.mark.asyncio
async def test_final_level_completion():
    """Test completion of Advanced (final) level."""
    # 1. User completes all advanced lessons
    # 2. Final completion message shown
    # 3. No "Advance" option (no higher level)
    # 4. "Prompt Master" celebration displayed
    pass
```

### 6.3 End-to-End Tests

**File**: `tests/e2e/test_full_progression_journey.py`

```python
@pytest.mark.e2e
@pytest.mark.asyncio
async def test_beginner_to_intermediate_journey():
    """
    E2E test: New user → assessment → complete beginner → 
    advance to intermediate.
    """
    # 1. New user starts bot
    # 2. Completes assessment → assigned beginner
    # 3. Completes all 5 beginner lessons with good scores
    # 4. Level completion detected
    # 5. Advances to intermediate
    # 6. Intermediate lessons shown
    # 7. Verify database state correct
    pass

@pytest.mark.e2e
@pytest.mark.asyncio
async def test_retry_then_advance():
    """
    E2E test: User completes level with low scores, retries, 
    then advances.
    """
    # 1. User completes beginner with avg=6.3
    # 2. Retry required message shown
    # 3. User retries 2 lessons, improves scores
    # 4. Now avg=7.4
    # 5. Completes last lesson again
    # 6. Now qualified to advance
    # 7. Advances successfully
    pass
```

### 6.4 Test Fixtures

**File**: `tests/conftest.py`

```python
@pytest.fixture
async def user_with_completed_beginner(db_session):
    """User who completed all beginner lessons with good scores."""
    user = User(
        telegram_id=12345,
        username="testuser",
        skill_level=SkillLevel.BEGINNER,
        learning_goal=LearningGoal.PROFESSIONAL
    )
    db_session.add(user)
    
    # Add completed lessons with scores
    for i in range(1, 6):
        lesson = Lesson(
            id=i,
            title=f"Lesson {i}",
            skill_level=SkillLevel.BEGINNER,
            order_index=i,
            tags=["test"],
            theory_content={},
            examples={},
            exercises={}
        )
        db_session.add(lesson)
        
        progress = UserProgress(
            user_id=user.telegram_id,
            lesson_id=lesson.id,
            status=LessonStatus.COMPLETED,
            last_score=7 + i,  # Scores: 8, 9, 10, 11, 12 (capped at 10)
            attempts=1
        )
        db_session.add(progress)
    
    await db_session.commit()
    return user

@pytest.fixture
async def user_needs_retry(db_session):
    """User who completed beginner but needs retry (avg <7)."""
    # Similar to above but with lower scores
    pass
```

---

## 7. Deployment Plan

### 7.1 Pre-Deployment Checklist

- [ ] All unit tests pass (>80% coverage)
- [ ] All integration tests pass
- [ ] E2E test for main flow passes
- [ ] Code review completed
- [ ] Documentation updated
- [ ] No database migrations required (verified)
- [ ] Backward compatibility maintained
- [ ] Logging added for key operations

### 7.2 Deployment Steps

#### Step 1: Code Deployment
```bash
# 1. Merge feature branch to develop
git checkout develop
git merge feature/skill-level-progression

# 2. Run final tests
pytest

# 3. Ensure no migrations needed
alembic current
alembic check  # Verify no pending migrations

# 4. Deploy to staging
# (Follow existing deployment process)
```

#### Step 2: Smoke Testing
```bash
# 1. Test bot starts correctly
uv run python -m promptheus.main

# 2. Test basic flows work
# - /start command
# - Complete a lesson
# - View progress

# 3. Test new feature
# - Complete all lessons in a level
# - Verify level completion message
# - Test advancement flow
```

#### Step 3: Monitoring
```bash
# Watch logs for errors
tail -f logs/promptheus.log | grep ERROR

# Monitor key metrics
# - Level completion rate
# - Advancement success rate
# - Error rates in new handlers
```

### 7.3 Rollback Plan

**If issues detected**:

1. **Immediate**: Disable new handlers via feature flag (if implemented)
2. **Quick Fix**: Deploy hotfix branch with issue resolved
3. **Full Rollback**: Revert commit and redeploy previous version

```bash
# Rollback procedure
git revert <commit-hash>
git push origin develop

# Redeploy previous version
# No database rollback needed (no schema changes)
```

### 7.4 Post-Deployment Validation

**Verify in Production**:
- [ ] Users can complete lessons with score ≥7
- [ ] Level completion messages display correctly
- [ ] Advancement updates skill_level correctly
- [ ] Multi-level progress view works
- [ ] No errors in logs related to new feature
- [ ] Performance metrics within acceptable range

---

## 8. Monitoring & Success Metrics

### 8.1 Application Metrics

**Track in Analytics**:
```python
# Log events for analysis
logger.info("level_completed", 
    user_id=user_id, 
    level=level, 
    avg_score=avg_score,
    qualified=eligible
)

logger.info("level_advanced", 
    user_id=user_id, 
    from_level=old_level, 
    to_level=new_level
)

logger.info("retry_encouraged",
    user_id=user_id,
    level=level,
    avg_score=avg_score,
    target_score=7.0
)
```

**Metrics to Monitor**:
- Level completion rate per level
- Advancement rate (qualified users who advance)
- Retry rate (users who retry vs. advance)
- Average score per level
- Time to complete each level
- Dropout rate after level completion message

### 8.2 Success Criteria

**Week 1 Targets**:
- [ ] ≥20 users complete a full level
- [ ] ≥60% of qualified users choose to advance
- [ ] ≥30% of unqualified users retry lessons
- [ ] 0 critical errors in progression flow
- [ ] Average score improves by 1+ point after retry

**Month 1 Targets**:
- [ ] ≥100 users complete beginner level
- [ ] ≥40% advance to intermediate
- [ ] ≥25% advance to advanced
- [ ] Average scores: Beginner 7.5+, Intermediate 7.8+, Advanced 8.0+
- [ ] User satisfaction rating >4/5 for progression feature

### 8.3 Dashboard Queries

```sql
-- Level completion funnel
SELECT 
    skill_level,
    COUNT(DISTINCT user_id) as users_started,
    COUNT(DISTINCT CASE 
        WHEN completed_count = 5 THEN user_id 
    END) as users_completed,
    COUNT(DISTINCT CASE 
        WHEN avg_score >= 7.0 THEN user_id 
    END) as users_qualified
FROM (
    SELECT 
        u.telegram_id as user_id,
        l.skill_level,
        COUNT(*) as completed_count,
        AVG(up.last_score) as avg_score
    FROM User u
    JOIN UserProgress up ON u.telegram_id = up.user_id
    JOIN Lesson l ON up.lesson_id = l.id
    WHERE up.status = 'completed'
    GROUP BY u.telegram_id, l.skill_level
) level_progress
GROUP BY skill_level;

-- Advancement rates
SELECT 
    'Beginner to Intermediate' as transition,
    COUNT(DISTINCT CASE WHEN skill_level = 'intermediate' THEN telegram_id END) * 100.0 / 
    COUNT(DISTINCT CASE WHEN skill_level = 'beginner' THEN telegram_id END) as advancement_rate
FROM User
WHERE created_at > DATE_SUB(NOW(), INTERVAL 30 DAY);
```

---

## 9. Rollback Plan

### 9.1 Risk Assessment

**Low Risk**:
- No database schema changes
- Backward compatible (existing flows unchanged)
- New code isolated in new methods
- Existing methods minimally modified

**Potential Issues**:
- Incorrect average calculation
- Missing edge cases in level detection
- UI/UX issues with new messages
- Performance impact from additional queries

### 9.2 Rollback Triggers

**Immediate Rollback If**:
- Error rate >5% in new handlers
- Users unable to complete lessons
- Database performance degradation
- Critical bug in level detection logic

### 9.3 Rollback Procedure

```bash
# 1. Identify problematic commit
git log --oneline

# 2. Create hotfix branch
git checkout -b hotfix/rollback-progression

# 3. Revert changes
git revert <commit-hash>

# 4. Test locally
pytest

# 5. Deploy hotfix
git push origin hotfix/rollback-progression
# Follow deployment process

# 6. Monitor for stability
tail -f logs/promptheus.log
```

**Post-Rollback**:
- Analyze root cause
- Fix issues in feature branch
- Re-test thoroughly
- Deploy when ready

---

## 10. Future Enhancements

### 10.1 Phase 2 Features (Post-MVP)

**Adaptive Difficulty**:
- Adjust minimum score threshold based on lesson difficulty
- Lessons 1-2: 6/10 threshold
- Lessons 3-4: 7/10 threshold
- Lesson 5: 8/10 threshold

**Skill Decay Detection**:
- Track time since last activity per level
- Suggest review if inactive >30 days
- Offer "refresher quiz" before advanced content

**Personalized Retry Recommendations**:
- AI analyzes common mistakes across retries
- Suggests specific theory sections to review
- Offers additional practice exercises

### 10.2 Analytics Enhancements

**User Segmentation**:
- Fast learners (complete level in <1 week)
- Perfectionists (retry multiple times for 10/10)
- Strugglers (avg score 6-7, need encouragement)

**Predictive Modeling**:
- Predict likelihood to advance based on early scores
- Identify users at risk of dropout
- Personalize encouragement messages

### 10.3 Gamification

**Badges & Achievements**:
- "First Try Master": Complete lesson with 10/10 on first attempt
- "Persistent Learner": Retry lesson 3+ times before completion
- "Level Speedrun": Complete level in <3 days

**Leaderboards**:
- Top scores per level (opt-in)
- Fastest level completion times
- Most improved scores

---

## Appendix A: File Structure Reference

```
src/promptheus/
├── bot/
│   ├── command_handlers.py (no changes)
│   ├── lesson_handlers.py (✏️ MODIFIED - add level completion logic)
│   ├── practice_handlers.py (✏️ MODIFIED - add score enforcement)
│   ├── progress_handlers.py (✏️ MODIFIED - multi-level display)
│   └── message_formatter.py (✏️ MODIFIED - new message templates)
├── core/
│   ├── progress_tracker.py (✏️ MODIFIED - add eligibility check)
│   └── learning_flow_orchestrator.py (no changes)
├── data/
│   ├── models.py (✅ NO CHANGES)
│   ├── async_repositories.py (✅ NO CHANGES - existing methods used)
│   └── database.py (✅ NO CHANGES)
└── main.py (✏️ MODIFIED - register new callback)

tests/
├── test_practice_handlers.py (📝 NEW TESTS)
├── test_lesson_handlers.py (📝 NEW TESTS)
├── test_progress_tracker.py (📝 NEW TESTS)
├── integration/
│   └── test_level_progression_flow.py (📝 NEW FILE)
└── e2e/
    └── test_full_progression_journey.py (📝 NEW FILE)
```

---

## Appendix B: Key Callback Patterns

**New Callback Patterns**:
```python
# Level advancement
"advance_to_beginner"
"advance_to_intermediate"
"advance_to_advanced"

# Level retry
"retry_level_beginner"
"retry_level_intermediate"
"retry_level_advanced"

# Practice with lesson context
"practice_retry_{lesson_id}"
"practice_hint_{lesson_id}"
```

**Existing Patterns** (unchanged):
```python
"lesson_{lesson_id}"
"lesson_complete_{lesson_id}"
"lesson_list"
"progress"
"menu"
```

---

## Appendix C: Implementation Timeline

| Day | Phase | Tasks | Deliverables |
|-----|-------|-------|--------------|
| 1 | Score Enforcement | Update practice_handlers, message_formatter, tests | Score validation working |
| 1-2 | Eligibility Check | Add check_level_eligibility to ProgressTracker, tests | Eligibility calculation working |
| 2-3 | Level Completion | Modify lesson_handlers, add completion flows, tests | Level detection working |
| 3 | Advancement Logic | Add advancement callback, register in main, tests | Skill level updates working |
| 4 | UX Polish | Message formatting, multi-level progress, visual hierarchy | Polished user experience |
| 4 | Multi-Level Display | Update progress_handlers with grouped stats | All-level progress view |
| 5 | Testing & QA | E2E tests, integration tests, bug fixes | Test coverage >80%, all tests pass |

**Total**: 4-5 working days

---

## Document Change Log

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-11-06 | Implementation Team | Initial comprehensive implementation guide |

---

## References

1. **Feature Specification**: `tasks/feature-skill-level-progression.md`
2. **Technical Requirements**: `docs/technical-requirements-document.md`
3. **User Stories**: `docs/user-stories.md`
4. **System Architecture**: `docs/system-architecture-document.md`
5. **Database Design**: `docs/database-design-document.md`
6. **UX Specifications**: `docs/ux-design-specifications.md`

---

**End of Implementation Guide**
