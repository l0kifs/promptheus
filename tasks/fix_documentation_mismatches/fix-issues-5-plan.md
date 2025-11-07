# Plan for Fixing Issues 5.1 - 5.3: AI Integration

> **Task ID:** FIX-AI-INTEGRATION-001  
> **Date Created:** 2025-11-06  
> **Priority:** Medium  
> **Estimated Time:** 6-8 hours  
> **Related Document:** `tasks/fix_documentation_mismatches/documentation-mismatches.md`

---

## META INFORMATION

**Name:** Fix AI Integration Discrepancies - Fallback Chain, Prompt Templates, and Temperature/Token Settings  
**Task Type:** Bug Fix + Technical Debt  
**Affected Components:** AI Integration Layer (OpenRouter Client, Assessment Engine, Prompt Management)  
**Dependencies:** None (isolated improvements in AI layer)

---

## BUSINESS CONTEXT

### Problem Description

In the current implementation of the AI Integration Layer, there are three critical discrepancies between documentation and code:

**5.1 Fallback Chain (TRD §5.2, SAD §7.1)**
- Missing exponential backoff (exponential backoff) between model call attempts
- When the primary model fails, it immediately switches to fallback without pause
- This can lead to rapid exhaustion of rate limits for all models during an outage

**5.2 Prompt Templates (TRD §5.2, US §6.2)**
- Prompts are hardcoded directly in methods (`assessment_engine.py`)
- No centralized template management
- No support for personalization through variables (skill_level, learning_goal)
- Maintenance complexity: changing a prompt requires code modification

**5.3 Temperature & Token Settings (TRD §5.2)**
- Temperature and max_tokens values are hardcoded in the code
- Settings from `Settings` are not used, although they are defined
- No flexibility for testing different parameters without code modification

### Business Goals

1. **Increase AI integration reliability** through correct implementation of fallback chain
2. **Simplify prompt management** through a centralized Prompt Template Manager
3. **Provide flexibility for AI parameter configuration** through settings instead of hardcode

### Target Audience

- **Developers**: simplification of prompt support and modification
- **End Users**: improved reliability of AI responses

### Business Value

- Reduction in AI API errors through correct retry logic
- Acceleration of prompt iterations (A/B testing, optimization)
- Compliance with architectural documentation

---

## TECHNICAL SPECIFICATION

### Functional Requirements

#### 5.1 Exponential Backoff in Fallback Chain

**Current Behavior**:
```python
async def call_with_fallback(self, ...):
    for model in models:
        try:
            result = await self.call_model(...)
            return result
        except Exception:
            continue  # Immediate attempt with next model
```

**Required Behavior**:
```python
async def call_with_fallback(self, ...):
    for attempt, model in enumerate(models):
        try:
            result = await self.call_model(...)
            return result
        except Exception:
            if attempt < len(models) - 1:  # Not the last model
                delay = 2 ** attempt  # 1s, 2s, 4s
                await asyncio.sleep(delay)
            continue
```

**Input Data**:
- List of models (primary, fallback, alternative)
- Prompt and request parameters

**Output Data**:
- Successful response from any model
- Or final error after exhausting all attempts

**Constraints**:
- Maximum 3 models in the chain
- Delays: 1s, 2s, 4s (exponential)
- Total timeout < 30 seconds

#### 5.2 Centralized Prompt Template Manager

**Architecture**:
```python
class PromptTemplateManager:
    """Centralized management of AI prompt templates."""
    
    def __init__(self):
        self.templates: dict[str, str] = {}
    
    def register_template(self, name: str, template: str):
        """Register a prompt template."""
        
    def render(self, name: str, **variables) -> str:
        """Render template with variables."""
```

**Templates for Migration**:
1. **assessment_questions**: prompt for generating assessment questions
2. **assessment_evaluation**: prompt for evaluating user answers
3. **exercise_feedback**: prompt for exercise evaluation
4. **improved_prompt**: prompt for generating improved version

**Personalization Variables**:
- `{skill_level}`: beginner/intermediate/advanced
- `{learning_goal}`: academic/professional/creative
- `{user_prompt}`: user's prompt
- `{criteria}`: evaluation criteria

**Template Format (Jinja2-like)**:
```python
ASSESSMENT_EVALUATION_TEMPLATE = """
You are an expert in prompt engineering for {skill_level} level users.
User's learning goal: {learning_goal}

User's prompt:
{user_prompt}

Evaluate the prompt based on:
{criteria}

Provide structured feedback...
"""
```

#### 5.3 Use Settings for Temperature and Tokens

**Current State**:
```python
# settings.py - defined but not used
temperature_assessment: float = 0.3
temperature_feedback: float = 0.5
temperature_default: float = 0.7

max_tokens_assessment: int = 256
max_tokens_feedback: int = 512
max_tokens_default: int = 1024
```

**Changes**:
```python
# assessment_engine.py - BEFORE
response = await self.ai_client.call_with_fallback(
    prompt=evaluation_prompt,
    max_tokens=512,  # Hardcode
    temperature=0.3,  # Hardcode
)

# assessment_engine.py - AFTER
settings = get_settings()
response = await self.ai_client.call_with_fallback(
    prompt=evaluation_prompt,
    max_tokens=settings.max_tokens_feedback,  # From config
    temperature=settings.temperature_feedback,  # From config
)
```

**All Places for Replacement**:
1. `AssessmentEngine.evaluate_answers()` → temperature_assessment, max_tokens_assessment
2. `AssessmentEngine` (feedback generation) → temperature_feedback, max_tokens_feedback
3. `OpenRouterClient.call_model()` (default) → temperature_default, max_tokens_default

### Non-Functional Requirements

#### Performance
- Fallback chain should not increase latency > 10s upon primary model success
- Exponential backoff should not block other requests (async)

#### Reliability
- Graceful handling of all errors in fallback chain
- Logging of each attempt and used model
- Retry logic should not create infinite loops

#### Compatibility
- Backward compatibility with existing OpenRouterClient API
- Should not break existing tests
- Support for old prompts through default templates

---

## TECHNICAL CONTEXT

### System Architecture

```
Bot Handlers
     ↓
Assessment Engine ────→ OpenRouter Client
     ↓                       ↓
Prompt Template Manager    Fallback Chain
     ↓                       ↓
Templates (dict)     [Primary → Fallback → Alternative]
                             ↓
                     Exponential Backoff (1s, 2s, 4s)
```

### Technology Stack

- **Language**: Python 3.11+
- **Async Runtime**: asyncio
- **HTTP Client**: httpx
- **Templating**: String formatting (for MVP), Jinja2 (optional)
- **Configuration**: Pydantic Settings
- **Logging**: loguru

### Project Structure

```
src/promptheus/
├── ai/
│   ├── openrouter_client.py       ← FIX: exponential backoff
│   └── prompt_template_manager.py ← CREATE: new class
├── core/
│   └── assessment_engine.py       ← UPDATE: use templates + settings
├── config/
│   └── settings.py                ← OK: settings already present
└── data/
```

### Files for Modification

**1. `src/promptheus/ai/openrouter_client.py`**
- **Purpose**: HTTP client for OpenRouter API with fallback chain
- **Where to Make Changes**: method `call_with_fallback()`
- **Add**: 
  - Exponential backoff between attempts
  - Logging of each attempt with delay
  - Asynchronous sleep through `asyncio.sleep()`

**2. `src/promptheus/ai/prompt_template_manager.py`** (CREATE)
- **Purpose**: Centralized storage and rendering of prompt templates
- **Structure**:
  - Class `PromptTemplateManager`
  - Methods: `register_template()`, `render()`, `get_template()`
  - Dictionary of templates in memory
- **Templates for Migration**:
  - `assessment_evaluation`
  - `exercise_feedback`
  - `improved_prompt_generation`

**3. `src/promptheus/core/assessment_engine.py`**
- **Purpose**: Logic for evaluating user knowledge and exercises
- **Where to Make Changes**:
  - Constructor: inject `PromptTemplateManager`
  - `evaluate_answers()`: use `template_manager.render()`
  - All `ai_client` calls: use `settings.temperature_*` and `settings.max_tokens_*`

**4. `tests/ai/test_openrouter_client.py`** (UPDATE)
- Add tests for exponential backoff
- Mock `asyncio.sleep()` for fast tests
- Verify delays: 1s, 2s, 4s

**5. `tests/ai/test_prompt_template_manager.py`** (CREATE)
- Unit tests for template rendering
- Tests for variable substitution
- Tests for missing templates

**6. `tests/core/test_assessment_engine.py`** (UPDATE)
- Update mocks to use `PromptTemplateManager`
- Verify correct use of settings

---

## EXAMPLES AND DOCUMENTATION

### Code Examples

#### Example 1: Exponential Backoff in Similar Task (reference)

```python
import asyncio
from loguru import logger

async def retry_with_backoff(func, max_attempts: int = 3):
    """Generic retry with exponential backoff."""
    for attempt in range(max_attempts):
        try:
            return await func()
        except Exception as e:
            if attempt == max_attempts - 1:
                raise
            delay = 2 ** attempt
            logger.warning(
                "Attempt failed, retrying",
                attempt=attempt + 1,
                delay=delay,
                error=str(e)
            )
            await asyncio.sleep(delay)
```

**Explanation**: Use this pattern as the basis for the fallback chain.

#### Example 2: Template Manager in Another Project (reference)

```python
class PromptTemplateManager:
    def __init__(self):
        self.templates = {}
    
    def register(self, name: str, template: str):
        self.templates[name] = template
    
    def render(self, name: str, **kwargs) -> str:
        if name not in self.templates:
            raise ValueError(f"Template '{name}' not found")
        return self.templates[name].format(**kwargs)

# Usage
manager = PromptTemplateManager()
manager.register("greeting", "Hello, {name}!")
result = manager.render("greeting", name="Alice")
```

#### Example 3: Using Settings (current project)

```python
# Existing pattern in the project
from promptheus.config import get_settings

settings = get_settings()
logger.info("Using log level", level=settings.log_level)
```

**Explanation**: Apply the same pattern for AI parameters.

### Documentation

- **Python asyncio sleep**: https://docs.python.org/3/library/asyncio-task.html#asyncio.sleep
- **Exponential Backoff**: https://en.wikipedia.org/wiki/Exponential_backoff
- **String Formatting**: https://docs.python.org/3/library/string.html#formatstrings
- **Pydantic Settings**: https://docs.pydantic.dev/latest/concepts/pydantic_settings/

### Existing Project Patterns

- **Dependency Injection**: Through constructor, `DependencyContainer`
- **Logging**: Structured through `loguru` with kwargs
- **Settings**: Singleton through `get_settings()` from Pydantic
- **Async Repositories**: Pattern for database operations

### Known Gotchas

⚠️ **Important:**
- **Asyncio.sleep blocks only the current coroutine**, not the entire event loop (this is good)
- **Mocking asyncio.sleep in tests**: use `pytest-asyncio` with `mocker.patch()`
- **Template variables**: use `{key}` syntax for `.format()`, avoid f-strings in templates
- **Settings singleton**: call `get_settings()` once in `__init__`, not in every method
- **Exponential backoff overflow**: limit maximum delay (4s is the last one)

---

## ACCEPTANCE CRITERIA

### Scenario Criteria (Given-When-Then)

#### Scenario 5.1.1: Exponential Backoff on Primary Model Failure

```gherkin
Given primary model "llama-4-scout:free" is unavailable (500 error)
And fallback model "gemini-2.5-pro-exp:free" is available
When OpenRouterClient.call_with_fallback() is called
Then system logs attempt 1 with primary model
And waits 1 second (2^0)
And logs attempt 2 with fallback model
And returns successful response from fallback model
And total execution time is ~1s + fallback model latency
```

#### Scenario 5.1.2: All Models Unavailable

```gherkin
Given all models (primary, fallback, alternative) are unavailable
When OpenRouterClient.call_with_fallback() is called
Then system attempts primary → waits 1s → fallback → waits 2s → alternative
And after alternative failure raises final error
And logs all 3 attempts with delays
And total time is ~7s (1s + 2s + 4s + latencies)
```

#### Scenario 5.2.1: Template Rendering with Variables

```gherkin
Given template "assessment_evaluation" is registered in PromptTemplateManager
And template contains variables {skill_level}, {learning_goal}, {user_prompt}
When template_manager.render("assessment_evaluation", skill_level="beginner", ...) is called
Then system returns prompt with substituted values
And prompt has no unreplaced {placeholders}
```

#### Scenario 5.2.2: Using Template in AssessmentEngine

```gherkin
Given AssessmentEngine is initialized with PromptTemplateManager
And user submitted prompt for evaluation
When evaluate_answers() method is called
Then system renders "exercise_feedback" template with variables
And sends rendered prompt to ai_client
And returns structured evaluation
```

#### Scenario 5.3.1: Using Temperature from Settings

```gherkin
Given settings.py has temperature_feedback=0.5
And AssessmentEngine generates feedback on exercise
When ai_client.call_with_fallback() is called
Then parameter temperature=0.5 is passed to API
And value is NOT hardcoded in code (0.3 or 0.7)
```

### Rules and Constraints

- [ ] Exponential backoff is applied only between models, not within one model
- [ ] Maximum delay: 4 seconds (2^2)
- [ ] Templates are stored in PromptTemplateManager, not in files (for MVP)
- [ ] All AI parameters (temperature, max_tokens) are taken from Settings
- [ ] Logging of each fallback chain attempt is mandatory

### Testing

- [ ] Unit test: exponential backoff is applied correctly (mock asyncio.sleep)
- [ ] Unit test: fallback chain with 3 models, all fail
- [ ] Unit test: PromptTemplateManager renders template correctly
- [ ] Unit test: PromptTemplateManager throws error on missing template
- [ ] Integration test: AssessmentEngine uses templates + settings
- [ ] Manual test: verify real AI calls with new parameters

### Code Review

- [ ] Code complies with PEP 8 and Ruff passes without errors
- [ ] Type hints added everywhere (mypy passes)
- [ ] Docstrings in Google style for all new classes/methods
- [ ] No hardcoded temperature/max_tokens in `assessment_engine.py`
- [ ] Structured logging with context (attempt, delay, model)

### Performance

- [ ] Fallback chain with primary model success: latency < 5s
- [ ] Fallback chain with 2 attempts: latency ~1s + model latency
- [ ] Template rendering: < 1ms per template

---

## IMPLEMENTATION PLAN

### Phase 1: Implement Exponential Backoff in OpenRouter Client

**Description**: Add exponential backoff logic to the `call_with_fallback()` method

**Tasks**:
- [ ] Modify `openrouter_client.py::call_with_fallback()`
  - Add attempt counter (enumerate)
  - Insert `await asyncio.sleep(2 ** attempt)` between attempts
  - Add logging of attempt, model, delay
- [ ] Create unit test `tests/ai/test_openrouter_client.py::test_exponential_backoff_on_failure`
  - Mock `call_model()` to return error on first attempt
  - Mock `asyncio.sleep()` to track delays
  - Assert: delay 1s before fallback
- [ ] Create unit test `test_all_models_fail_with_backoff`
  - All models return error
  - Assert: delays 1s, 2s, 4s
  - Assert: final error raised

**Validation**:
- ✅ Ruff and mypy pass without errors
- ✅ Tests pass (pytest -v tests/ai/test_openrouter_client.py)
- ✅ Coverage for `call_with_fallback()` >= 90%

---

### Phase 2: Create Prompt Template Manager

**Description**: Implement a class for managing prompt templates

**Tasks**:
- [ ] Create file `src/promptheus/ai/prompt_template_manager.py`
- [ ] Implement `PromptTemplateManager` class:
  - `__init__()`: initialize empty dict of templates
  - `register_template(name: str, template: str)`: add template
  - `render(name: str, **variables) -> str`: render with variables
  - `get_template(name: str) -> str`: get raw template
- [ ] Define templates (in same file as constants):
  - `ASSESSMENT_EVALUATION_TEMPLATE`: for evaluating answers
  - `EXERCISE_FEEDBACK_TEMPLATE`: for exercise feedback
  - `IMPROVED_PROMPT_TEMPLATE`: for generating improved prompt
- [ ] Create unit tests `tests/ai/test_prompt_template_manager.py`:
  - `test_register_and_render_template`: basic rendering
  - `test_render_with_multiple_variables`: multiple variables
  - `test_render_missing_template_raises_error`: error on missing template
  - `test_render_missing_variable_raises_error`: error on missing variable

**Validation**:
- ✅ Class `PromptTemplateManager` created and documented
- ✅ 3+ templates registered
- ✅ Tests cover main cases (>80% coverage)
- ✅ Mypy passes without errors

---

### Phase 3: Integrate Template Manager in Assessment Engine

**Description**: Update `AssessmentEngine` to use templates instead of hardcode

**Tasks**:
- [ ] Update `src/promptheus/core/assessment_engine.py`:
  - Add `PromptTemplateManager` to constructor (DI)
  - Replace hardcoded prompts with `template_manager.render()`
  - In `evaluate_answers()`: use "assessment_evaluation" template
  - For feedback generation: use "exercise_feedback"
- [ ] Update `DependencyContainer` to inject `PromptTemplateManager`:
  - In `initialize()`: create `PromptTemplateManager` instance
  - Register all templates
  - Pass to `AssessmentEngine` on creation
- [ ] Update tests `tests/core/test_assessment_engine.py`:
  - Mock `PromptTemplateManager` in fixtures
  - Verify `template_manager.render()` calls with correct variables

**Validation**:
- ✅ `AssessmentEngine` uses `PromptTemplateManager`
- ✅ No hardcoded prompts in methods
- ✅ Tests pass with updated mocks
- ✅ Coverage >= 80%

---

### Phase 4: Use Settings for Temperature and Max Tokens

**Description**: Replace hardcoded values with parameters from `Settings`

**Tasks**:
- [ ] Update `src/promptheus/core/assessment_engine.py`:
  - In `__init__()`: save `settings = get_settings()`
  - In all `ai_client.call_with_fallback()` calls:
    - Replace `temperature=0.3` with `self.settings.temperature_assessment`
    - Replace `max_tokens=512` with `self.settings.max_tokens_feedback`
- [ ] Update `src/promptheus/ai/openrouter_client.py` (if defaults exist):
  - In `call_model()`: use `settings.temperature_default`
- [ ] Check all files for hardcoding:
  - `grep -r "temperature=[0-9]" src/`
  - `grep -r "max_tokens=[0-9]" src/`
- [ ] Update tests:
  - Mock `get_settings()` in tests
  - Verify correct parameter passing from settings

**Validation**:
- ✅ No hardcoded temperature/max_tokens in code
- ✅ Grep finds no patterns `temperature=0.` or `max_tokens=`
- ✅ Tests pass with mocked settings
- ✅ Manual verification: settings.py changes affect AI calls

---

### Phase 5: Update Documentation and Final Validation

**Description**: Update comments and conduct E2E verification

**Tasks**:
- [ ] Update docstrings:
  - `OpenRouterClient.call_with_fallback()`: mention exponential backoff
  - `PromptTemplateManager`: usage examples
  - `AssessmentEngine`: mention template use
- [ ] Create usage example in comments:
  ```python
  # Example: Using PromptTemplateManager
  manager = PromptTemplateManager()
  manager.register_template("greeting", "Hello, {name}!")
  result = manager.render("greeting", name="Alice")
  ```
- [ ] Conduct manual E2E test:
  - Run bot locally
  - Go through onboarding → assessment → lesson → exercise
  - Check logs for correct fallback chain usage
  - Verify AI parameters from settings are applied
- [ ] Update CHANGELOG.md:
  ```markdown
  ## [Unreleased]
  ### Fixed
  - Added exponential backoff (1s, 2s, 4s) to AI model fallback chain
  - Centralized prompt templates in PromptTemplateManager
  - Replaced hardcoded AI parameters with Settings configuration
  ```

**Validation**:
- ✅ Docstrings updated and clear
- ✅ Manual E2E test passed
- ✅ CHANGELOG.md updated
- ✅ No TODO/FIXME comments in changed code

---

## TESTING AND VALIDATION

### Unit Tests

#### Exponential Backoff Tests

```python
# tests/ai/test_openrouter_client.py
import pytest
from unittest.mock import AsyncMock, patch
from promptheus.ai.openrouter_client import OpenRouterClient

@pytest.mark.asyncio
async def test_exponential_backoff_on_primary_failure():
    """Test exponential backoff when primary model fails."""
    # Given
    client = OpenRouterClient()
    models = ["primary", "fallback", "alternative"]
    
    # Mock call_model to fail on first attempt, succeed on second
    call_count = 0
    async def mock_call_model(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise Exception("Primary model failed")
        return {"choices": [{"message": {"content": "Success"}}]}
    
    client.call_model = AsyncMock(side_effect=mock_call_model)
    
    # Mock asyncio.sleep to track delays
    with patch("asyncio.sleep") as mock_sleep:
        # When
        result = await client.call_with_fallback(
            prompt="test",
            models=models
        )
        
        # Then
        assert call_count == 2  # Primary failed, fallback succeeded
        assert mock_sleep.call_count == 1  # One delay between attempts
        mock_sleep.assert_called_once_with(1)  # 2^0 = 1 second
        assert result["choices"][0]["message"]["content"] == "Success"

@pytest.mark.asyncio
async def test_all_models_fail_with_correct_delays():
    """Test exponential backoff when all models fail."""
    # Given
    client = OpenRouterClient()
    models = ["primary", "fallback", "alternative"]
    
    client.call_model = AsyncMock(side_effect=Exception("All models failed"))
    
    # When / Then
    with patch("asyncio.sleep") as mock_sleep:
        with pytest.raises(Exception, match="All models failed"):
            await client.call_with_fallback(prompt="test", models=models)
        
        # Assert delays: 1s (after primary), 2s (after fallback)
        assert mock_sleep.call_count == 2
        calls = [call.args[0] for call in mock_sleep.call_args_list]
        assert calls == [1, 2]  # 2^0, 2^1
```

#### Prompt Template Manager Tests

```python
# tests/ai/test_prompt_template_manager.py
import pytest
from promptheus.ai.prompt_template_manager import PromptTemplateManager

def test_register_and_render_template():
    """Test basic template registration and rendering."""
    # Given
    manager = PromptTemplateManager()
    template = "Hello, {name}! You are {age} years old."
    
    # When
    manager.register_template("greeting", template)
    result = manager.render("greeting", name="Alice", age=30)
    
    # Then
    assert result == "Hello, Alice! You are 30 years old."

def test_render_missing_template_raises_error():
    """Test error when rendering non-existent template."""
    # Given
    manager = PromptTemplateManager()
    
    # When / Then
    with pytest.raises(ValueError, match="Template 'nonexistent' not found"):
        manager.render("nonexistent", name="Alice")

def test_render_missing_variable_raises_error():
    """Test error when variable is missing."""
    # Given
    manager = PromptTemplateManager()
    manager.register_template("greeting", "Hello, {name}!")
    
    # When / Then
    with pytest.raises(KeyError):
        manager.render("greeting")  # Missing 'name' variable
```

#### Assessment Engine Tests (Updated)

```python
# tests/core/test_assessment_engine.py
import pytest
from unittest.mock import AsyncMock, Mock
from promptheus.core.assessment_engine import AssessmentEngine
from promptheus.ai.prompt_template_manager import PromptTemplateManager
from promptheus.config import get_settings

@pytest.mark.asyncio
async def test_evaluate_answers_uses_template_and_settings():
    """Test that evaluate_answers uses template manager and settings."""
    # Given
    mock_ai_client = AsyncMock()
    mock_ai_client.call_with_fallback.return_value = {
        "choices": [{"message": {"content": '{"score": 85}'}}]
    }
    
    mock_template_manager = Mock(spec=PromptTemplateManager)
    mock_template_manager.render.return_value = "Rendered prompt with variables"
    
    settings = get_settings()
    
    engine = AssessmentEngine(
        ai_client=mock_ai_client,
        template_manager=mock_template_manager
    )
    
    # When
    result = await engine.evaluate_answers(
        answers=["answer1", "answer2"],
        user_id=123
    )
    
    # Then
    # Assert template was rendered with correct variables
    mock_template_manager.render.assert_called_once()
    call_kwargs = mock_template_manager.render.call_args.kwargs
    assert "skill_level" in call_kwargs
    assert "user_prompt" in call_kwargs
    
    # Assert AI client called with settings parameters
    mock_ai_client.call_with_fallback.assert_called_once()
    ai_call_kwargs = mock_ai_client.call_with_fallback.call_args.kwargs
    assert ai_call_kwargs["temperature"] == settings.temperature_feedback
    assert ai_call_kwargs["max_tokens"] == settings.max_tokens_feedback
```

### Commands to Run

```bash
# Run all tests for modified components
pytest tests/ai/test_openrouter_client.py -v
pytest tests/ai/test_prompt_template_manager.py -v
pytest tests/core/test_assessment_engine.py -v

# With coverage
pytest tests/ai/ --cov=src/promptheus/ai --cov-report=term-missing
pytest tests/core/test_assessment_engine.py --cov=src/promptheus/core/assessment_engine --cov-report=term-missing

# Linter and type checking
ruff check src/promptheus/ai/
ruff check src/promptheus/core/assessment_engine.py
mypy src/promptheus/ai/
mypy src/promptheus/core/assessment_engine.py

# Check for hardcoding (should return empty)
grep -r "temperature=[0-9]" src/promptheus/
grep -r "max_tokens=[0-9]" src/promptheus/
```

### Manual Testing Scenarios

**1. E2E test fallback chain**
- Run bot: `python -m src.promptheus.main`
- Go through onboarding to exercise
- Submit prompt for evaluation
- Check logs:
  - If primary model succeeds: one call without fallback
  - If primary unavailable: logging of attempts with delays

**2. Check prompt templates**
- Go through assessment questions
- Verify prompts are personalized (mention skill_level, learning_goal)
- Change template in `PromptTemplateManager` (add emoji)
- Restart bot, verify changes in AI responses

**3. Check settings for AI parameters**
- Change `settings.py`: `temperature_feedback = 0.1`
- Restart bot
- Submit prompt for evaluation
- Expected: more deterministic, less creative answer
- Return to `0.5`, repeat - answer should be more varied

---

## ADDITIONAL CONSIDERATIONS

### Risks

**Risk 1: Exponential backoff will increase latency during frequent failures**
- **Mitigation**: Limit maximum attempts to 3 models, maximum delay 4s
- **Alternative**: If > 50% requests use fallback, reconsider primary model choice

**Risk 2: Template Manager will complicate prompt debugging**
- **Mitigation**: Log full rendered prompt before sending to AI
- **Tool**: Add debug endpoint for viewing templates

**Risk 3: Changing temperature/max_tokens may degrade answer quality**
- **Mitigation**: Keep old values as defaults in `settings.py`
- **Testing**: A/B test several values before finalizing

### Assumptions

- OpenRouter API will have >95% uptime for primary model
- Exponential backoff is sufficient for 90%+ successful requests
- Users tolerate up to 10s latency for AI responses
- Templates will not change more than once per sprint

### Constraints

- Only 3 models in fallback chain (primary, fallback, alternative)
- Templates stored in memory (not in database) for MVP
- No support for complex Jinja2 logic (only `.format()`)
- Settings require bot restart to apply

### Future Improvements

- [ ] Adaptive fallback: model selection based on latency/cost
- [ ] Template versioning: A/B test templates with metrics
- [ ] Dynamic settings: change parameters without restart
- [ ] Circuit breaker: skip unavailable model for N minutes
- [ ] Prometheus metrics: fallback count, latency per model

---

## COMPLETION CHECKLIST

### Development

**Issue 5.1: Exponential Backoff**
- [ ] Modified `openrouter_client.py::call_with_fallback()`
- [ ] Added `await asyncio.sleep(2 ** attempt)` between attempts
- [ ] Logging of attempts, models, delays
- [ ] Import `asyncio` added to file

**Issue 5.2: Prompt Template Manager**
- [ ] Created `src/promptheus/ai/prompt_template_manager.py`
- [ ] Implemented `PromptTemplateManager` class
- [ ] 3+ templates registered in constants
- [ ] Methods `register_template()`, `render()`, `get_template()` work
- [ ] DependencyContainer updated to inject `PromptTemplateManager`
- [ ] AssessmentEngine uses templates instead of hardcode

**Issue 5.3: Settings for AI Parameters**
- [ ] `assessment_engine.py` uses `settings.temperature_*`
- [ ] `assessment_engine.py` uses `settings.max_tokens_*`
- [ ] No hardcoded values in code (grep verification)
- [ ] Settings correctly passed to `ai_client.call_with_fallback()`

### Testing

**Unit Tests**
- [ ] `test_exponential_backoff_on_primary_failure` passes
- [ ] `test_all_models_fail_with_correct_delays` passes
- [ ] `test_register_and_render_template` passes
- [ ] `test_render_missing_template_raises_error` passes
- [ ] `test_evaluate_answers_uses_template_and_settings` passes
- [ ] Coverage >= 80% for modified files

**Integration Tests**
- [ ] E2E test: onboarding → assessment → exercise with real AI
- [ ] Check logs for correct fallback chain on primary failure
- [ ] Verify prompt personalization through templates
- [ ] Verify settings impact on AI responses (temperature)

### Documentation

- [ ] Docstrings added/updated for new methods
- [ ] Comments on complex code sections (exponential backoff)
- [ ] CHANGELOG.md updated (Fixed section)
- [ ] README updated if needed for settings

### Code Quality

- [ ] Ruff passes: `ruff check src/`
- [ ] Mypy passes: `mypy src/`
- [ ] Type hints everywhere (all public methods)
- [ ] No TODO/FIXME in commits
- [ ] Code review passed (if required)

### Finalization

- [ ] All tests pass: `pytest tests/ -v`
- [ ] Coverage >= 80%: `pytest --cov`
- [ ] Clear commit messages:
  - `fix(ai): add exponential backoff to fallback chain`
  - `feat(ai): implement PromptTemplateManager for centralized prompts`
  - `fix(core): use Settings for AI temperature and max_tokens`
- [ ] Pull request created (if required)
- [ ] Manual E2E test passed

---

## SUCCESS METRICS

### Technical Metrics

- ✅ Exponential backoff applied correctly (delays: 1s, 2s, 4s)
- ✅ 3+ templates migrated to `PromptTemplateManager`
- ✅ 0 hardcoded temperature/max_tokens values in code
- ✅ Test coverage >= 80% for modified components
- ✅ All tests pass (unit + integration)

### Quality Metrics

- ✅ Code complies with architectural documentation (SAD, TRD)
- ✅ Logs show correct fallback behavior
- ✅ Prompts easily changed through `PromptTemplateManager`
- ✅ AI parameters easily tuned through `settings.py`

### Business Metrics (after deployment)

- AI API error rate reduced by 20%+ (due to backoff)
- Prompt iteration time cut in half (no need to modify code)
- 0 critical AI integration bugs in first week

---

**Responsible Developer:** TBD  
**Reviewer:** TBD  
**Estimated Completion:** 6-8 hours  
**Actual Completion:** TBD

**Document Version:** 1.0.0  
**Date Created:** 2025-11-06  
**Based on:** `docs/ai-agent-task-template.md` v1.0.0
