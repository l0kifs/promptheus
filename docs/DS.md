# Development Standards (DS)
## Promptheus - Telegram Bot for Prompt Engineering Education

**Version:** 1.0.0  
**Last Updated:** 2025-10-31

---

## 1. Code Style & Formatting

### 1.1 Python Version
- **Required:** Python 3.11+
- **Rationale:** Modern type hints, performance improvements, async enhancements

### 1.2 Formatter & Linter
- **Tool:** Ruff (replaces Black, isort, flake8, pylint)
- **Configuration:** `pyproject.toml`
- **Line Length:** 100 characters
- **Quote Style:** Double quotes

### 1.3 Type Hints
- **Required:** All public functions, methods, class attributes
- **Tools:** mypy for static type checking
- **Style:** Python 3.11+ syntax (`list[str]`, `dict[str, int]`)

```python
# ✅ Correct
def get_user_progress(user_id: int) -> list[UserProgress]:
    """Retrieve all progress records for a user."""
    return progress_repo.find_by_user(user_id)

# ❌ Wrong
def get_user_progress(user_id):
    return progress_repo.find_by_user(user_id)
```

---

## 2. Naming Conventions

### 2.1 General Rules
- **Language:** English for all names (code, comments, docs)
- **Style:** Clear, descriptive, no abbreviations (except standard ones)
- **Consistency:** Follow existing patterns in codebase

### 2.2 Files & Modules
- **Pattern:** `snake_case.py`
- **Location:** Match layer structure

```
✅ Correct:
- bot_handler.py
- learning_flow_orchestrator.py
- openrouter_client.py

❌ Wrong:
- BotHandler.py
- learningFlowOrchestrator.py
- OR_client.py
```

### 2.3 Classes
- **Pattern:** `PascalCase`
- **Suffixes:** Descriptive role indicators

```python
# ✅ Correct
class UserRepository:
class AssessmentEngine:
class OpenRouterClient:
class MessageFormatter:

# ❌ Wrong
class user_repository:
class Assessment:  # Too vague
class ORClient:  # Cryptic abbreviation
```

### 2.4 Functions & Methods
- **Pattern:** `snake_case`
- **Verbs:** Start with action verbs
- **Boolean:** Prefix with `is_`, `has_`, `can_`, `should_`

```python
# ✅ Correct
def calculate_assessment_score(answers: list[bool]) -> int:
def is_lesson_completed(user_id: int, lesson_id: int) -> bool:
def format_theory_message(content: TheoryContent) -> str:

# ❌ Wrong
def calcScore(answers):  # camelCase
def completed(user_id, lesson_id):  # Unclear verb
def format(content):  # Too generic
```

### 2.5 Variables
- **Pattern:** `snake_case`
- **Constants:** `UPPER_SNAKE_CASE` (module level)
- **Private:** Prefix with `_` (single underscore)

```python
# ✅ Correct
user_progress = repo.get_progress(user_id)
MAX_RETRY_ATTEMPTS = 3
_internal_cache = {}

# ❌ Wrong
userProgress = repo.get_progress(user_id)
max_retry_attempts = 3  # Not constant
__cache = {}  # Double underscore reserved for name mangling
```

### 2.6 Database Tables & Columns
- **Tables:** `snake_case` (match SQLAlchemy model names)
- **Columns:** `snake_case`
- **Foreign Keys:** `{referenced_table}_id`

```python
# ✅ Correct
class User(Base):
    __tablename__ = "user"
    telegram_id = Column(BigInteger, primary_key=True)
    current_lesson_id = Column(Integer, ForeignKey("lesson.id"))

# ❌ Wrong
class User(Base):
    __tablename__ = "Users"  # PascalCase
    telegramID = Column(BigInteger)  # camelCase
    lesson = Column(Integer)  # Unclear FK
```

---

## 3. Architecture Patterns

### 3.1 Layered Architecture
- **Layers:** Bot Interface → Application Core → Integration/Data Access
- **Rule:** Dependencies flow downward only
- **Violation:** Never import from upper layers

```python
# ✅ Correct (Bot Interface imports Application Core)
from promptheus.core.learning_flow import LearningFlowOrchestrator

# ❌ Wrong (Data Access imports Application Core)
# Data layer should not know about core logic
```

### 3.2 Repository Pattern
- **Purpose:** Abstract database operations
- **Naming:** `{Entity}Repository`
- **Methods:** CRUD verbs (`create`, `find`, `update`, `delete`)

```python
# ✅ Correct
class UserRepository:
    def find_by_telegram_id(self, telegram_id: int) -> User | None:
    def create(self, user: User) -> User:
    def update_skill_level(self, user_id: int, level: SkillLevel) -> None:

# ❌ Wrong
class UserDB:  # Vague naming
    def get(self, id):  # Ambiguous
    def save(self, user):  # Too generic
```

### 3.3 Dependency Injection
- **Pattern:** Constructor injection for dependencies
- **Avoid:** Global state, singletons (except config)

```python
# ✅ Correct
class AssessmentEngine:
    def __init__(
        self,
        ai_client: OpenRouterClient,
        user_repo: UserRepository
    ):
        self._ai_client = ai_client
        self._user_repo = user_repo

# ❌ Wrong
class AssessmentEngine:
    def __init__(self):
        self._ai_client = OpenRouterClient()  # Hard dependency
        global user_repo  # Global state
```

---

## 4. Code Quality Standards

### 4.1 SOLID Principles
- **S**ingle Responsibility: One class/function = one purpose
- **O**pen/Closed: Extend behavior via inheritance/composition
- **L**iskov Substitution: Subtypes must be substitutable
- **I**nterface Segregation: Small, focused interfaces
- **D**ependency Inversion: Depend on abstractions, not concretions

### 4.2 Simplicity (KISS & YAGNI)
- **KISS:** Simplest solution that meets requirements
- **YAGNI:** Implement only what's needed now
- **DRY:** Avoid duplication, extract common logic

```python
# ✅ Correct (Simple, direct)
def is_lesson_completed(status: LessonStatus) -> bool:
    return status == LessonStatus.COMPLETED

# ❌ Wrong (Over-engineered)
class LessonStatusChecker:
    def __init__(self, strategy: CompletionStrategy):
        self._strategy = strategy
    
    def check(self, status: LessonStatus) -> bool:
        return self._strategy.evaluate(status)
```

### 4.3 Error Handling
- **Required:** Validate input at layer boundaries
- **Pattern:** Raise domain-specific exceptions
- **Logging:** Use structured logging with context

```python
# ✅ Correct
class InvalidSkillLevelError(ValueError):
    """Raised when skill level is not valid."""

def set_skill_level(user: User, level: str) -> None:
    if level not in ["beginner", "intermediate", "advanced"]:
        raise InvalidSkillLevelError(f"Invalid level: {level}")
    user.skill_level = level

# ❌ Wrong
def set_skill_level(user, level):
    user.skill_level = level  # No validation
```

---

## 5. Asynchronous Code

### 5.1 Async/Await Pattern
- **Usage:** I/O-bound operations (API calls, database queries)
- **Naming:** No special prefix needed
- **Consistency:** All layers async or provide async wrappers

```python
# ✅ Correct
async def fetch_lesson_content(lesson_id: int) -> LessonContent:
    """Fetch lesson content from database."""
    async with db_session() as session:
        return await lesson_repo.find_by_id(session, lesson_id)

# ❌ Wrong
async def async_fetch_lesson(id):  # Redundant prefix
    return lesson_repo.find_by_id(id)  # Forgot await
```

### 5.2 Error Handling in Async
- **Pattern:** Try-except within async functions
- **Timeout:** Set reasonable timeouts for external calls
- **Cleanup:** Use `async with` for resource management

```python
# ✅ Correct
async def call_ai_api(prompt: str) -> str:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(API_URL, json={"prompt": prompt})
            response.raise_for_status()
            return response.json()["text"]
    except httpx.TimeoutException:
        logger.warning("AI API timeout", prompt=prompt[:50])
        raise AIServiceUnavailableError("Request timed out")
    except httpx.HTTPStatusError as e:
        logger.error("AI API error", status=e.response.status_code)
        raise
```

---

## 6. Documentation Standards

### 6.1 Docstrings
- **Required:** All public classes, functions, methods
- **Format:** Google-style docstrings
- **Content:** Purpose, parameters, returns, raises

```python
# ✅ Correct
def calculate_assessment_score(answers: list[bool]) -> int:
    """Calculate user skill level score based on assessment answers.
    
    Args:
        answers: List of boolean answers to assessment questions.
    
    Returns:
        Score from 0 to 100, where 0 is beginner, 100 is advanced.
    
    Raises:
        ValueError: If answers list is empty.
    """
    if not answers:
        raise ValueError("Answers list cannot be empty")
    return int(sum(answers) / len(answers) * 100)
```

### 6.2 Comments
- **Usage:** Explain WHY, not WHAT
- **Avoid:** Obvious comments, commented-out code
- **TODO:** Use `# TODO:` for future improvements

```python
# ✅ Correct
# Use exponential backoff to avoid overwhelming the API during outages
retry_delay = 2 ** attempt

# ❌ Wrong
# Set retry_delay to 2 to the power of attempt
retry_delay = 2 ** attempt
```

### 6.3 Type Hints as Documentation
- **Philosophy:** Type hints reduce need for comments
- **Complex types:** Use `TypeAlias` for readability

```python
# ✅ Correct
from typing import TypeAlias

UserId: TypeAlias = int
ProgressMap: TypeAlias = dict[int, list[UserProgress]]

def get_all_progress(user_ids: list[UserId]) -> ProgressMap:
    """Get progress for multiple users."""
    ...
```

---

## 7. Testing Standards

### 7.1 Test Structure
- **Framework:** pytest
- **Location:** `tests/` directory (mirrors `src/` structure)
- **Naming:** `test_{function_name}.py`, `test_{function_name}_{scenario}`

```
src/
  promptheus/
    core/
      assessment_engine.py
tests/
  core/
    test_assessment_engine.py
```

### 7.2 Test Naming
- **Pattern:** `test_{what}_{condition}_{expected}`
- **Descriptive:** Should read like a specification

```python
# ✅ Correct
def test_calculate_score_with_all_correct_answers_returns_100():
def test_calculate_score_with_empty_list_raises_value_error():
def test_is_lesson_completed_with_in_progress_status_returns_false():

# ❌ Wrong
def test_score():  # Too vague
def test_1():  # Meaningless
def testCalculateScore():  # Wrong convention
```

### 7.3 Test Coverage
- **Target:** >80% for business logic
- **Required:** All public API endpoints, critical paths
- **Mocking:** Mock external dependencies (API, database)

```python
# ✅ Correct
@pytest.mark.asyncio
async def test_fetch_user_progress_returns_sorted_by_lesson_order():
    # Arrange
    user_id = 12345
    expected_progress = [
        UserProgress(lesson_id=1, status=LessonStatus.COMPLETED),
        UserProgress(lesson_id=2, status=LessonStatus.IN_PROGRESS),
    ]
    mock_repo = Mock(spec=ProgressRepository)
    mock_repo.find_by_user.return_value = expected_progress
    
    # Act
    result = await fetch_user_progress(user_id, mock_repo)
    
    # Assert
    assert result == expected_progress
    mock_repo.find_by_user.assert_called_once_with(user_id)
```

---

## 8. Configuration Management

### 8.1 Environment Variables
- **Tool:** python-dotenv + Pydantic Settings
- **Naming:** `UPPER_SNAKE_CASE`
- **Required:** Never hardcode secrets

```python
# ✅ Correct
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    telegram_bot_token: str
    openrouter_api_key: str
    database_url: str
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"

# ❌ Wrong
TELEGRAM_TOKEN = "123456:ABC-DEF..."  # Hardcoded secret
```

### 8.2 Configuration Validation
- **Pattern:** Validate on app startup
- **Fail fast:** Exit if critical config missing

```python
# ✅ Correct
def init_app() -> None:
    """Initialize application with validated configuration."""
    try:
        settings = Settings()
    except ValidationError as e:
        logger.critical("Configuration error", error=str(e))
        sys.exit(1)
```

---

## 9. Logging Standards

### 9.1 Logging Tool
- **Library:** loguru
- **Format:** Structured logging with context
- **Levels:** DEBUG < INFO < WARNING < ERROR < CRITICAL

### 9.2 Logging Guidelines
- **Context:** Include relevant identifiers (user_id, lesson_id)
- **Sensitive data:** Never log secrets, PII
- **Performance:** Use appropriate log levels

```python
# ✅ Correct
logger.info("User completed lesson", user_id=user_id, lesson_id=lesson_id)
logger.warning("API fallback triggered", model="primary", error=str(e))
logger.error("Database connection failed", attempt=retry_count)

# ❌ Wrong
logger.info(f"User {user_id} completed lesson {lesson_id}")  # String formatting
logger.debug("Some info")  # Vague message
logger.error(f"Token: {api_token}")  # Logging secrets
```

---

## 10. Git Workflow

### 10.1 Commit Standards
- **Format:** Conventional Commits (see `git-commit-rules.md`)
- **Principle:** One commit = one logical change
- **Message:** Clear, imperative mood, ≤50 chars

```bash
# ✅ Correct
git commit -m "feat(auth): add password reset functionality"
git commit -m "fix(api): resolve race condition in token refresh"
git commit -m "docs(readme): update installation instructions"

# ❌ Wrong
git commit -m "updates"
git commit -m "Fixed stuff and added things"
git commit -m "feat: implement feature and fix bugs and update docs"
```

### 10.2 Branch Strategy
- **Main branches:** `main` (production), `develop` (integration)
- **Feature branches:** `feature/{issue-number}-{short-description}`
- **Bug fixes:** `fix/{issue-number}-{short-description}`
- **Naming:** `kebab-case`, descriptive

```bash
# ✅ Correct
feature/123-add-assessment-engine
fix/456-resolve-database-timeout
docs/789-update-api-documentation

# ❌ Wrong
feature_123  # Snake case
feature  # No description
AddAssessmentEngine  # PascalCase
```

---

## 11. Code Review Checklist

### 11.1 Before Submitting PR
- [ ] Code follows naming conventions
- [ ] All functions have type hints and docstrings
- [ ] Tests added for new functionality (>80% coverage)
- [ ] No hardcoded secrets or PII in logs
- [ ] Error handling implemented consistently
- [ ] Code is self-documenting (clear names, logical structure)
- [ ] Ruff and mypy pass without errors
- [ ] Commit messages follow Conventional Commits

### 11.2 Review Focus Areas
- **Architecture:** Does it follow layered architecture?
- **Simplicity:** Could it be simpler?
- **Error handling:** Are edge cases covered?
- **Testing:** Are tests meaningful and sufficient?
- **Documentation:** Is the code self-explanatory?

---

## 12. Anti-Patterns to Avoid

### 12.1 Common Mistakes
- ❌ **God Objects:** Classes with too many responsibilities
- ❌ **Magic Numbers:** Hardcoded values without constants
- ❌ **Deep Nesting:** >3 levels of indentation
- ❌ **Long Functions:** >50 lines (consider extraction)
- ❌ **Premature Optimization:** Optimize when needed, not before

### 12.2 Python-Specific
- ❌ **Mutable defaults:** `def func(items=[]):`
- ❌ **Bare except:** `except:` (use specific exceptions)
- ❌ **String concatenation in loops:** Use `join()`
- ❌ **Not using context managers:** Manual file close
- ❌ **Ignoring `None`:** Not checking for `None` returns

---

## 13. Quick Reference

### 13.1 Naming Summary
| Element | Convention | Example |
|---------|-----------|---------|
| Files/Modules | `snake_case` | `user_repository.py` |
| Classes | `PascalCase` | `AssessmentEngine` |
| Functions/Methods | `snake_case` | `calculate_score()` |
| Variables | `snake_case` | `user_progress` |
| Constants | `UPPER_SNAKE_CASE` | `MAX_RETRY_ATTEMPTS` |
| Private | `_snake_case` | `_internal_cache` |
| Type Aliases | `PascalCase` | `UserId` |

### 13.2 Tools Configuration
```toml
# pyproject.toml
[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP"]

[tool.mypy]
python_version = "3.11"
strict = true
warn_return_any = true
warn_unused_configs = true
```

---

## 14. References

- **Principles:** SOLID, KISS, DRY, YAGNI (see `development-rules.md`)
- **Commits:** Conventional Commits (see `git-commit-rules.md`)
- **Architecture:** Layered Architecture (see `SAD.md`)
- **Data Models:** SQLAlchemy patterns (see `DDD.md`)
- **API Integration:** OpenRouter, Telegram (see `TRD.md`)

---

**Document Responsibility:** Define coding standards and naming conventions for consistent, maintainable codebase. Does not cover architecture decisions (SAD), technical requirements (TRD), or database design (DDD).
