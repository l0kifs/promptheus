# Task-Prompt Alignment Validation - Implementation Guide

## Problem Statement

Currently, the AI evaluation system assesses user prompts based solely on generic prompt engineering principles (role definition, context clarity, instructions, output format) **without validating whether the prompt actually addresses the exercise task**.

### Example of the Issue

**Lesson**: Prompt Chaining and Workflows (Advanced)

**Exercise Task**: 
> Design a 4-prompt chain: topic research → headline generation → outline creation → first draft. Write all 4 prompts with clear handoffs.

**User's Submitted Prompt**:
> You are an expert in marketing, make an analysis of my business decision for expanding for a new market...

**Current Behavior**: 
- Score: 6/10
- Feedback focuses on improving role definition, context clarity, output format
- **Missing**: Recognition that the user's prompt is about business analysis, NOT a 4-prompt chain for content marketing

**Expected Behavior**:
- Score: 2-3/10 (low due to task mismatch)
- Feedback highlights the misalignment: "Your prompt addresses business decision analysis, but the task requires a 4-prompt workflow chain for content marketing"
- Guide user back to the actual task

---

## Solution Overview

Enhance the AI evaluation prompt template to include the exercise scenario and task, enabling the AI to:
1. **Validate alignment** between user's prompt and the exercise task
2. **Penalize misalignment** with lower scores
3. **Provide specific feedback** about what the task actually requires
4. **Evaluate quality** only after confirming alignment

---

## Implementation Steps

### Step 1: Update Prompt Template Manager

**File**: `src/promptheus/ai/prompt_template_manager.py`

**Current Template** (`exercise_feedback`):
```python
self.register_template(
    "exercise_feedback",
    """You are an expert prompt engineering instructor evaluating a student's exercise submission.

Student's Prompt: "{user_prompt}"

Skill Level: {skill_level}
Learning Goal: {learning_goal}

Provide a structured evaluation:
1. Score (0-10): Rate the prompt quality
2. Strengths: What's good about it (2-3 points)
3. Improvements: What could be better (2-3 points)

Focus on: role definition, context clarity, specific instructions, and output format.

Respond in this exact JSON format:
{{
  "score": <number>,
  "strengths": ["strength1", "strength2"],
  "improvements": ["improvement1", "improvement2"]
}}""",
)
```

**Updated Template** (with task alignment validation):
```python
self.register_template(
    "exercise_feedback",
    """You are an expert prompt engineering instructor evaluating a student's exercise submission.

Exercise Context:
Scenario: {exercise_scenario}
Task: {exercise_task}

Student's Prompt: "{user_prompt}"

Skill Level: {skill_level}
Learning Goal: {learning_goal}

Evaluation Process:
1. FIRST: Check if the student's prompt addresses the exercise task
   - Does the prompt attempt to solve the given scenario/task?
   - If NO (major mismatch): Score 0-3, explain the mismatch in improvements
   - If PARTIAL (addresses task but poorly): Score 3-6, note alignment issues
   - If YES (clearly aligned): Score 4-10 based on quality

2. THEN: If aligned, evaluate prompt quality based on:
   - Role definition
   - Context clarity
   - Specific instructions
   - Output format

Respond in this exact JSON format:
{{
  "score": <number 0-10>,
  "strengths": ["strength1", "strength2"],
  "improvements": ["improvement1", "improvement2"]
}}

For misaligned prompts, improvements MUST start with explaining the mismatch.
Example: "Your prompt addresses [X], but the task requires [Y]. Please create a prompt that..."
""",
)
```

**Changes**:
- Added `{exercise_scenario}` and `{exercise_task}` variables
- Explicit instruction to validate alignment FIRST
- Scoring guidance based on alignment level
- Required format for mismatch feedback

---

### Step 2: Update Assessment Engine to Pass Exercise Context

**File**: `src/promptheus/core/assessment_engine.py`

**Current Method** (line ~286):
```python
async def evaluate_user_prompt(
    self,
    user_prompt: str,
    lesson_id: int,
    skill_level: str = "beginner",
    learning_goal: str = "general",
) -> dict[str, int | list[str]]:
    """Evaluate user's prompt submission for a practice exercise."""
    logger.info("Evaluating user prompt", lesson_id=lesson_id, prompt_length=len(user_prompt))

    # Create evaluation prompt using template manager
    evaluation_prompt = self.template_manager.render(
        "exercise_feedback",
        user_prompt=user_prompt,
        skill_level=skill_level,
        learning_goal=learning_goal,
    )
```

**Updated Method**:
```python
async def evaluate_user_prompt(
    self,
    user_prompt: str,
    lesson_id: int,
    exercise_scenario: str = "",
    exercise_task: str = "",
    skill_level: str = "beginner",
    learning_goal: str = "general",
) -> dict[str, int | list[str]]:
    """Evaluate user's prompt submission for a practice exercise.
    
    Args:
        user_prompt: The prompt submitted by the user
        lesson_id: The ID of the current lesson
        exercise_scenario: The exercise scenario/context from the lesson
        exercise_task: The specific task the user should complete
        skill_level: User's current skill level
        learning_goal: User's learning goal
    
    Returns:
        Dictionary with score (0-10), strengths, and improvements
    """
    logger.info("Evaluating user prompt", lesson_id=lesson_id, prompt_length=len(user_prompt))

    # Create evaluation prompt using template manager with exercise context
    evaluation_prompt = self.template_manager.render(
        "exercise_feedback",
        user_prompt=user_prompt,
        exercise_scenario=exercise_scenario,
        exercise_task=exercise_task,
        skill_level=skill_level,
        learning_goal=learning_goal,
    )
```

**Changes**:
- Added `exercise_scenario` and `exercise_task` parameters
- Updated docstring
- Pass new parameters to template renderer

---

### Step 3: Update Practice Handler to Extract and Pass Exercise Context

**File**: `src/promptheus/bot/practice_handlers.py`

**Current Code** (in `text_message_handler`, line ~290):
```python
# Get AI feedback
assessment_engine = self.assessment_engine
feedback = await assessment_engine.evaluate_user_prompt(user_prompt, lesson_id)
```

**Updated Code**:
```python
# Get lesson to extract exercise context
lesson = await self.learning_orchestrator.lesson_repo.find_by_id(lesson_id)

if not lesson:
    logger.error("Lesson not found for evaluation", lesson_id=lesson_id)
    await loading_msg.edit_text(
        "❌ Error: Lesson not found. Please try again.",
        parse_mode="Markdown",
    )
    return

# Extract exercise scenario and task from lesson
exercises = lesson.exercises  # type: ignore
scenarios = exercises.get("scenarios", [])

exercise_scenario = ""
exercise_task = ""
if scenarios:
    first_scenario = scenarios[0]
    exercise_scenario = first_scenario.get("scenario", "")
    exercise_task = first_scenario.get("task", "")

# Get user for skill level and learning goal
user = await self.learning_orchestrator.user_repo.find_by_telegram_id(user_id)
skill_level = user.skill_level.value if user else "beginner"
learning_goal = user.learning_goal.value if user else "general"

# Get AI feedback with exercise context
assessment_engine = self.assessment_engine
feedback = await assessment_engine.evaluate_user_prompt(
    user_prompt=user_prompt,
    lesson_id=lesson_id,
    exercise_scenario=exercise_scenario,
    exercise_task=exercise_task,
    skill_level=skill_level,
    learning_goal=learning_goal,
)
```

**Changes**:
- Retrieve lesson to access exercise data
- Extract scenario and task from lesson.exercises
- Retrieve user to get actual skill_level and learning_goal
- Pass all context to evaluation method

**Location**: Insert this code before the `assessment_engine.evaluate_user_prompt` call (around line 290)

---

### Step 4: Update Tests

**File**: `tests/test_assessment_handlers.py` (or create new test file)

Add test cases for:

```python
@pytest.mark.asyncio
async def test_evaluate_prompt_with_task_mismatch(engine, mocker):
    """Test that misaligned prompts receive low scores."""
    # Mock AI response for misaligned prompt
    engine.ai_client.call_with_fallback.return_value = """{
        "score": 2,
        "strengths": ["Well-written prompt for a different task"],
        "improvements": [
            "Your prompt addresses business decision analysis, but the task requires a 4-prompt workflow chain for content marketing",
            "Create 4 connected prompts with clear handoffs between them"
        ]
    }"""
    
    # Mock template manager
    engine.template_manager.render.return_value = "Rendered prompt with task context"
    
    result = await engine.evaluate_user_prompt(
        user_prompt="Analyze my business decision to expand to new market...",
        lesson_id=12,
        exercise_scenario="You want to create a content marketing workflow",
        exercise_task="Design a 4-prompt chain: topic research → headline generation → outline creation → first draft",
        skill_level="advanced",
        learning_goal="professional"
    )
    
    assert result["score"] <= 3  # Low score for mismatch
    assert any("task requires" in imp.lower() for imp in result["improvements"])
    
    # Verify template was called with exercise context
    engine.template_manager.render.assert_called_once()
    call_args = engine.template_manager.render.call_args[1]
    assert "exercise_scenario" in call_args
    assert "exercise_task" in call_args


@pytest.mark.asyncio
async def test_evaluate_prompt_with_task_alignment(engine, mocker):
    """Test that aligned prompts are evaluated on quality."""
    # Mock AI response for aligned prompt
    engine.ai_client.call_with_fallback.return_value = """{
        "score": 8,
        "strengths": [
            "Addresses the task correctly with 4-prompt chain",
            "Clear handoffs between prompts"
        ],
        "improvements": [
            "Could add more specific role definitions",
            "Consider specifying output format for each step"
        ]
    }"""
    
    engine.template_manager.render.return_value = "Rendered prompt"
    
    result = await engine.evaluate_user_prompt(
        user_prompt="Prompt 1: Research trending topics in [industry]... Prompt 2: Using the topics from above, generate 10 headlines...",
        lesson_id=12,
        exercise_scenario="You want to create a content marketing workflow",
        exercise_task="Design a 4-prompt chain: topic research → headline generation → outline creation → first draft",
        skill_level="advanced",
        learning_goal="professional"
    )
    
    assert result["score"] >= 7  # Good score for aligned, quality prompt
```

**File**: `tests/e2e/test_practice_evaluation.py`

Update existing E2E test to pass exercise context:

```python
@pytest.mark.asyncio
async def test_successful_prompt_evaluation(
    self, bot_handlers, practice_user_update, practice_user_context, mocker
):
    """Test successful prompt submission and evaluation with task context."""
    # ... existing setup code ...
    
    # Mock AI evaluation with task alignment
    bot_handlers.assessment_engine.evaluate_user_prompt = mocker.AsyncMock(
        return_value={
            "score": 9,
            "strengths": [
                "Correctly addresses the exercise task",
                "Excellent task specificity",
                "Clear context provided"
            ],
            "improvements": ["Consider adding output format requirements"],
        }
    )
    
    # ... rest of test ...
```

---

### Step 5: Update Database Schema Documentation (if needed)

**File**: `docs/database-design-document.md`

The existing lesson schema already includes the `exercises` field with scenario and task:

```json
{
  "scenarios": [
    {
      "scenario": "Scenario description",
      "task": "Your task"
    }
  ]
}
```

**No changes needed** - schema already supports this feature.

---

## Validation & Testing

### Manual Testing Steps

1. **Test Misaligned Prompt**:
   - Start lesson 12 (Prompt Chaining and Workflows)
   - Go to practice exercise
   - Submit: "You are a business analyst. Analyze my decision to expand to a new market..."
   - Expected: Score 2-3/10, feedback says "Your prompt addresses business analysis, but the task requires a 4-prompt chain"

2. **Test Aligned Prompt**:
   - Same lesson
   - Submit: "Prompt 1: Research trending topics in [industry]. Prompt 2: Using topics above, generate headlines..."
   - Expected: Score 7-10/10, feedback evaluates quality (role, context, etc.)

3. **Test Partial Alignment**:
   - Same lesson
   - Submit: "Create headlines for content marketing" (addresses part of task but not the full chain)
   - Expected: Score 4-6/10, feedback notes incomplete task coverage

### Automated Testing

Run the new unit tests:
```bash
pytest tests/test_assessment_handlers.py::test_evaluate_prompt_with_task_mismatch -v
pytest tests/test_assessment_handlers.py::test_evaluate_prompt_with_task_alignment -v
```

Run E2E tests:
```bash
pytest tests/e2e/test_practice_evaluation.py -v
```

---

## Expected Outcomes

### Before Implementation
- User submits prompt unrelated to task → Score 6/10 with generic feedback
- No indication that prompt doesn't address the exercise
- Confusing for learners who think they're doing well

### After Implementation
- User submits unrelated prompt → Score 2/10 with explicit mismatch explanation
- Clear guidance: "The task requires X, but your prompt does Y"
- Learner understands they need to address the specific task
- Aligned prompts are evaluated fairly on quality

---

## Implementation Checklist

- [x] Update documentation (user-stories.md, technical-requirements-document.md, system-architecture-document.md, ux-design-specifications.md)
- [x] Update `prompt_template_manager.py` - Add task context to `exercise_feedback` template
- [x] Update `assessment_engine.py` - Add `exercise_scenario` and `exercise_task` parameters
- [x] Update `practice_handlers.py` - Extract and pass exercise context
- [x] Create unit tests for alignment validation (3 new tests added, all 13 tests passing)
- [x] Update existing tests for backward compatibility
- [ ] Update E2E tests (optional - existing tests still pass)
- [ ] Manual testing with real lessons
- [ ] Code review
- [ ] Merge to develop branch

---

## Rollout Plan

1. **Development**: Implement changes in feature branch `feature/task-prompt-alignment`
2. **Testing**: Run full test suite, manual testing with lessons 1-15
3. **Review**: Code review with team
4. **Staging**: Deploy to staging environment, test with real API
5. **Production**: Gradual rollout:
   - Phase 1: Monitor AI responses for 24h
   - Phase 2: Analyze user feedback patterns
   - Phase 3: Full deployment

---

## Maintenance & Monitoring

### Metrics to Track
- Distribution of scores before/after implementation
- Frequency of task mismatch feedback
- User retry behavior after mismatch feedback
- User satisfaction (completion rates, session duration)

### AI Response Quality Monitoring
- Review AI evaluation logs weekly
- Check for false positives (aligned prompts marked as misaligned)
- Check for false negatives (misaligned prompts scored highly)
- Adjust template if patterns emerge

---

## Potential Issues & Solutions

### Issue 1: AI misjudges alignment
**Symptom**: User's prompt clearly addresses task but AI says it's misaligned

**Solution**: 
- Refine template with more examples
- Add explicit instruction: "Be generous in judging alignment - if the user attempts the task even partially, consider it aligned"

### Issue 2: Overly harsh scoring
**Symptom**: All prompts get 2-3/10 scores

**Solution**:
- Review template scoring guidance
- Add calibration examples in template
- Consider adjusting score ranges (0-2 for total mismatch, 3-5 for partial, 6+ for aligned)

### Issue 3: Template too long / token cost
**Symptom**: Increased API costs or response time

**Solution**:
- Optimize template wording
- Remove redundant instructions
- Consider using lightweight model for alignment check, then main model for quality evaluation

---

## Future Enhancements

1. **Multi-language Support**: Translate alignment feedback messages
2. **Example-based Validation**: Include good/bad examples in the template
3. **Automated Retry Suggestions**: Generate a corrected prompt attempt for the user
4. **Analytics Dashboard**: Visualize alignment success rates per lesson
5. **A/B Testing**: Test different template variations for optimal feedback

---

## References

- User Stories: `docs/user-stories.md` (US-3.2)
- Technical Requirements: `docs/technical-requirements-document.md` (§2.3, §2.4)
- System Architecture: `docs/system-architecture-document.md` (§2.3)
- UX Design: `docs/ux-design-specifications.md` (§3.2)
- Lesson Structure: `promptheus-content/lessons/advanced/12_prompt_chaining_and_workflows.json`
