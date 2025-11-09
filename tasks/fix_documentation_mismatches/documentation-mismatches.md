# Discrepancies between documentation and implementation

> Analysis performed: 2025-11-04
>
> The document contains a list of inconsistencies between what is described in the documentation and what is actually implemented in the code.

---

## 1. Architecture and structure

### 1.1 Layered Architecture (SAD)

**Documentation (SAD §1, §2)**:
- Clear separation into layers: Bot Interface → Application Core → AI Integration / Data Access
- Dependency flow only downwards
- Stateless application design

**Implementation**:
- ✅ Layers are correctly separated
- ❌ **Violation**: `BotHandlers` directly uses `get_db()` instead of dependency injection
- ❌ **Violation**: Handlers create repositories inside methods, not via DI
- ⚠️ **Problem**: Not stateless - uses `context.user_data` to store state instead of DB

```python
# handlers.py - current implementation
with get_db() as db:
    user_repo = UserRepository(db)  # Created every time
    
# Should be via DI:
def __init__(self, db: Session, user_repo: UserRepository, ...):
    self.user_repo = user_repo
```

---

### 1.2 Repository Pattern (DS §3.2, SAD §2.4)

**Documentation (DS §3.2)**:
- Constructor injection for dependencies
- Avoid global state and singletons

**Implementation**:
- ✅ Repository pattern is applied correctly
- ❌ **Violation**: Repositories are created inside handlers instead of being injected
- ❌ **Violation**: `get_db()` is called in handlers instead of passing the session

```python
# Current approach
class BotHandlers:
    def __init__(self, ai_client: OpenRouterClient):
        self.ai_client = ai_client
        # No injection of repositories
        
    async def start_command(self, ...):
        with get_db() as db:  # New session every time
            user_repo = UserRepository(db)
```

---

## 2. Synchrony vs Asynchrony

### 2.1 Async/Await Pattern (DS §5, TRD §1.2)

**Documentation (DS §5.1, TRD §1.2)**:
- Async runtime: asyncio
- All layers async or with async wrappers

**Implementation**:
- ✅ Bot handlers are asynchronous
- ✅ AI client is asynchronous
- ❌ **Discrepancy**: Repositories are synchronous, although called from async context
- ❌ **Discrepancy**: SQLAlchemy used synchronously instead of async version

```python
# Repositories - synchronous
class UserRepository:
    def find_by_telegram_id(self, telegram_id: int) -> User | None:
        return self.db.query(User).filter(...).first()
        
# Called from async function without await
async def start_command(self, ...):
    with get_db() as db:  # Synchronous context manager
        user_repo = UserRepository(db)
        user = user_repo.find_by_telegram_id(user_id)  # No await
```

**Problem**: Blocking DB operations in the async event loop can cause delays.

---

## 3. Configuration and Settings

### 3.1 Model Configuration (TRD §5.2, §7.1)

**Documentation (TRD §5.2)**:
```
AI_MODEL_PRIMARY=meta-llama/llama-4-scout:free
AI_MODEL_FALLBACK=google/gemini-2.5-pro-exp:free
AI_MODEL_ALTERNATIVE=mistralai/mistral-small-3.1-24b-instruct:free
AI_MODEL_LIGHTWEIGHT=qwen/qwen2.5-vl-3b-instruct:free  # 4 models
```

**Implementation (settings.py)**:
```python
ai_model_primary: str = "meta-llama/llama-4-scout:free"
ai_model_fallback: str = "google/gemini-2.5-pro-exp:free"
ai_model_alternative: str = "mistralai/mistral-small-3.1-24b-instruct:free"
# ai_model_lightweight is missing - only 3 models
```

---

### 3.2 Webhook Configuration (TRD §7.1)

**Documentation (TRD §7.1)**:
```
WEBHOOK_URL=https://your-domain.com/webhook  # for webhook mode
```

**Implementation (settings.py)**:
- ❌ **Missing**: No `webhook_url` field in Settings
- ❌ **Missing**: No `webhook_secret` for validation

**main.py**:
```python
# Always polling, webhook not supported
await application.updater.start_polling(allowed_updates=Update.ALL_TYPES)
```

---

## 4. Database Schema

### 4.1 User Table (DDD §3.1)

**Documentation (DDD §3.1)**:
```sql
assessment_score INTEGER NULL, CHECK (0-100)  -- With range constraint
```

**Implementation (models.py)**:
```python
assessment_score = Column(Integer, nullable=True)
# No CHECK constraint on range 0-100
```

---

### 4.2 Lesson Table Indexes (DDD §3.2)

**Documentation (DDD §3.2)**:
```sql
UNIQUE INDEX: skill_level, order_index
GIN INDEX: tags (PostgreSQL only)
```

**Implementation (models.py)**:
```python
class Lesson(Base):
    skill_level = Column(Enum(SkillLevel), nullable=False, index=True)
    order_index = Column(Integer, nullable=False)
    # No composite UNIQUE INDEX on (skill_level, order_index)
    # No GIN INDEX on tags
```

**Problem**: There may be two lessons with the same order_index for one skill_level.

---

### 4.3 UserProgress Indexes (DDD §3.3)

**Documentation (DDD §3.3)**:
```sql
UNIQUE INDEX: user_id, lesson_id (one progress per user-lesson)
INDEX: user_id, status (for progress queries)
```

**Implementation**:
- ❌ **Missing**: No UNIQUE constraint on (user_id, lesson_id)
- ❌ **Missing**: No composite INDEX on (user_id, status)

**Problem**: Duplicates of progress records for the same user and lesson are possible.

---

### 4.4 Timestamps (DDD §5.1)

**Documentation (DDD §5.1)**:
- PostgreSQL: `TIMESTAMP WITH TIME ZONE`

**Implementation (models.py)**:
```python
created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
# Uses datetime.utcnow (naive datetime) instead of timezone-aware
```

**Problem**: When migrating to PostgreSQL, timezone issues may arise.

---

## 5. AI Integration

### 5.1 Fallback Chain (TRD §5.2, SAD §7.1)

**Documentation (SAD §7.1)**:
```
Primary → (exponential backoff) → Fallback → (exponential backoff) → Alternative
Backoff: 1s, 2s, 4s
```

**Implementation (openrouter_client.py)**:
```python
async def call_with_fallback(self, ...):
    for model in models:
        try:
            result = await self.call_model(...)
            return result
        except Exception:
            continue  # Immediately try next model, no backoff
```

❌ **Discrepancy**: No exponential backoff between attempts.

---

### 5.2 Prompt Templates (TRD §5.2, US §6.2)

**Documentation (US §6.2)**:
- Separate templates: assessment, feedback generation, example creation
- Stored in Prompt Template Manager
- Variables for personalization (skill_level, learning_goal)

**Implementation**:
```python
# assessment_engine.py
evaluation_prompt = f"""You are an expert..."""  # Hardcoded
```

❌ **Discrepancy**: Prompts are hardcoded in methods instead of a centralized manager.

---

### 5.3 Temperature & Token Settings (TRD §5.2)

**Documentation (TRD §5.2)**:
```
temperature_assessment: 0.3
temperature_feedback: 0.5
temperature_default: 0.7

max_tokens_assessment: 256
max_tokens_feedback: 512
max_tokens_default: 1024
```

**Implementation**:
- ✅ Settings exist in configuration
- ❌ **Not used**: Values are hardcoded in code:

```python
# assessment_engine.py
response = await self.ai_client.call_with_fallback(
    prompt=evaluation_prompt,
    max_tokens=512,  # Hardcoded instead of settings.max_tokens_feedback
    temperature=0.3,  # Hardcoded instead of settings.temperature_assessment
)
```

---

## 6. Onboarding & Assessment

### 6.1 Skill Level Calculation (TRD §2.1)

**Documentation (TRD §2.1)**:
- AI analyzes user responses and adapts content

**Implementation (assessment_engine.py)**:
```python
async def evaluate_answers(self, answers: list[str]) -> dict:
    # Simple count of correct answers, AI not used
    correct_count = sum(results)
    score = int((correct_count / total) * 100)
```

❌ **Discrepancy**: AI is not used for evaluation, only basic arithmetic.

---

### 6.2 Assessment Questions Count (US §1.2)

**Documentation (US §1.2)**:
- 5 multiple-choice questions

**Implementation**:
- ✅ Correct: 5 questions in `get_assessment_questions()`

---

## 7. Lesson Delivery

### 7.1 Content Chunking (TRD §3.3, UXD §2.1)

**Documentation (TRD §3.3, UXD §2.1)**:
- Theory: 50-80 words per message
- Split into 2-4 sequential messages if needed

**Implementation (handlers.py)**:
```python
theory_section = lesson_data["theory_content"]["sections"][section_index]
await query.edit_message_text(
    self.formatter.format_theory(theory_section["text"]),  # Whole text
    ...
)
```

❌ **Discrepancy**: Content is not split into parts, sent in full.

---

### 7.2 Lesson Progress Tracking (TRD §4.3)

**Documentation (DDD §3.3)**:
```
status: not_started → in_progress → completed
completed_at set when status changes to completed
```

**Implementation (progress_tracker.py)**:
```python
def start_lesson(self, user_id: int, lesson_id: int):
    progress = self.progress_repo.find_by_user_and_lesson(user_id, lesson_id)
    if not progress:
        self.progress_repo.create(user_id, lesson_id)  # status=IN_PROGRESS
```

✅ Correct, but:
- ❌ **Problem**: No automatic transition `not_started` → `in_progress`, it's created immediately as `in_progress`.

---

## 8. Practice & Feedback

### 8.1 Feedback Structure (UXD §3.3)

**Documentation (UXD §3.3)**:
```
Structured in 2-3 short messages:
1. Score message
2. Good points
3. Improved version
```

**Implementation**:
```python
# Feedback is sent as a single comprehensive message
# containing score, strengths, improvements, and improved version
feedback_text = "📝 *Your Prompt:*\n" + f"_{user_prompt}_\n\n" + f"🔍 *Score:* {score}/10\n\n" + ...

await loading_msg.edit_text(feedback_text, ...)
```

⚠️ **Accepted as-is**: Single message approach provides better UX by showing all feedback at once without message fragmentation.

---

### 8.2 Attempts Counter (DDD §3.3)

**Documentation (DDD §3.3)**:
```
attempts incremented on each exercise submission
```

**Implementation (handlers.py)**:
```python
# In text_message_handler when submitting a prompt:
# No call to progress_tracker.increment_attempts()
```

❌ **Discrepancy**: Attempts counter not incremented on each submission.

---

## 9. Navigation & UX

### 9.1 Resume Capability (TRD §2.2, US §4.2)

**Documentation (US §4.2)**:
- Continue from last checkpoint (specific section in lesson)
- Show "Welcome back!" with lesson and section

**Implementation**:
```python
# start_command - for returning user
keyboard = [
    [InlineKeyboardButton("▶️ Continue", callback_data="continue")],
]
```

⚠️ **Partially**: Button exists, but:
- No saving of exact lesson section
- `context_data` in UserSession is not used for resume
- Continue callback does not show which section was left off

---

### 9.2 Typing Indicators (UXD §4.3, TRD §7.2)

**Documentation (TRD §7.2)**:
```
Message typing delay: 0.5-1s between sequential messages
```

**Implementation**:
- ❌ **Missing**: No delays between messages
- ❌ **Missing**: No `send_chat_action(ChatAction.TYPING)`

---

### 9.3 Back Button (UXD §2.2)

**Documentation (UXD §2.2)**:
- "⬅️ Back" button always available

**Implementation**:
- ⚠️ **Partially**: Present in some places but not everywhere
- ❌ In assessment there is no Back button
- ❌ In lesson theory there is `theory_prev`, but not named "Back"

---

## 10. Session Management

### 10.1 Session State (DDD §3.4, SAD §4.1)

**Documentation (DDD §3.4)**:
```
context_data stores state-specific temporary data
updated_at refreshed on every interaction
Session expires after 15 minutes inactivity
```

**Implementation**:
- ✅ `context_data` JSON field exists
- ❌ **Not used**: State is stored in `context.user_data` (in-memory)
- ❌ **Not updated**: `updated_at` is not refreshed on each interaction
- ❌ **No cleanup**: No automatic cleanup of old sessions

```python
# handlers.py - uses Telegram context instead of DB
context.user_data["assessment_questions"] = questions
context.user_data["current_question"] = 0
# These data are not saved into UserSession.context_data
```

**Problem**: On bot restart the session is lost.

---

### 10.2 Session Cleanup (US §5.3, DDD §10.2)

**Documentation (US §5.3)**:
```
Daily task removes sessions with updated_at > 30 days
Only UserSession records deleted
UserProgress and core user data preserved
```

**Implementation**:
- ❌ **Missing**: No scheduled task for cleanup
- ❌ **Missing**: No logic to remove old sessions

---

## 11. Error Handling

### 11.1 Rate Limiting (TRD §3.1, US §5.2)

**Documentation (US §5.2)**:
```
Limit: 10 requests per minute per user
On exceeding: "⏸️ Too Many Requests" message
Wait time indicated (1 minute)
Limit applied at Bot Interface Layer level
```

**Implementation**:
- ✅ `rate_limit_requests: int = 10` in Settings
- ❌ **Not implemented**: No middleware for rate checks
- ❌ **Not implemented**: No message on exceeding limit

---

### 11.2 Error Handler (main.py)

**Documentation (TRD §8.1)**:
- User Errors → User-friendly message
- API Errors → Retry with fallback
- System Errors → Log + notify admin

**Implementation (handlers.py)**:
```python
async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error("Error occurred", error=str(context.error))
    # No user message sent
    # No distinction between error types
```

❌ **Discrepancy**: Minimal error handling, no messages to users.

---

## 12. Logging

### 12.1 Structured Logging (TRD §8.2, DS §9.1)

**Documentation (TRD §8.2)**:
```json
{
  "timestamp": "2025-11-01T12:00:00Z",
  "level": "INFO",
  "user_id": "123456789",
  "action": "lesson_completed",
  "lesson_id": "intro-to-prompting",
  "duration_ms": 245,
  "context": {}
}
```

**Implementation (main.py, repositories.py)**:
```python
logger.info("User created successfully", telegram_id=telegram_id)
# Good: uses kwargs
```

✅ **Partially correct**, but:
- ❌ No unified JSON format for all logs
- ❌ No `action` field everywhere
- ❌ No `duration_ms` for timing operations

---

### 12.2 Log Levels (TRD §8.2)

**Documentation (TRD §8.2)**:
- Development: DEBUG
- Production: WARNING

**Implementation (main.py)**:
```python
logger.add(
    sys.stderr,
    level=settings.log_level,  # Taken from config
    ...
)
logger.add(
    "logs/promptheus_{time}.log",
    level="DEBUG",  # Always DEBUG in file logs!
    ...
)
```

❌ **Discrepancy**: File logs are always DEBUG, even in production.

---

## 13. Testing

### 13.1 Test Coverage (TS §13.1)

**Documentation (TS §13.1)**:
- Test coverage >80% for business logic
- All public API endpoints covered
- Mock external dependencies

**Implementation**:
```bash
tests/
  conftest.py
  test_core.py
  test_repositories.py
```

❌ **Discrepancy**: Only 2 test files; coverage likely ~30%.

---

### 13.2 Test Structure (TS §7.1, §7.2)

**Documentation (TS §7.2)**:
```
tests/
  core/
    test_assessment_engine.py
  data/
    test_repositories.py
  bot/
    test_handlers.py
  ai/
    test_openrouter_client.py
```

**Implementation**:
```
tests/
  test_core.py  # One file for all core
  test_repositories.py  # One file for all repositories
```

❌ **Discrepancy**: Flat structure instead of layer-based hierarchy.

---

### 13.3 Test Naming (TS §7.2)

**Documentation (TS §7.2)**:
```python
def test_calculate_score_with_all_correct_answers_returns_100():
```

**Implementation** (need to check test_*.py):
- Not analyzed, but likely doesn't follow the pattern.

---

## 14. Deployment

### 14.1 Docker Support (DP §4.2)

**Documentation (DP §4.2)**:
```bash
docker compose build
docker compose up -d
```

**Implementation**:
- ❌ **Missing**: No `Dockerfile`
- ❌ **Missing**: No `docker-compose.yml`
- ❌ **Missing**: No `.dockerignore`

---

### 14.2 Health Check (DP §5.1)

**Documentation (DP §5.1)**:
```python
# GET /health
{
  "status": "healthy",
  "database": "connected",
  "telegram_api": "reachable",
  "openrouter_api": "reachable",
  "version": "0.1.0"
}
```

**Implementation**:
- ❌ **Missing**: No HTTP server for health check
- ❌ **Missing**: Polling mode does not provide HTTP endpoint

---

## 15. Naming Conventions

### 15.1 Variables (DS §2.5)

**Documentation (DS §2.5)**:
```python
# Constants: UPPER_SNAKE_CASE (module level)
MAX_RETRY_ATTEMPTS = 3
```

**Implementation (openrouter_client.py)**:
```python
class OpenRouterClient:
    def __init__(self):
        self.base_url = "https://openrouter.ai/api/v1"  # Lowercase
        self.timeout = 10.0
```

❌ **Discrepancy**: `BASE_URL` and `TIMEOUT` should be module-level constants.

---

### 15.2 Async Functions (DS §5.1)

**Documentation (DS §5.1)**:
- No special prefix needed for async functions

**Implementation**:
- ✅ Correct: no `async_` prefix in names

---

## 16. Code Quality

### 16.1 Dependency Injection (DS §3.3)

**Documentation (DS §3.3)**:
```python
# ✅ Correct
class AssessmentEngine:
    def __init__(self, ai_client: OpenRouterClient, user_repo: UserRepository):
        self._ai_client = ai_client
        self._user_repo = user_repo
```

**Implementation (assessment_engine.py)**:
```python
class AssessmentEngine:
    def __init__(self, ai_client: OpenRouterClient):
        self.ai_client = ai_client
    # No user_repo, repositories created in handlers
```

❌ **Discrepancy**: Not all dependencies are injected.

---

### 16.2 Error Messages (DS §4.3)

**Documentation (DS §4.3)**:
```python
class InvalidSkillLevelError(ValueError):
    """Raised when skill level is not valid."""
```

**Implementation**:
- ❌ **Missing**: No custom exceptions (InvalidSkillLevelError etc.)
- Standard exceptions used without context

---

## 17. Documentation

### 17.1 Docstrings (DS §6.1)

**Documentation (DS §6.1)**:
```python
def calculate_score(answers: list[bool]) -> int:
    """Calculate user skill level score.
    
    Args:
        answers: List of boolean answers.
    
    Returns:
        Score from 0 to 100.
    
    Raises:
        ValueError: If answers list is empty.
    """
```

**Implementation**:
```python
# repositories.py
def find_by_telegram_id(self, telegram_id: int) -> User | None:
    """Find user by telegram ID."""  # Only a short description
    logger.debug("Finding user...", telegram_id=telegram_id)
    ...
```

⚠️ **Partially**: Docstrings exist but not in full format (missing Args/Returns/Raises).

---

## Summary table of critical discrepancies

| Category         | Documentation         | Implementation         | Criticality |
| ---------------- | --------------------- | ---------------------- | ----------- |
| DI Pattern       | Constructor injection | Created inside methods | 🔴 High      |
| Async/Await      | All layers async      | Repositories sync      | 🔴 High      |
| Session State    | Persisted in DB       | In-memory context      | 🔴 High      |
| DB Constraints   | CHECK, UNIQUE indexes | Missing                | 🟡 Medium    |
| Fallback Chain   | Exponential backoff   | Immediate fallback     | 🟡 Medium    |
| Message Chunking | 50-80 words split     | Sent whole             | 🟡 Medium    |
| Rate Limiting    | 10 req/min            | Not implemented        | 🔴 High      |
| Error Handling   | Typed exceptions      | Generic exceptions     | 🟡 Medium    |
| Prompt Templates | Centralized manager   | Hardcoded strings      | 🟢 Low       |
| Docker           | Dockerfile + compose  | Missing                | 🔴 High      |
| Testing          | >80% coverage         | ~30% estimate          | 🟡 Medium    |
| Health Check     | HTTP endpoint         | Missing                | 🔴 High      |
| Logging          | JSON structured       | Partial structured     | 🟢 Low       |
| Webhook          | Supported             | Polling only           | 🟡 Medium    |

---

## Recommendations for fixes

### 1. Critical fixes (Blocking Release)

1. **Dependency Injection**
   - Refactor handlers to inject repositories
   - Remove `with get_db()` from handlers
   - Create a container for dependency management

2. **Session Persistence**
   - Store state in `UserSession.context_data` instead of `context.user_data`
   - Update `updated_at` on every interaction
   - Implement restore from DB on reconnect

3. **Rate Limiting**
   - Add middleware to check limits
   - Store request timestamps in Redis/DB
   - Show message on limit exceed

4. **Database Constraints**
   - Add UNIQUE on (user_id, lesson_id) in UserProgress
   - Add CHECK on score ranges
   - Add composite index (skill_level, order_index)

5. **Docker & Deployment**
   - Add Dockerfile
   - Add docker-compose.yml
   - Configure health check endpoint

### 2. Important improvements (Before Production)

1. **Async Repositories**
   - Migrate to SQLAlchemy async
   - Replace sync repositories with async ones

2. **Error Handling**
   - Create domain-specific exceptions
   - Add retry logic with exponential backoff
   - Improve error handler to send user messages

3. **Testing**
   - Increase coverage to >80%
   - Add integration and E2E tests
   - Structure `tests/` by layers

4. **Message Chunking**
   - Implement splitting of theory into 50-80 word chunks
   - Send multiple messages for feedback

### 3. Refactoring (Code Quality)

1. **Prompt Templates**
   - Create a PromptTemplateManager
   - Move prompts out of methods

2. **Settings Usage**
   - Use settings for temperature/max_tokens instead of hardcoded values
   - Add `webhook_url` to settings

3. **Logging**
   - Standardize JSON format
   - Add `duration_ms` for operations
   - Avoid logging sensitive data

4. **Naming**
   - Move constants to UPPER_CASE at module level
   - Improve docstrings to full Google style

---

**Conclusion**: The main architecture is correct, but there are critical gaps in implementation patterns (DI, async, session), DB constraints and production readiness features (rate limiting, docker, health checks).
