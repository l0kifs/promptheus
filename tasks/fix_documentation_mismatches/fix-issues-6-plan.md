# Technical Task Template for AI Agent

> **Version:** 1.0.0  
> **Created:** 2025-11-07  
> **Purpose:** Fix documentation discrepancies in assessment engine

---

## 📋 Table of Contents

1. [METADATA](#metadata)
2. [BUSINESS CONTEXT](#business-context)
3. [TECHNICAL SPECIFICATION](#technical-specification)
4. [TECHNICAL CONTEXT](#technical-context)
5. [EXAMPLES AND DOCUMENTATION](#examples-and-documentation)
6. [ACCEPTANCE CRITERIA](#acceptance-criteria)
7. [IMPLEMENTATION PLAN](#implementation-plan)
8. [TESTING AND VALIDATION](#testing-and-validation)
9. [ADDITIONAL CONSIDERATIONS](#additional-considerations)
10. [COMPLETION CHECKLIST](#completion-checklist)

---

## METADATA

**Task ID:** PRMT-061  
**Name:** Fix Assessment Engine Issues 6.1-6.2  
**Created:** 2025-11-07  
**Priority:** High  
**Complexity Estimate:** 7/10  
**Estimated Time:** 6-8 hours  

---

## BUSINESS CONTEXT

### Problem Description
The assessment engine has critical discrepancies between documented behavior and actual implementation. Users receive inaccurate skill level assessments because the system uses simple answer counting instead of AI-powered analysis, leading to poor learning path personalization.

### Business Goals
- Provide accurate skill level assessment using AI analysis
- Ensure consistent 5-question assessment format
- Improve user experience with personalized learning paths
- Maintain assessment reliability and user trust

### Target Audience
- **Primary:** New users during onboarding
- **Secondary:** Development team maintaining assessment accuracy

### Business Value
- Better user onboarding experience (higher completion rates)
- More accurate learning path recommendations
- Reduced user frustration from mismatched difficulty levels
- Foundation for scalable assessment system

---

## TECHNICAL SPECIFICATION

### Functional Requirements

#### Main Functionality
Implement AI-powered assessment evaluation that analyzes user responses to determine skill level, replacing the current simple correct/incorrect counting system.

#### Detailed Requirements

1. **AI-Powered Assessment Evaluation**
   - Description: Use OpenRouter API to analyze user responses to assessment questions
   - Input data: User's answers to 5 assessment questions, skill level context
   - Output data: Score (0-100), skill level determination, detailed analysis
   - Constraints: Must maintain 5-question format, response time <10 seconds

2. **Assessment Question Validation**
   - Description: Ensure exactly 5 multiple-choice questions are presented
   - Input data: Assessment questions configuration
   - Output data: Validated question set
   - Constraints: Must match US §1.2 specification (5 questions)

3. **Fallback Assessment Logic**
   - Description: Provide basic assessment when AI is unavailable
   - Input data: User answers, error condition
   - Output data: Conservative skill level assignment
   - Constraints: Must be clearly marked as fallback, log AI unavailability

### Non-Functional Requirements

#### Performance
- Assessment evaluation: <10 seconds (AI response time)
- Question loading: <100ms
- Memory usage: <50MB per assessment

#### Reliability
- AI service unavailability: Graceful fallback to basic logic
- Invalid responses: Error handling with user-friendly messages
- Concurrent assessments: Support 10+ simultaneous evaluations

#### Compatibility
- Maintain existing API contracts
- Backward compatibility with current assessment data
- Integration with existing dependency injection pattern

---

## TECHNICAL CONTEXT

### System Architecture
```
┌─────────────────┐      ┌──────────────────┐      ┌─────────────────┐
│ Assessment      │─────▶│ AI Integration   │─────▶│ OpenRouter API  │
│ Engine          │      │ Layer            │      │                 │
└─────────────────┘      └──────────────────┘      └─────────────────┘
         │
         ▼
┌─────────────────┐
│ Database        │
│ (User.skill_level)
└─────────────────┘
```

### Technology Stack
- **Language:** Python 3.11+
- **AI Client:** OpenRouter API with fallback chain
- **Templates:** PromptTemplateManager for assessment prompts
- **Async:** Full async/await implementation
- **Testing:** pytest with mocked AI responses

### Project Structure
```
src/promptheus/
├── core/
│   ├── assessment_engine.py          ← MODIFY: Add AI evaluation
│   └── ...
├── ai/
│   ├── prompt_template_manager.py    ← MODIFY: Add assessment template
│   └── openrouter_client.py          ← USE: For AI calls
├── config/
│   └── settings.py                   ← CHECK: AI model config
└── data/
    └── models.py                     ← USE: SkillLevel enum
```

### Files to Modify

1. **`src/promptheus/core/assessment_engine.py`**
   - Purpose: Main assessment logic and skill level calculation
   - Where to make changes: `evaluate_answers()` method, add AI evaluation
   - Notes: Maintain backward compatibility, add error handling

2. **`src/promptheus/ai/prompt_template_manager.py`**
   - Purpose: AI prompt templates for different scenarios
   - Where to make changes: Add assessment evaluation template
   - Notes: Template should analyze answer patterns, not just count correct answers

3. **`src/promptheus/config/settings.py`**
   - Purpose: Application configuration
   - Where to make changes: Verify AI model settings for assessment
   - Notes: Ensure appropriate temperature/max_tokens for assessment

### Related Components
- **OpenRouterClient:** For AI API calls with fallback
- **DependencyContainer:** For proper component injection
- **User Model:** For storing assessment results
- **Bot Handlers:** For calling assessment engine

---

## EXAMPLES AND DOCUMENTATION

### Code Examples

#### Example 1: Current Implementation (Problematic)
```python
# assessment_engine.py - Current evaluate_answers
async def evaluate_answers(self, answers: list[str]) -> dict[str, int | str]:
    # Simple counting - NO AI ANALYSIS
    results = [ans == correct for ans, correct in zip(answers, correct_answers)]
    correct_count = sum(results)
    score = int((correct_count / total) * 100)
    
    # Basic threshold logic
    if score >= 80:
        level = SkillLevel.ADVANCED
    elif score >= 60:
        level = SkillLevel.INTERMEDIATE
    else:
        level = SkillLevel.BEGINNER
```

#### Example 2: Desired Implementation (AI-Powered)
```python
# assessment_engine.py - Fixed evaluate_answers
async def evaluate_answers(self, answers: list[str]) -> dict[str, int | str]:
    # Use AI to analyze answer patterns and context
    analysis_prompt = self.template_manager.render(
        "assessment_analysis",
        answers=answers,
        questions=self.get_assessment_questions()
    )
    
    response = await self.ai_client.call_with_fallback(
        prompt=analysis_prompt,
        max_tokens=self.settings.max_tokens_assessment,
        temperature=self.settings.temperature_assessment,
    )
    
    # Parse AI analysis for nuanced evaluation
    analysis = self._parse_assessment_response(response)
    return analysis
```

#### Example 3: Assessment Analysis Template
```python
# prompt_template_manager.py - New template
self.register_template(
    "assessment_analysis",
    """You are an expert prompt engineering instructor evaluating a student's knowledge assessment.

Assessment Questions and Student Answers:
{questions_and_answers}

Analyze the student's understanding of prompt engineering concepts:
1. Correctness of answers
2. Depth of understanding shown in responses
3. Pattern recognition in prompt engineering principles
4. Practical application knowledge

Provide assessment in JSON format:
{{
  "score": <0-100, nuanced evaluation>,
  "skill_level": "beginner|intermediate|advanced",
  "analysis": "Brief explanation of assessment",
  "strengths": ["key strengths observed"],
  "areas_for_improvement": ["areas needing work"]
}}""",
)
```

### Documentation
- [TRD §2.1](../docs/technical-requirements-document.md): AI analyzes user responses and adapts content
- [US §1.2](../docs/user-stories.md): 5 multiple-choice questions for assessment
- [DDD §3.1](../docs/database-design-document.md): User assessment_score storage
- [OpenRouter API Documentation](https://openrouter.ai/docs): Model capabilities and parameters

### Existing Patterns
- **AI Integration:** `evaluate_user_prompt()` method uses AI evaluation successfully
- **Template Management:** `PromptTemplateManager` with `render()` method
- **Error Handling:** Try/catch with fallback responses in AI methods
- **Async Patterns:** `await` for all AI calls, proper session management

### Known Pitfalls
⚠️ **Important:**
- AI responses may be inconsistent - implement robust JSON parsing with fallbacks
- Assessment must be fast (<10s) - use lightweight model for analysis
- Maintain exact 5-question format - don't change question structure
- Handle AI service outages gracefully - fallback to basic counting with warning
- Consider answer context, not just correctness - AI should analyze reasoning quality

---

## ACCEPTANCE CRITERIA

### Scenario Criteria (Given-When-Then)

#### Scenario 1: Successful AI-powered assessment
```gherkin
Given user completes 5 assessment questions
When system evaluates answers using AI analysis
Then AI provides nuanced score (0-100) based on understanding depth
And skill level is determined considering answer patterns
And assessment completes within 10 seconds
```

#### Scenario 2: AI service unavailable
```gherkin
Given AI service is down during assessment
When system attempts AI evaluation
Then system falls back to basic answer counting
And user receives assessment with clear "limited analysis" notice
And error is logged for monitoring
```

#### Scenario 3: Invalid AI response format
```gherkin
Given AI returns malformed JSON response
When system parses assessment result
Then system uses fallback parsing logic
And provides reasonable default assessment
And continues user onboarding flow
```

### Rules and Constraints
- [ ] Assessment must use exactly 5 questions (no more, no less)
- [ ] AI evaluation must complete within 10 seconds timeout
- [ ] Skill level determination must consider answer quality, not just count
- [ ] Fallback logic must be clearly distinguishable from AI analysis
- [ ] All existing API contracts must remain unchanged

### Testing
- [ ] Unit tests for AI evaluation logic (>=90% coverage)
- [ ] Integration tests with mocked AI responses
- [ ] End-to-end assessment flow testing
- [ ] AI service failure scenario testing
- [ ] Performance tests (<10s response time)

### Code Review
- [ ] Code follows async patterns consistently
- [ ] Error handling covers AI failures gracefully
- [ ] Template rendering is secure (no injection risks)
- [ ] Logging includes relevant context (user_id, assessment details)

### Performance
- [ ] AI assessment evaluation: <10 seconds average
- [ ] Memory usage: <50MB per assessment
- [ ] No memory leaks in AI response processing
- [ ] Concurrent assessments don't degrade performance

---

## IMPLEMENTATION PLAN

### Execution Stages

#### Stage 1: Template and Configuration Setup
**Description:** Add assessment analysis template and verify AI settings
**Tasks:**
- [ ] Add "assessment_analysis" template to PromptTemplateManager
- [ ] Verify AI model settings in config (temperature=0.3, max_tokens=256)
- [ ] Test template rendering with sample data
- [ ] Update template documentation

**Validation:**
- Template renders correctly with assessment data
- AI settings match assessment requirements
- No syntax errors in template strings

#### Stage 2: AI Evaluation Implementation
**Description:** Implement AI-powered assessment evaluation
**Tasks:**
- [ ] Modify `evaluate_answers()` to use AI analysis instead of simple counting
- [ ] Add response parsing method for assessment results
- [ ] Implement fallback logic for AI failures
- [ ] Add comprehensive error handling and logging

**Validation:**
- AI evaluation returns expected JSON structure
- Fallback logic works when AI unavailable
- Assessment still completes within time limits

#### Stage 3: Question Count Validation
**Description:** Ensure exactly 5 questions are used
**Tasks:**
- [ ] Verify `get_assessment_questions()` returns exactly 5 questions
- [ ] Add validation check in assessment engine
- [ ] Update documentation to confirm 5-question requirement
- [ ] Test question loading and validation

**Validation:**
- Assessment always presents exactly 5 questions
- Question structure matches expected format
- No runtime errors with question loading

#### Stage 4: Testing and Validation
**Description:** Comprehensive testing of new assessment logic
**Tasks:**
- [ ] Write unit tests for AI evaluation logic
- [ ] Add integration tests with mocked AI client
- [ ] Test error scenarios (AI timeout, invalid responses)
- [ ] Performance testing for response times

**Validation:**
- All tests pass with >90% coverage
- AI evaluation works in test environment
- Fallback scenarios handled correctly

#### Stage 5: Documentation Update
**Description:** Update code documentation and comments
**Tasks:**
- [ ] Update docstrings in assessment_engine.py
- [ ] Add comments explaining AI evaluation logic
- [ ] Update method signatures and type hints
- [ ] Document fallback behavior

**Validation:**
- Code is self-documenting
- Docstrings follow Google style
- Type hints are complete and accurate

---

## TESTING AND VALIDATION

### Unit Tests
```python
# tests/core/test_assessment_engine.py
import pytest
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_evaluate_answers_with_ai_success():
    """Test successful AI-powered assessment evaluation."""
    # Given
    mock_ai_client = AsyncMock()
    mock_template_manager = Mock()
    engine = AssessmentEngine(mock_ai_client, mock_template_manager)
    
    mock_ai_client.call_with_fallback.return_value = '''
    {
      "score": 75,
      "skill_level": "intermediate",
      "analysis": "Good understanding of basic concepts",
      "strengths": ["Clear role understanding"],
      "areas_for_improvement": ["Context provision"]
    }
    '''
    
    # When
    result = await engine.evaluate_answers(["A", "B", "C", "A", "B"])
    
    # Then
    assert result["score"] == 75
    assert result["level"] == "intermediate"
    mock_ai_client.call_with_fallback.assert_called_once()

@pytest.mark.asyncio
async def test_evaluate_answers_ai_failure_fallback():
    """Test fallback when AI evaluation fails."""
    # Given
    mock_ai_client = AsyncMock(side_effect=Exception("AI timeout"))
    engine = AssessmentEngine(mock_ai_client, Mock())
    
    # When
    result = await engine.evaluate_answers(["A", "B", "C", "A", "B"])
    
    # Then
    assert "fallback" in result  # Indicate fallback was used
    assert isinstance(result["score"], int)
    assert result["level"] in ["beginner", "intermediate", "advanced"]
```

### Commands to Run
```bash
# Run assessment engine tests
pytest tests/core/test_assessment_engine.py -v

# Run with coverage
pytest --cov=src/promptheus/core/assessment_engine.py tests/core/test_assessment_engine.py

# Test AI integration
pytest tests/ai/test_openrouter_client.py -k assessment

# Full test suite
pytest --cov --cov-fail-under=90
```

### Manual Testing Scenarios

1. **Normal assessment flow**
   - Complete 5 questions as beginner user
   - Verify AI analysis provides nuanced feedback
   - Check skill level assignment is appropriate

2. **AI service interruption**
   - Simulate AI timeout during assessment
   - Verify fallback logic activates
   - Confirm user still receives assessment result

3. **Edge case answers**
   - Answer all questions incorrectly
   - Answer all questions correctly
   - Mix correct/incorrect answers
   - Verify AI analysis considers patterns

---

## ADDITIONAL CONSIDERATIONS

### Risks
- **Risk: AI analysis too slow (>10s timeout)**
  - Mitigation: Use lightweight model, implement response caching, optimize prompt length
  
- **Risk: Inconsistent AI responses**
  - Mitigation: Robust JSON parsing, fallback logic, response validation
  
- **Risk: Breaking existing assessment flow**
  - Mitigation: Maintain API compatibility, extensive testing, gradual rollout

### Assumptions
- OpenRouter API remains stable and available
- Assessment questions remain at 5 (as per US §1.2)
- AI models can provide consistent JSON responses
- Fallback logic provides reasonable assessment quality

### Limitations
- AI analysis depends on model quality and consistency
- Fallback assessment is less sophisticated than AI analysis
- Assessment is limited to 5 questions for performance
- No real-time assessment adjustment during question flow

### Future Improvements
- [ ] Implement progressive assessment (adjust difficulty based on answers)
- [ ] Add assessment analytics and improvement tracking
- [ ] Support for different assessment types (video, interactive)
- [ ] Multi-language assessment support
- [ ] Assessment A/B testing framework

---

## COMPLETION CHECKLIST

### Development
- [ ] Added assessment analysis template to PromptTemplateManager
- [ ] Modified evaluate_answers() to use AI evaluation
- [ ] Implemented response parsing for assessment results
- [ ] Added fallback logic for AI service failures
- [ ] Verified exactly 5 assessment questions
- [ ] Added comprehensive error handling and logging

### Testing
- [ ] Unit tests for AI evaluation logic (≥90% coverage)
- [ ] Integration tests with mocked AI responses
- [ ] Tests for AI failure scenarios and fallback behavior
- [ ] Performance tests ensuring <10s response time
- [ ] End-to-end assessment flow validation

### Documentation
- [ ] Updated docstrings in assessment_engine.py
- [ ] Added comments explaining AI evaluation approach
- [ ] Documented fallback behavior and limitations
- [ ] Updated method signatures and type hints

### Code Quality
- [ ] Code follows async patterns consistently
- [ ] Ruff linting passes without errors
- [ ] mypy type checking successful
- [ ] No hardcoded values or magic numbers

### Finalization
- [ ] All tests pass in CI/CD pipeline
- [ ] Code review completed and approved
- [ ] Assessment discrepancies resolved (6.1-6.2)
- [ ] Documentation updated to reflect implementation
- [ ] Task marked as completed in project tracking</content>
<parameter name="filePath">/home/serj/dev/my-github-repos/promptheus/tasks/fix_documentation_mismatches/fix-issues-6-plan.md