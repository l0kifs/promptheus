````markdown
# Testing Strategy (TS)
## Promptheus - Telegram Bot for Prompt Engineering Education

**Version:** 1.0.0  
**Last Updated:** 2025-11-01

---

## 1. Testing Philosophy

**Quality Goals:**
- Ensure reliable user experience across all learning flows
- Validate AI integration resilience and fallback mechanisms
- Maintain data integrity and session state consistency
- Catch regressions early through automated testing

**Coverage Target:** >80% for business logic, 100% for critical paths

---

## 2. Test Pyramid Strategy

```
           ┌─────────────┐
           │   E2E (5%)  │  User flows, system integration
           ├─────────────┤
           │ Integration │  Component interaction, API calls
           │   (25%)     │
           ├─────────────┤
           │   Unit      │  Business logic, utilities
           │   (70%)     │
           └─────────────┘
```

---

## 3. Test Types

### 3.1 Unit Tests

**Scope:** Individual functions, methods, classes in isolation

**Components:**
- **Application Core**: Learning flow logic, assessment calculations, content delivery
- **Data Access Layer**: Repository methods, model validation
- **AI Integration**: Prompt templating, response parsing, model selection
- **Bot Interface**: Message formatting, keyboard generation

**Tools:**
- Framework: `pytest`
- Mocking: `pytest-mock`, `unittest.mock`
- Async: `pytest-asyncio`

**Example Test Cases:**
```python
# Assessment Engine
test_calculate_score_with_all_correct_answers_returns_100()
test_calculate_score_with_empty_list_raises_value_error()
test_determine_skill_level_for_beginner_score_returns_beginner()

# Progress Tracker
test_mark_lesson_completed_updates_status_and_timestamp()
test_increment_attempts_increases_counter()

# Message Formatter
test_format_theory_message_splits_at_80_words()
test_format_keyboard_creates_valid_telegram_structure()
```

**Coverage Target:** >85%

---

### 3.2 Integration Tests

**Scope:** Interaction between components, external services (mocked)

**Test Areas:**
- **Bot Handler → Core Logic**: Command routing, state transitions
- **Core → Data Access**: CRUD operations with test database
- **Core → AI Client**: API calls with mocked responses
- **Database Operations**: Transactions, foreign key constraints

**Tools:**
- Test Database: In-memory SQLite or Docker PostgreSQL
- HTTP Mocking: `httpx-mock`, `responses`
- Database Fixtures: `pytest-fixtures` for setup/teardown

**Example Test Cases:**
```python
# Learning Flow
test_start_lesson_creates_progress_record_and_returns_theory()
test_complete_exercise_saves_score_and_advances_to_next()

# AI Integration
test_evaluate_prompt_with_timeout_triggers_fallback_model()
test_parse_ai_response_extracts_score_and_feedback()

# Session Management
test_update_session_state_persists_to_database()
test_expired_session_cleanup_removes_old_records()
```

**Coverage Target:** >75%

---

### 3.3 End-to-End Tests

**Scope:** Complete user journeys from Telegram API to database

**Critical Flows:**
1. **Onboarding**: `/start` → Assessment → Goal Selection → Personalized Path
2. **Lesson Learning**: View Lessons → Start → Theory → Examples → Exercise
3. **Practice Evaluation**: Submit Prompt → AI Feedback → Completion
4. **Navigation**: Progress View → Resume Capability → Menu Navigation

**Tools:**
- Bot Simulation: `python-telegram-bot` test utilities
- Database: Isolated test database with migrations
- API Mocking: Stub OpenRouter API responses

**Example Test Cases:**
```python
# Complete User Journey
test_new_user_completes_onboarding_and_starts_first_lesson()
test_user_submits_exercise_receives_feedback_completes_lesson()
test_returning_user_resumes_from_last_checkpoint()

# Error Scenarios
test_ai_api_failure_shows_error_preserves_progress()
test_rate_limit_exceeded_blocks_request_shows_message()
```

**Coverage Target:** >60% for happy paths, key error scenarios

---

## 4. Critical Path Testing

**Must-Pass Scenarios** (Block deployment if failing):

### 4.1 User Onboarding
- User sends `/start` → Welcome message appears
- Assessment test completed → Skill level calculated correctly
- Goal selected → Personalized path generated

### 4.2 Lesson Flow
- Lesson started → Progress record created with `in_progress` status
- Theory section navigated → Content split into 50-80 word chunks
- Exercise submitted → AI evaluates and returns feedback
- Lesson completed → Status updated to `completed`, timestamp set

### 4.3 AI Integration
- Primary model call succeeds → Response parsed correctly
- Primary model fails → Fallback model triggered automatically
- All models fail → User-friendly error message shown

### 4.4 Data Integrity
- User progress saved → Retrievable after session restart
- Foreign key constraints enforced → No orphaned records
- Concurrent updates handled → No race conditions

---

## 5. Test Data Management

### 5.1 Test Fixtures

**User Profiles:**
```python
@pytest.fixture
def beginner_user():
    return User(
        telegram_id=12345,
        skill_level=SkillLevel.BEGINNER,
        learning_goal=LearningGoal.PROFESSIONAL
    )

@pytest.fixture
def advanced_user():
    return User(
        telegram_id=67890,
        skill_level=SkillLevel.ADVANCED,
        learning_goal=LearningGoal.ACADEMIC
    )
```

**Lesson Content:**
```python
@pytest.fixture
def sample_lesson():
    return Lesson(
        id=1,
        title="Role Definition",
        skill_level=SkillLevel.BEGINNER,
        order_index=1,
        theory_content={"sections": [...]},
        examples={"comparisons": [...]},
        exercises={"scenarios": [...]}
    )
```

**AI Responses:**
```python
@pytest.fixture
def mock_ai_feedback():
    return {
        "score": 7,
        "strengths": ["Clear role definition"],
        "improvements": ["Add output format", "Specify context"]
    }
```

### 5.2 Database State Management

**Isolation Strategy:**
- Each test runs in transaction, rolled back after
- Test database reset before each test suite
- Factory pattern for test data generation

**Migration Testing:**
```python
# Test Alembic migrations
test_upgrade_migration_applies_without_errors()
test_downgrade_migration_reverts_cleanly()
test_migration_preserves_existing_data()
```

---

## 6. Performance Testing

### 6.1 Response Time Benchmarks

**Targets:**
- Bot command response: <500ms
- Database queries: <100ms
- AI API calls: 3-10s (with timeout at 10s)
- Message formatting: <50ms

**Tools:**
- `pytest-benchmark` for Python functions
- Load testing: `locust` for concurrent users

**Example Tests:**
```python
@pytest.mark.benchmark
def test_format_message_performance(benchmark):
    result = benchmark(format_theory_message, sample_content)
    assert result  # Benchmark automatically measures time

def test_database_query_under_100ms():
    start = time.perf_counter()
    user_repo.find_by_telegram_id(12345)
    elapsed = (time.perf_counter() - start) * 1000
    assert elapsed < 100, f"Query took {elapsed}ms"
```

### 6.2 Scalability Testing

**Scenarios:**
- 100 concurrent users sending commands
- 1000 database queries per second
- AI API rate limit handling

**Metrics:**
- Response time percentiles (p50, p95, p99)
- Error rate under load
- Database connection pool exhaustion

---

## 7. Security & Validation Testing

### 7.1 Input Validation

**Test Cases:**
- SQL injection attempts in user input → Parameterized queries block
- XSS in Telegram messages → Markdown escaping applied
- Invalid callback data → Handled gracefully without crash
- Malformed API responses → Parsing errors caught

```python
def test_user_input_sanitization():
    malicious_input = "<script>alert('xss')</script>"
    formatted = format_message(malicious_input)
    assert "<script>" not in formatted

def test_sql_injection_blocked():
    user_input = "1'; DROP TABLE user; --"
    # Should not raise exception or affect database
    user_repo.find_by_username(user_input)
```

### 7.2 Authentication & Authorization

**Test Cases:**
- Telegram user ID validation → Only authenticated users proceed
- Session hijacking prevention → Session tied to telegram_id
- API key rotation → No hardcoded secrets in code

### 7.3 Data Privacy

**Test Cases:**
- PII not logged → Log scrubbing validates no sensitive data
- Encryption at rest → Database config enforces encryption
- API communication over HTTPS → Connection config verified

---

## 8. Error Handling & Resilience

### 8.1 Network Failures

**Test Scenarios:**
```python
# Telegram API unavailable
test_bot_send_message_timeout_retries_with_backoff()
test_bot_connection_error_logs_and_continues()

# OpenRouter API failures
test_ai_primary_model_500_error_triggers_fallback()
test_all_ai_models_fail_shows_user_friendly_error()

# Database connection loss
test_db_connection_timeout_retries_operation()
test_transaction_rollback_on_constraint_violation()
```

### 8.2 State Recovery

**Test Cases:**
- Session interrupted mid-lesson → Resume from last checkpoint
- Database transaction failed → No partial data saved
- AI evaluation timeout → User can retry exercise

```python
def test_lesson_resume_after_session_timeout():
    # Simulate user starting lesson
    start_lesson(user_id, lesson_id)
    
    # Session expires (simulate time passage)
    expire_session(user_id)
    
    # User returns
    response = handle_start_command(user_id)
    
    assert "Continue from" in response
    assert current_lesson_id in response
```

---

## 9. Regression Testing

### 9.1 Automated Regression Suite

**Triggers:**
- Run on every pull request
- Run before production deployment
- Nightly full suite execution

**Key Areas:**
- All critical paths (onboarding, lesson flow, practice)
- Bug fix tests (prevent reintroduction)
- API contract tests (detect breaking changes)

### 9.2 Visual Regression (Future)

**Scope:** Message formatting, keyboard layouts
**Tools:** Screenshot comparison for Telegram UI
**Implementation:** Post-MVP enhancement

---

## 10. Testing by Layer

### 10.1 Bot Interface Layer

**Test Focus:**
- Message handler routing to correct logic
- Callback query parsing and delegation
- State manager transitions
- Keyboard generation correctness

```python
# Handler Tests
test_start_command_sends_welcome_for_new_user()
test_menu_command_returns_main_menu_keyboard()
test_callback_lesson_start_updates_progress()

# Formatter Tests
test_format_theory_chunks_content_at_80_words()
test_create_navigation_keyboard_has_back_button()
```

### 10.2 Application Core Layer

**Test Focus:**
- Learning flow orchestration logic
- Assessment score calculation
- Progress tracking accuracy
- Content delivery chunking

```python
# Orchestrator Tests
test_get_next_lesson_respects_skill_level()
test_complete_lesson_marks_completed_and_advances()

# Assessment Tests
test_calculate_skill_level_from_scores()
test_generate_personalized_path_matches_goal()

# Content Tests
test_chunk_theory_splits_at_sentence_boundaries()
test_format_examples_includes_annotations()
```

### 10.3 AI Integration Layer

**Test Focus:**
- Model selection and fallback chain
- Prompt template rendering
- Response parsing and validation
- Retry logic with exponential backoff

```python
# Client Tests
test_call_api_with_primary_model_success()
test_timeout_triggers_fallback_model()
test_parse_feedback_response_extracts_score()

# Template Tests
test_render_assessment_prompt_includes_skill_level()
test_render_feedback_prompt_includes_criteria()
```

### 10.4 Data Access Layer

**Test Focus:**
- Repository CRUD operations
- Query correctness and optimization
- Transaction handling
- Foreign key enforcement

```python
# Repository Tests
test_create_user_saves_to_database()
test_find_by_telegram_id_returns_correct_user()
test_update_lesson_progress_increments_attempts()

# Constraint Tests
test_delete_user_cascades_to_progress()
test_duplicate_telegram_id_raises_integrity_error()
```

---

## 11. Test Environment Setup

### 11.1 Local Development

**Configuration:**
```bash
# .env.test
TELEGRAM_BOT_TOKEN=test_token_1234567890
OPENROUTER_API_KEY=test_key_sk-xxx
DATABASE_URL=sqlite:///:memory:
LOG_LEVEL=DEBUG
```

**Setup:**
```bash
# Install dependencies
uv sync --dev

# Run tests
pytest

# With coverage
pytest --cov=promptheus --cov-report=html
```

### 11.2 CI/CD Pipeline

**GitHub Actions Workflow:**
```yaml
test:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v3
    - uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    - name: Install dependencies
      run: |
        pip install uv
        uv sync --dev
    - name: Run linting
      run: ruff check .
    - name: Run type checking
      run: mypy src/
    - name: Run tests
      run: pytest --cov --cov-fail-under=80
```

---

## 12. Quality Gates

### 12.1 Pre-Commit Checks

**Requirements:**
- ✅ All tests pass
- ✅ Code coverage >80%
- ✅ Ruff linting no errors
- ✅ mypy type checking passes
- ✅ No print statements in code

### 12.2 Pre-Deployment Checks

**Requirements:**
- ✅ All critical path tests pass
- ✅ Integration tests pass with test database
- ✅ Performance benchmarks meet targets
- ✅ No security vulnerabilities (safety check)
- ✅ Database migrations tested

### 12.3 Monitoring Post-Deployment

**Metrics:**
- Error rate <1% (from logs)
- API response time <3s (p95)
- AI fallback rate <5%
- Database query time <100ms (p95)

---

## 13. Test Maintenance

### 13.1 Test Code Quality

**Standards:**
- Tests follow same code style as production code
- Descriptive test names (`test_what_condition_expected`)
- One assertion per test (where reasonable)
- DRY principle: Use fixtures for common setup
- Clear AAA structure: Arrange, Act, Assert

### 13.2 Flaky Test Handling

**Policy:**
- Flaky test detected → Mark as `@pytest.mark.flaky`
- Root cause investigated within 1 sprint
- Fixed or permanently disabled with justification
- Track flaky test rate <2%

### 13.3 Test Suite Performance

**Optimization:**
- Parallel execution: `pytest -n auto`
- Skip slow tests in development: `pytest -m "not slow"`
- Cache test database fixtures
- Mock external services consistently

**Target:** Full test suite <5 minutes

---

## 14. Test Reporting

### 14.1 Coverage Reports

**Format:** HTML report generated after each run
**Storage:** `htmlcov/` directory (gitignored)
**Review:** Weekly coverage trend analysis

**Command:**
```bash
pytest --cov=promptheus --cov-report=html
open htmlcov/index.html
```

### 14.2 CI/CD Test Reports

**Outputs:**
- JUnit XML for CI dashboard integration
- Coverage badge in README
- Failed test logs attached to PR comments

---

## 15. Testing Checklist

### 15.1 New Feature Checklist

- [ ] Unit tests for all new functions/methods
- [ ] Integration tests for component interactions
- [ ] E2E test for happy path user flow
- [ ] Error scenario tests (network, validation, edge cases)
- [ ] Performance test if latency-sensitive
- [ ] Security validation if handling user input
- [ ] Update test fixtures and factories
- [ ] Coverage meets 80% threshold

### 15.2 Bug Fix Checklist

- [ ] Regression test added reproducing original bug
- [ ] Test fails before fix, passes after fix
- [ ] Related edge cases covered
- [ ] Integration test validates fix in context
- [ ] Root cause documented in test docstring

---

## 16. Future Testing Enhancements

### 16.1 Post-MVP (v1.1)

**Additions:**
- Load testing with `locust` for 1000+ concurrent users
- Contract testing for Telegram Bot API
- Chaos engineering for resilience validation
- A/B testing framework for UX experiments

### 16.2 Production (v2.0)

**Additions:**
- Canary deployment testing
- Synthetic monitoring (cron job simulating user)
- Real user monitoring (RUM) integration
- Automated rollback on test failures

---

## 17. Test Ownership

**Responsibility Matrix:**

| Test Type | Owner | Frequency | CI/CD Gate |
|-----------|-------|-----------|------------|
| Unit Tests | Developer | Per commit | PR merge |
| Integration Tests | Developer | Per commit | PR merge |
| E2E Tests | QA/Developer | Per PR | Deployment |
| Performance Tests | DevOps | Weekly | Pre-release |
| Security Tests | Security Team | Bi-weekly | Pre-release |
| Regression Suite | Automated | Nightly | Pre-deployment |

---

## 18. Success Metrics

### 18.1 Test Quality KPIs

**Targets:**
- Test coverage: >80% (business logic)
- Flaky test rate: <2%
- Test suite execution time: <5 minutes
- Test failure rate in CI: <5%
- Bug escape rate to production: <1%

### 18.2 Quality Impact Metrics

**Indicators:**
- Production incidents: <1 per month
- Mean time to detection (MTTD): <1 hour
- Mean time to resolution (MTTR): <4 hours
- User-reported bugs: <5 per release

---

## 19. References

**Related Documents:**
- **TRD**: Technical requirements and integration details
- **SAD**: System architecture and component boundaries
- **DDD**: Database schema and data integrity constraints
- **DS**: Code quality standards and conventions

**Testing Standards:**
- pytest documentation: https://docs.pytest.org
- Python testing best practices: PEP 8, Google Style Guide
- Telegram Bot API testing: python-telegram-bot test utilities

---

**Document Responsibility:** Define comprehensive testing strategy, test types, quality gates, and success criteria. Does not cover implementation details (TRD), architecture decisions (SAD), or code style (DS).

````
