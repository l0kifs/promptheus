# Documentation-Implementation Mismatch Fixes Roadmap

> Created: 2025-11-04  
> Based on: documentation-mismatches.md
>
> Structured step-by-step plan to eliminate discrepancies between documentation and current implementation of the Promptheus project.

---

## 🎯 General Approach

The plan is divided into 4 phases with prioritization:
- **Phase 1 (Critical)**: Blocks production release
- **Phase 2 (High)**: Required for stable operation
- **Phase 3 (Medium)**: Code quality improvement
- **Phase 4 (Low)**: Refactoring and optimization

Each task is marked:
- 🔴 Critical - blocking issues
- 🟡 High - important improvements
- 🟢 Medium - code quality
- 🔵 Low - nice to have

---

## Phase 1: Critical Fixes (Blocks Production)

### 1.1 Database Constraints & Indexes 🔴

**Problems:**
- No UNIQUE constraint on (user_id, lesson_id) → progress duplicates
- No UNIQUE index on (skill_level, order_index) → lesson duplicates
- No CHECK constraints on score ranges
- No composite indexes for query optimization

**Action Plan:**

- [x] **Task 1.1.1**: Create Alembic migration to add constraints
  ```python
  # alembic/versions/xxxx_add_constraints.py
  # 1. Add UNIQUE constraint on UserProgress(user_id, lesson_id)
  # 2. Add UNIQUE constraint on Lesson(skill_level, order_index)
  # 3. Add CHECK constraint on User.assessment_score (0-100)
  # 4. Add CHECK constraint on UserProgress.last_score (0-100)
  ```
  
- [x] **Task 1.1.2**: Add composite indexes
  ```python
  # 1. INDEX on UserProgress(user_id, status) for fast progress queries
  # 2. INDEX on Lesson(skill_level, order_index) for sorting
  # 3. GIN INDEX on Lesson.tags (PostgreSQL only)
  ```

- [x] **Task 1.1.3**: Update models.py with declarative constraints
  ```python
  # models.py
  # Add __table_args__ for each model with constraints
  # Add CheckConstraint for score fields
  # Add UniqueConstraint for composite keys
  ```

- [x] **Task 1.1.4**: Write tests to verify constraints
  ```python
  # tests/data/test_constraints.py
  # Verify that duplicates raise IntegrityError
  # Verify that score outside range raises error
  ```

- [x] **Task 1.1.5**: Test migration on dev data
  ```bash
  # 1. Apply migration on test DB
  # 2. Verify existing data doesn't violate constraints
  # 3. Prepare cleanup script if needed
  ```

**Files to Modify:**
- `alembic/versions/xxxx_add_constraints.py` (new)
- `src/promptheus/data/models.py`
- `tests/data/test_constraints.py` (new)

**Acceptance Criteria:**
- ✅ All migrations apply without errors
- ✅ Tests pass
- ✅ Cannot create duplicate progress/lessons
- ✅ Score validation works

---

### 1.2 Session Persistence 🔴

**Problem:**
- State stored in `context.user_data` (in-memory)
- Bot restart loses entire session
- `UserSession.context_data` not used

**Action Plan:**

- [x] **Task 1.2.1**: Create SessionManager for DB operations
  ```python
  # src/promptheus/core/session_manager.py
  class SessionManager:
      def save_state(user_id, state_key, value)
      def get_state(user_id, state_key, default)
      def clear_state(user_id)
      def update_activity(user_id)  # Update updated_at
  ```

- [ ] **Task 1.2.2**: Refactor handlers to use SessionManager
  ```python
  # handlers.py
  # Replace all context.user_data["key"] with session_manager.save_state()
  # Replace all context.user_data.get() with session_manager.get_state()
  ```

- [ ] **Task 1.2.3**: Migrate assessment flow
  ```python
  # Rewrite assessment_questions → DB
  # Rewrite current_question → DB
  # Rewrite assessment_answers → DB
  ```

- [ ] **Task 1.2.4**: Migrate lesson flow
  ```python
  # Rewrite current_section → DB
  # Rewrite lesson_data cache → DB
  ```

- [ ] **Task 1.2.5**: Implement session restore
  ```python
  # Check DB session on handler start
  # Restore state if exists
  # Show "Continue from..." if interrupted
  ```

- [ ] **Task 1.2.6**: Add auto-update for updated_at
  ```python
  # Middleware or decorator to update timestamp
  # Update UserSession.updated_at on every interaction
  ```

- [ ] **Task 1.2.7**: Test session persistence
  ```python
  # tests/core/test_session_manager.py
  # Verify save/get state
  # Verify restore after restart
  # Verify timestamp updates
  ```

**Files to modify:**
- `src/promptheus/core/session_manager.py` (new)
- `src/promptheus/bot/handlers.py` (major refactoring)
- `src/promptheus/data/repositories.py` (update SessionRepository)
- `tests/core/test_session_manager.py` (new)

**Acceptance criteria:**
- ✅ No usage of `context.user_data`
- ✅ All state in DB
- ✅ Bot restart doesn't lose sessions
- ✅ Resume works correctly

---

### 1.3 Rate Limiting 🔴

**Problem:**
- No spam protection
- Settings.rate_limit_requests not used

**Action Plan:**

- [ ] **Task 1.3.1**: Create RateLimiter class
  ```python
  # src/promptheus/core/rate_limiter.py
  class RateLimiter:
      def check_limit(user_id) -> bool
      def record_request(user_id)
      def get_wait_time(user_id) -> int
  ```

- [ ] **Task 1.3.2**: Choose storage for rate limiting
  ```
  Options:
  1. In-memory dict (simple, for MVP)
  2. Redis (production-ready, but additional dependency)
  3. Database (works, but slower)
  
  Solution for MVP: In-memory with periodic cleanup
  ```

- [ ] **Task 1.3.3**: Implement in-memory rate limiter
  ```python
  # Use collections.deque for timestamps
  # Sliding window algorithm
  # Cleanup old entries every N minutes
  ```

- [ ] **Task 1.3.4**: Create middleware/decorator
  ```python
  # src/promptheus/bot/middleware.py
  def rate_limit(func):
      # Check limit before calling handler
      # If exceeded → send message to user
  ```

- [ ] **Task 1.3.5**: Apply to all handlers
  ```python
  # handlers.py
  @rate_limit
  async def start_command(self, update, context):
      ...
  ```

- [ ] **Task 1.3.6**: Format rate limit exceeded message
  ```python
  # message_formatter.py
  def format_rate_limit_exceeded(wait_seconds):
      return "⏸️ Too many requests. Wait {wait_seconds}s"
  ```

- [ ] **Task 1.3.7**: Test rate limiting
  ```python
  # tests/core/test_rate_limiter.py
  # Verify request counting
  # Verify blocking when exceeded
  # Verify reset after timeout
  ```

**Files to modify:**
- `src/promptheus/core/rate_limiter.py` (new)
- `src/promptheus/bot/middleware.py` (new)
- `src/promptheus/bot/handlers.py` (add decorator)
- `src/promptheus/bot/message_formatter.py` (new method)
- `tests/core/test_rate_limiter.py` (new)

**Acceptance criteria:**
- ✅ 10 req/min limit works
- ✅ Message shown when exceeded
- ✅ Limit resets after 1 minute
- ✅ Tests cover edge cases

---

### 1.4 Docker & Deployment 🔴

**Problem:**
- No containerization
- Cannot deploy in standard way

**Action Plan:**

- [ ] **Task 1.4.1**: Create Dockerfile
  ```dockerfile
  # Dockerfile
  # Multi-stage build
  # Stage 1: Builder (install dependencies)
  # Stage 2: Runtime (only prod dependencies)
  # Python 3.11 alpine or slim
  ```

- [ ] **Task 1.4.2**: Create .dockerignore
  ```
  # .dockerignore
  .git/
  __pycache__/
  *.pyc
  .env
  .venv/
  tests/
  docs/
  ```

- [ ] **Task 1.4.3**: Create docker-compose.yml
  ```yaml
  # docker-compose.yml
  # Services:
  #   - app (bot application)
  #   - db (PostgreSQL for production)
  # Volumes for persistence
  # Networks for isolation
  ```

- [ ] **Task 1.4.4**: Create docker-compose.dev.yml
  ```yaml
  # docker-compose.dev.yml
  # Override for development
  # Mount src/ for hot reload
  # SQLite instead of PostgreSQL
  # Debug logging
  ```

- [ ] **Task 1.4.5**: Update README with Docker instructions
  ```markdown
  # README.md
  ## Quick Start with Docker
  ## Development setup
  ## Production deployment
  ```

- [ ] **Task 1.4.6**: Add health check to Dockerfile
  ```dockerfile
  # HEALTHCHECK for Docker
  # Simple health check script
  ```

- [ ] **Task 1.4.7**: Test Docker build
  ```bash
  # 1. docker compose build
  # 2. docker compose up
  # 3. Verify bot works
  # 4. Verify persistence after restart
  ```

**Files to modify:**
- `Dockerfile` (new)
- `.dockerignore` (new)
- `docker-compose.yml` (new)
- `docker-compose.dev.yml` (new)
- `README.md` (update)
- `.env.example` (create if missing)

**Acceptance Criteria:**
- ✅ Docker image builds without errors
- ✅ docker-compose up starts the bot
- ✅ DB persists in a volume
- ✅ README contains full instructions

---

### 1.5 Health Check Endpoint 🔴

**Problem:**
- No way to check bot health from outside
- No monitoring for production

**Action Plan:**

- [ ] **Task 1.5.1**: Add aiohttp to dependencies
  ```toml
  # pyproject.toml
  dependencies = [
      "aiohttp>=3.9",
      ...
  ]
  ```

- [ ] **Task 1.5.2**: Create HTTP server for health checks
  ```python
  # src/promptheus/monitoring/health_server.py
  class HealthCheckServer:
      def __init__(self, port=8080)
      async def start()
      async def stop()
      async def handle_health(request)
  ```

- [ ] **Task 1.5.3**: Implement checks
  ```python
  # health_server.py
  async def check_database() -> bool
  async def check_telegram_api() -> bool
  async def check_openrouter_api() -> bool
  def get_version() -> str
  ```

- [ ] **Task 1.5.4**: Integrate into main.py
  ```python
  # main.py
  # Run health server in parallel with the bot
  # Graceful shutdown for both
  ```

- [ ] **Task 1.5.5**: Configure port via settings
  ```python
  # settings.py
  health_check_port: int = Field(default=8080)
  health_check_enabled: bool = Field(default=True)
  ```

- [ ] **Task 1.5.6**: Update Docker with health check
  ```dockerfile
  # Dockerfile
  HEALTHCHECK --interval=30s --timeout=3s \
    CMD curl -f http://localhost:8080/health || exit 1
  ```

- [ ] **Task 1.5.7**: Tests for health endpoint
  ```python
  # tests/monitoring/test_health_server.py
  # Verify response format
  # Verify status codes
  # Verify all checks
  ```

**Files to modify:**
- `src/promptheus/monitoring/__init__.py` (new)
- `src/promptheus/monitoring/health_server.py` (new)
- `src/promptheus/main.py` (integration)
- `src/promptheus/config/settings.py` (new fields)
- `pyproject.toml` (add aiohttp)
- `Dockerfile` (update HEALTHCHECK)
- `tests/monitoring/test_health_server.py` (new)

**Acceptance Criteria:**
- ✅ GET /health returns JSON with status
- ✅ All components are checked (DB, Telegram, OpenRouter)
- ✅ Docker HEALTHCHECK works
- ✅ Can be disabled via settings

---

## Phase 2: High Priority (Important for stability)

### 2.1 Dependency Injection Refactoring 🟡

**Problem:**
- Repositories are created in handlers
- Violates SOLID principles
- Hard to test

**Action Plan:**

- [ ] **Task 2.1.1**: Create DependencyContainer
  ```python
  # src/promptheus/core/dependencies.py
  class DependencyContainer:
      def __init__(self, settings: Settings)
      def get_db_session() -> Session
      def get_user_repository(db: Session) -> UserRepository
      def get_lesson_repository(db: Session) -> LessonRepository
      # ... all repositories
  ```

- [ ] **Task 2.1.2**: Refactor BotHandlers constructor
  ```python
  # handlers.py
  class BotHandlers:
      def __init__(
          self,
          ai_client: OpenRouterClient,
          session_manager: SessionManager,
          assessment_engine: AssessmentEngine,
          learning_flow: LearningFlowOrchestrator,
          progress_tracker: ProgressTracker,
          formatter: MessageFormatter,
      ):
          # Inject all dependencies
  ```

- [ ] **Task 2.1.3**: Remove `with get_db()` from handlers
  ```python
  # Instead of creating DB sessions inside methods, use injected ones
  # Create a wrapper to manage transactions
  ```

- [ ] **Task 2.1.4**: Update main.py with DI
  ```python
  # main.py
  container = DependencyContainer(settings)
  handlers = BotHandlers(
      ai_client=container.get_ai_client(),
      session_manager=container.get_session_manager(),
      ...
  )
  ```

- [ ] **Task 2.1.5**: Update tests to use mock dependencies
  ```python
  # tests/bot/test_handlers.py
  # Easily mock injected dependencies
  ```

**Files to modify:**
- `src/promptheus/core/dependencies.py` (new)
- `src/promptheus/bot/handlers.py` (major refactor)
- `src/promptheus/main.py` (update initialization)
- `tests/bot/test_handlers.py` (update with mocks)

**Acceptance Criteria:**
- ✅ No `with get_db()` in handlers
- ✅ All dependencies injected via constructor
- ✅ Tests use mock dependencies
- ✅ Follows SOLID principles

---

### 2.2 Async Repositories 🟡

**Problem:**
- Sync repositories in async event loop
- Blocking DB operations

**Action Plan:**

- [ ] **Task 2.2.1**: Evaluate approach
  ```
  Options:
  1. Migrate to SQLAlchemy async (recommended)
  2. Run sync code in thread pool (quick fix)
  
  Decision: SQLAlchemy async for correct architecture
  ```

- [ ] **Task 2.2.2**: Update dependencies
  ```toml
  # pyproject.toml
  dependencies = [
      "sqlalchemy[asyncio]>=2.0",
      "asyncpg>=0.29",  # Async PostgreSQL driver
      "aiosqlite>=0.19",  # Async SQLite driver
  ]
  ```

- [ ] **Task 2.2.3**: Refactor database.py
  ```python
  # database.py
  # Replace with create_async_engine
  # AsyncSession instead of Session
  # async context manager for get_db()
  ```

- [ ] **Task 2.2.4**: Convert repositories to async
  ```python
  # repositories.py
  # Make all methods async
  # Replace .query() with select()
  # Replace .first() with scalars().first()
  ```

- [ ] **Task 2.2.5**: Update orchestrators and engines
  ```python
  # learning_flow_orchestrator.py, assessment_engine.py, etc.
  # All methods async
  # await repository calls
  ```

- [ ] **Task 2.2.6**: Update handlers
  ```python
  # handlers.py
  # await all repository/core calls
  # async with for DB sessions
  ```

- [ ] **Task 2.2.7**: Update tests
  ```python
  # conftest.py
  # Async fixtures
  # pytest-asyncio markers
  ```

- [ ] **Task 2.2.8**: No data migration required
  ```
  # Only code changes, DB schema remains the same
  ```

**Files to modify:**
- `pyproject.toml` (update deps)
- `src/promptheus/data/database.py` (async engine)
- `src/promptheus/data/repositories.py` (all async)
- `src/promptheus/core/*.py` (all async)
- `src/promptheus/bot/handlers.py` (await calls)
- `tests/conftest.py` (async fixtures)
- `tests/**/*.py` (all tests async)

**Acceptance Criteria:**
- ✅ All repository methods async
- ✅ No blocking I/O in the event loop
- ✅ Tests pass with async
- ✅ Performance not degraded

---

### 2.3 Error Handling & Custom Exceptions 🟡

**Problem:**
- Generic exceptions
- No user-friendly errors
- Error handler does not send messages

**Action Plan:**

- [ ] **Task 2.3.1**: Create domain exceptions
  ```python
  # src/promptheus/core/exceptions.py
  class PromptheusException(Exception)
  class UserNotFoundException(PromptheusException)
  class LessonNotFoundException(PromptheusException)
  class InvalidSkillLevelError(PromptheusException)
  class RateLimitExceeded(PromptheusException)
  class AIServiceUnavailable(PromptheusException)
  ```

- [ ] **Task 2.3.2**: Use in repositories
  ```python
  # repositories.py
  # Raise UserNotFoundException instead of returning None
  # Where applicable
  ```

- [ ] **Task 2.3.3**: Use in core
  ```python
  # assessment_engine.py, progress_tracker.py, etc.
  # Raise domain exceptions
  ```

- [ ] **Task 2.3.4**: Improve error_handler
  ```python
  # handlers.py
  async def error_handler(update, context):
      error = context.error
      
      if isinstance(error, RateLimitExceeded):
          # Send rate limit message to user
      elif isinstance(error, AIServiceUnavailable):
          # Send retry message
      elif isinstance(error, PromptheusException):
          # Generic user-friendly message
      else:
          # Log critical error
  ```

- [ ] **Task 2.3.5**: Add retry with exponential backoff
  ```python
  # src/promptheus/core/retry.py
  @retry(max_attempts=3, backoff_base=2)
  async def call_with_retry(func):
      # 1s, 2s, 4s delays
  ```

- [ ] **Task 2.3.6**: Apply retry to AI calls
  ```python
  # openrouter_client.py
  @retry(max_attempts=3, backoff_base=2)
  async def call_model(self, ...):
  ```

- [ ] **Task 2.3.7**: Tests for exceptions
  ```python
  # tests/core/test_exceptions.py
  # Verify that exceptions are raised correctly
  # Verify error handler behavior
  ```

**Files to modify:**
- `src/promptheus/core/exceptions.py` (new)
- `src/promptheus/core/retry.py` (new)
- `src/promptheus/data/repositories.py` (raise exceptions)
- `src/promptheus/core/*.py` (raise exceptions)
- `src/promptheus/ai/openrouter_client.py` (retry logic)
- `src/promptheus/bot/handlers.py` (improve error_handler)
- `tests/core/test_exceptions.py` (new)

**Acceptance Criteria:**
- ✅ Domain-specific exceptions
- ✅ Error handler sends messages to users
- ✅ Exponential backoff for AI
- ✅ Tests cover error scenarios

---

### 2.4 Message Chunking & Feedback 🟡

**Problem:**
- Theory is not chunked into 50-80 words
- Feedback generates 2-3 messages but only the first is sent

**Action Plan:**

- [ ] **Task 2.4.1**: Create ContentChunker utility
  ```python
  # src/promptheus/bot/content_chunker.py
  class ContentChunker:
      def chunk_theory(text: str, max_words: int = 80) -> list[str]
      def chunk_by_sentences(text: str, max_words: int) -> list[str]
  ```

- [ ] **Task 2.4.2**: Update format_theory
  ```python
  # message_formatter.py
  def format_theory(content: str) -> list[str]:
      # Return a list of chunks instead of a single string
      chunks = ContentChunker.chunk_theory(content, max_words=80)
      return [f"💡 *Theory*\n\n{chunk}" for chunk in chunks]
  ```

- [ ] **Task 2.4.3**: Update theory handlers
  ```python
  # handlers.py
  async def show_theory_section(self, ...):
      theory_chunks = self.formatter.format_theory(section_text)
      
      # Send first chunk
      await query.edit_message_text(theory_chunks[0], ...)
      
      # If there are more chunks, show a "Next" button
      # Save current_chunk_index in session
  ```

- [ ] **Task 2.4.4**: Add theory_chunk_next handler
  ```python
  # handlers.py
  async def theory_chunk_next_callback(self, ...):
      # Show next chunk
      # When chunks are done → move to examples
  ```

- [ ] **Task 2.4.5**: Fix feedback sending
  ```python
  # handlers.py
  async def send_feedback(self, ...):
      feedback_messages = self.formatter.format_feedback(...)
      
      # Send ALL messages
      for i, msg in enumerate(feedback_messages):
          if i == 0:
              await query.edit_message_text(msg, ...)
          else:
              await asyncio.sleep(0.5)  # Typing delay
              await query.message.reply_text(msg, ...)
  ```

- [ ] **Task 2.4.6**: Add typing indicators
  ```python
  # handlers.py
  async def send_with_typing(self, chat_id, text):
      await context.bot.send_chat_action(
          chat_id=chat_id,
          action=ChatAction.TYPING
      )
      await asyncio.sleep(0.5)
      await context.bot.send_message(chat_id, text)
  ```

- [ ] **Task 2.4.7**: Tests for chunking
  ```python
  # tests/bot/test_content_chunker.py
  # Verify splitting into the correct number of words
  # Verify sentences are not broken
  ```

**Files to modify:**
- `src/promptheus/bot/content_chunker.py` (new)
- `src/promptheus/bot/message_formatter.py` (update)
- `src/promptheus/bot/handlers.py` (update theory/feedback)
- `tests/bot/test_content_chunker.py` (new)

**Acceptance Criteria:**
- ✅ Theory split into chunks of 50-80 words
- ✅ All feedback messages are sent
- ✅ Typing indicators before messages
- ✅ UX smooth and mobile-friendly

---

### 2.5 Testing Infrastructure 🟡

**Problem:**
- Coverage <30%
- No integration and E2E tests
- Flat test structure

**Action Plan:**

- [ ] **Task 2.5.1**: Restructure tests/
  ```
  tests/
    bot/
      test_handlers.py
      test_message_formatter.py
      test_content_chunker.py
    core/
      test_assessment_engine.py
      test_learning_flow_orchestrator.py
      test_progress_tracker.py
      test_session_manager.py
      test_rate_limiter.py
    data/
      test_repositories.py
      test_models.py
      test_constraints.py
    ai/
      test_openrouter_client.py
    integration/
      test_onboarding_flow.py
      test_lesson_flow.py
      test_practice_flow.py
    conftest.py
  ```

- [ ] **Task 2.5.2**: Create test fixtures
  ```python
  # conftest.py
  @pytest.fixture
  def db_session():  # Async session for tests
  
  @pytest.fixture
  def sample_user():  # User with beginner level
  
  @pytest.fixture
  def sample_lesson():  # Full lesson
  
  @pytest.fixture
  def mock_ai_client():  # Mock OpenRouter
  ```

- [ ] **Task 2.5.3**: Write unit tests for new components
  ```python
  # tests/core/test_session_manager.py
  # tests/core/test_rate_limiter.py
  # tests/bot/test_content_chunker.py
  # Cover all methods
  ```

- [ ] **Task 2.5.4**: Write integration tests
  ```python
  # tests/integration/test_onboarding_flow.py
  # Full flow: /start → assessment → goal → path
  
  # tests/integration/test_lesson_flow.py
  # Full flow: lesson start → theory → examples → practice
  ```

- [ ] **Task 2.5.5**: Configure coverage reporting
  ```toml
  # pyproject.toml
  [tool.pytest.ini_options]
  addopts = "--cov=src/promptheus --cov-report=html --cov-report=term --cov-fail-under=80"
  ```

- [ ] **Task 2.5.6**: Create test database setup
  ```python
  # conftest.py
  # Create test DB before tests
  # Apply migrations
  # Clean up after tests
  ```

- [ ] **Task 2.5.7**: Reach 80% coverage
  ```bash
  # Run coverage and find untested areas
  # Add tests until 80% is reached
  ```

**Files to modify:**
- Restructure the entire `tests/` directory
- `tests/conftest.py` (major refactor)
- Many new test files
- `pyproject.toml` (coverage settings)

**Acceptance Criteria:**
- ✅ Test coverage >80%
- ✅ Structured test hierarchy
- ✅ Integration tests for critical paths
- ✅ CI shows coverage

---

## Phase 3: Medium Priority (Code quality)

### 3.1 Configuration & Settings Usage 🟢

**Problem:**
- Hardcoded values instead of settings
- Not all environment variables are used

**Action Plan:**

- [ ] **Task 3.1.1**: Add missing settings
  ```python
  # settings.py
  webhook_url: str | None = Field(default=None)
  webhook_secret: str | None = Field(default=None)
  ai_model_lightweight: str = Field(default="qwen/qwen2.5-vl-3b-instruct:free")
  message_typing_delay: float = Field(default=0.5)
  ```

- [ ] **Task 3.1.2**: Use temperature settings
  ```python
  # assessment_engine.py
  response = await self.ai_client.call_with_fallback(
      prompt=evaluation_prompt,
      max_tokens=self.settings.max_tokens_feedback,  # From settings
      temperature=self.settings.temperature_feedback,  # From settings
  )
  ```

- [ ] **Task 3.1.3**: Inject settings where needed
  ```python
  # All classes using AI should receive settings
  class AssessmentEngine:
      def __init__(self, ai_client: OpenRouterClient, settings: Settings):
          self.settings = settings
  ```

- [ ] **Task 3.1.4**: Rename constants to UPPER_CASE
  ```python
  # openrouter_client.py
  # Move to module level
  BASE_URL = "https://openrouter.ai/api/v1"
  DEFAULT_TIMEOUT = 10.0
  ```

- [ ] **Task 3.1.5**: Create .env.example
  ```bash
  # .env.example
  # All variables with dummy values
  # Comments for each
  ```

- [ ] **Task 3.1.6**: Update README with env vars
  ```markdown
  # README.md
  ## Environment Variables
  # Description of all variables
  ```

**Files to modify:**
- `src/promptheus/config/settings.py` (add fields)
- `src/promptheus/ai/openrouter_client.py` (constants)
- `src/promptheus/core/assessment_engine.py` (use settings)
- `.env.example` (new)
- `README.md` (documentation)

**Acceptance Criteria:**
- ✅ No hardcoded values
- ✅ All settings used
- ✅ .env.example is up to date
- ✅ README documents env vars

---

### 3.2 Prompt Template Manager 🟢

**Problem:**
- Prompts hardcoded in methods
- Hard to change and version

**Action Plan:**

- [ ] **Task 3.2.1**: Create PromptTemplateManager
  ```python
  # src/promptheus/ai/prompt_templates.py
  class PromptTemplateManager:
      def get_assessment_prompt() -> str
      def get_feedback_prompt(scenario: str) -> str
      def get_evaluation_prompt(prompt: str, criteria: list) -> str
  ```

- [ ] **Task 3.2.2**: Move all prompts into templates
  ```python
  # prompt_templates.py
  ASSESSMENT_PROMPT = """
  You are an expert prompt engineering instructor...
  
  Variables: {skill_level}, {learning_goal}
  """
  
  FEEDBACK_PROMPT = """
  Evaluate this student's prompt...
  
  Variables: {user_prompt}, {scenario}, {criteria}
  """
  ```

- [ ] **Task 3.2.3**: Use template manager
  ```python
  # assessment_engine.py
  def __init__(self, ai_client, settings, template_manager):
      self.template_manager = template_manager
      
  async def evaluate_prompt(self, ...):
      prompt = self.template_manager.get_feedback_prompt(
          user_prompt=user_prompt,
          scenario=scenario
      )
  ```

- [ ] **Task 3.2.4**: Add template versioning
  ```python
  # Ability to have different prompt versions
  # A/B testing in the future
  ```

**Files to modify:**
- `src/promptheus/ai/prompt_templates.py` (new)
- `src/promptheus/ai/openrouter_client.py` (use templates)
- `src/promptheus/core/assessment_engine.py` (use templates)

**Acceptance Criteria:**
- ✅ All prompts in one place
- ✅ Easy to change and version
- ✅ Template variables are used

---

### 3.3 Logging Improvements 🟢

**Problem:**
- Not fully structured
- No duration_ms
- File log always DEBUG

**Action Plan:**

- [ ] **Task 3.3.1**: Create logging utilities
  ```python
  # src/promptheus/core/logging_utils.py
  class LogContext:
      # Context manager for logging with duration
      def __enter__(self):
          self.start_time = time.perf_counter()
      def __exit__(self):
          duration_ms = (time.perf_counter() - self.start_time) * 1000
          logger.info("Operation completed", duration_ms=duration_ms)
  ```

- [ ] **Task 3.3.2**: Standardize log fields
  ```python
  # All logs should include:
  # - timestamp (automatic)
  # - level (automatic)
  # - user_id (where applicable)
  # - action (always)
  # - duration_ms (for operations)
  ```

- [ ] **Task 3.3.3**: Update file logging level
  ```python
  # main.py
  logger.add(
      "logs/promptheus_{time}.log",
      level=settings.log_level,  # Not always DEBUG
      ...
  )
  ```

- [ ] **Task 3.3.4**: Add log scrubbing
  ```python
  # logging_utils.py
  def scrub_sensitive_data(record):
      # Remove API keys, tokens, etc
  ```

- [ ] **Task 3.3.5**: Apply LogContext
  ```python
  # In handlers and core methods
  with LogContext(action="lesson_completed", user_id=user_id):
      # Code
  ```

**Files to modify:**
- `src/promptheus/core/logging_utils.py` (new)
- `src/promptheus/main.py` (update logging config)
- `src/promptheus/**/*.py` (use LogContext)

**Acceptance Criteria:**
- ✅ Unified log format
- ✅ duration_ms in operations
- ✅ Sensitive data scrubbing
- ✅ File log level configurable

---

### 3.4 Timezone-Aware Timestamps 🟢

**Problem:**
- Use of naive datetime.utcnow
- Issues when migrating to PostgreSQL

**Action Plan:**

- [ ] **Task 3.4.1**: Create utility for timestamps
  ```python
  # src/promptheus/core/time_utils.py
  from datetime import datetime, timezone
  
  def utc_now() -> datetime:
      return datetime.now(timezone.utc)
  ```

- [ ] **Task 3.4.2**: Replace all datetime.utcnow
  ```python
  # models.py, repositories.py, progress_tracker.py
  # Replace datetime.utcnow with time_utils.utc_now()
  ```

- [ ] **Task 3.4.3**: Update Alembic for timezone
  ```python
  # alembic migration
  # Change DateTime to DateTime(timezone=True) for PostgreSQL
  ```

- [ ] **Task 3.4.4**: Tests with timezone
  ```python
  # Verify that all timestamps are timezone-aware
  ```

**Files to modify:**
- `src/promptheus/core/time_utils.py` (new)
- `src/promptheus/data/models.py` (use util)
- `src/promptheus/data/repositories.py` (use util)
- `src/promptheus/core/progress_tracker.py` (use util)
- `alembic/versions/xxxx_timezone_aware.py` (new migration)

**Acceptance Criteria:**
- ✅ All timestamps timezone-aware
- ✅ No datetime.utcnow in code
- ✅ PostgreSQL supports TIMESTAMP WITH TIME ZONE

---

## Phase 4: Low Priority (Refactoring)

### 4.1 Webhook Support 🔵

**Action Plan:**

- [ ] **Task 4.1.1**: Add webhook settings
- [ ] **Task 4.1.2**: Implement webhook mode in main.py
- [ ] **Task 4.1.3**: Add IP validation
- [ ] **Task 4.1.4**: Update deployment docs

**Criticality:** Low - polling is sufficient for MVP

---

### 4.2 Advanced AI Features 🔵

**Action Plan:**

- [ ] **Task 4.2.1**: AI-powered skill assessment (instead of counting)
- [ ] **Task 4.2.2**: Model usage tracking & cost estimation
- [ ] **Task 4.2.3**: Response caching for frequent requests

**Criticality:** Low - current approach works

---

### 4.3 UX Improvements 🔵

**Action Plan:**

- [ ] **Task 4.3.1**: Progress bar visualization
- [ ] **Task 4.3.2**: Resume at precise lesson section
- [ ] **Task 4.3.3**: Hint system for practice
- [ ] **Task 4.3.4**: Personalization by learning_goal

**Criticality:** Low - nice to have

---

## 📊 Tracking & Monitoring

### Progress Metrics

After each phase measure:

```python
# Quality metrics
- Test coverage: aim for >80%
- Type coverage: mypy --strict pass
- Lint violations: ruff check --fix pass
- Security issues: safety check pass

# Performance metrics
- Bot response time: <500ms for commands
- DB query time: <100ms per query
- AI response time: 3-10s (acceptable)
- Memory usage: <500MB under load

# Stability metrics
- Error rate: <1%
- Uptime: >99%
- Successful deployments: 100%
```

### Final readiness checklist

Phase 1 Complete:
- [ ] All database constraints work
- [ ] Session persistence across restarts
- [ ] Rate limiting protects against spam
- [ ] docker-compose up successful
- [ ] Health check endpoint available

Phase 2 Complete:
- [ ] Dependency injection correctly implemented
- [ ] All async code without blocking
- [ ] Domain-specific exceptions
- [ ] Message chunking works
- [ ] Test coverage >80%

Phase 3 Complete:
- [ ] Settings used everywhere
- [ ] Prompt templates centralized
- [ ] Logging structured
- [ ] Timestamps timezone-aware

Phase 4 (Optional):
- [ ] Webhook mode works
- [ ] Advanced AI features
- [ ] UX improvements

---

## 🚀 Execution Strategy

### Recommended Order

1. **Week 1**: Phase 1.1-1.3 (DB, Session, Rate Limiting)
2. **Week 2**: Phase 1.4-1.5 + Phase 2.1 (Docker, Health, DI)
3. **Week 3**: Phase 2.2-2.3 (Async, Errors)
4. **Week 4**: Phase 2.4-2.5 (Chunking, Testing)
5. **Week 5**: Phase 3 (Quality improvements)
6. **Week 6**: Phase 4 + Buffer for issues

### Daily Workflow

1. Choose 1-2 tasks from the current phase
2. Create a feature branch
3. Implement + write tests
4. Code review (self or peer)
5. Merge to develop
6. Mark the task as done

### Git Strategy

```bash
# Create a feature branch for each task
git checkout -b fix/task-1.1.1-database-constraints

# Commit often with clear messages
git commit -m "feat(db): add unique constraint on user_progress"

# Push and create PR
git push origin fix/task-1.1.1-database-constraints

# After review merge to develop
```

---

**Summary**: ~6 weeks plan to reach production-ready state. Priority on Phase 1-2 for an MVP release.
