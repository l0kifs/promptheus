# Technical Task: Fix Issues 11.1-11.2 - Rate Limiting and Error Handling

## METADATA

**Task ID:** PRMT-ERR-001
**Name:** Implement Rate Limiting and Enhanced Error Handling
**Created:** 2025-11-08
**Priority:** High
**Complexity Estimate:** 7/10
**Estimated Time:** 6-8 hours

---

## BUSINESS CONTEXT

### Problem Description
The current implementation lacks critical production-ready features for rate limiting and proper error handling, which can lead to:
- Abuse of the bot by malicious users
- Poor user experience during system failures
- Unclear error messages leaving users confused
- Potential security risks from unlimited API access

### Business Goals
- Prevent bot abuse and ensure fair resource usage
- Provide clear, helpful error messages to users
- Improve system reliability and user trust
- Meet production requirements for error handling

### Target Audience
- **Primary:** End users of the Telegram bot
- **Secondary:** System administrators, developers

### Business Value
- Enhanced user experience with clear error communication
- Protection against abuse and resource exhaustion
- Compliance with production requirements
- Foundation for reliable scaling

---

## TECHNICAL SPECIFICATION

### Functional Requirements

#### Rate Limiting Implementation
**Main Functionality**
As a system, I must limit request frequency from users to prevent abuse and ensure quality for all users.

**Detailed Requirements**
1. **Rate Limit Enforcement**
   - Description: Implement middleware that tracks and enforces request limits per user
   - Input data: User ID, request timestamp
   - Output data: Allow/deny decision with remaining time
   - Constraints: 10 requests per minute per user, sliding window

2. **Rate Limit Response**
   - Description: Return user-friendly message when limit exceeded
   - Input data: User ID, time until reset
   - Output data: Formatted message with wait time
   - Constraints: Message in Russian, emoji indicators

3. **Rate Limit Storage**
   - Description: Store request timestamps for rate calculation
   - Input data: User ID, current timestamp
   - Output data: Updated request history
   - Constraints: In-memory for MVP, Redis-ready for production

#### Enhanced Error Handling
**Main Functionality**
As a system, I must provide appropriate error responses based on error type and communicate clearly with users.

**Detailed Requirements**
1. **Error Classification**
   - Description: Categorize errors into User, API, and System types
   - Input data: Exception type, context
   - Output data: Error category and handling strategy
   - Constraints: Follow TRD §8.1 error handling strategy

2. **User-Friendly Messages**
   - Description: Send appropriate messages to users based on error type
   - Input data: Error category, user context
   - Output data: Formatted message with next steps
   - Constraints: Russian language, helpful guidance

3. **Error Logging**
   - Description: Log errors with appropriate detail levels
   - Input data: Error details, user context
   - Output data: Structured log entries
   - Constraints: Include user_id, action, error details

### Non-Functional Requirements

#### Performance
- Rate limit checks: <10ms per request
- Error handling overhead: <5ms per error
- Memory usage for rate limiting: <50MB for 1000 concurrent users

#### Security
- Rate limiting prevents DoS attacks
- Error messages don't leak sensitive information
- Logging sanitizes user data

#### Reliability
- Rate limiting state survives bot restarts (persistent storage)
- Error handling never crashes the bot
- Graceful degradation during high load

#### Compatibility
- Works with existing Telegram bot framework
- Compatible with current async architecture
- No breaking changes to existing handlers

---

## TECHNICAL CONTEXT

### System Architecture
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Telegram      │───▶│  Rate Limit      │───▶│   Bot Handler   │
│   Request       │    │  Middleware      │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │                        │
                              ▼                        ▼
                       ┌─────────────┐    ┌──────────────────┐
                       │   Storage   │    │  Error Handler   │
                       │ (In-memory) │    │                  │
                       └─────────────┘    └──────────────────┘
```

### Technology Stack
- **Backend:** Python 3.11, python-telegram-bot
- **Async Framework:** asyncio
- **Storage:** In-memory (dict) for MVP, Redis for production
- **Logging:** loguru with structured logging

### Project Structure
```
src/promptheus/
├── bot/
│   ├── middleware/           # NEW: rate limiting middleware
│   │   └── rate_limiter.py
│   ├── handlers.py           # MODIFY: enhanced error handler
│   └── base_handlers.py      # MODIFY: error handler implementation
├── core/
│   └── rate_limit_service.py # NEW: rate limit business logic
└── config/
    └── settings.py           # EXISTS: rate_limit_requests setting
```

### Files to Modify

1. **`src/promptheus/bot/base_handlers.py`**
   - Purpose: Base handler class with error handling
   - Where to make changes: Enhance `error_handler` method
   - Notes: Add error classification and user messaging

2. **`src/promptheus/bot/middleware/rate_limiter.py`** (CREATE)
   - Purpose: Telegram middleware for rate limiting
   - Notes: Implement as telegram.ext middleware

3. **`src/promptheus/core/rate_limit_service.py`** (CREATE)
   - Purpose: Business logic for rate limiting
   - Notes: Sliding window algorithm, storage abstraction

4. **`src/promptheus/main.py`**
   - Purpose: Bot application setup
   - Where to make changes: Add middleware registration
   - Notes: Register rate limiting middleware

### Related Components
- **Settings:** `rate_limit_requests` already exists
- **Dependency Container:** May need to inject rate limit service
- **Logging:** Uses loguru for structured logging
- **Async Pattern:** Must be async-compatible

---

## EXAMPLES AND DOCUMENTATION

### Code Examples

#### Example 1: Telegram Middleware Pattern
```python
# From python-telegram-bot documentation
class RateLimitMiddleware:
    def __init__(self, rate_limiter):
        self.rate_limiter = rate_limiter
    
    async def __call__(self, update, context, callback):
        user_id = update.effective_user.id
        
        if not await self.rate_limiter.check_limit(user_id):
            # Send rate limit message
            await update.effective_message.reply_text("⏸️ Too many requests...")
            return  # Don't call handler
        
        return await callback(update, context)
```

#### Example 2: Error Classification
```python
# Enhanced error handler pattern
async def error_handler(self, update, context):
    error = context.error
    
    if isinstance(error, NetworkError):
        await self._handle_network_error(update, error)
    elif isinstance(error, RateLimitError):
        await self._handle_rate_limit_error(update, error)
    elif isinstance(error, ValidationError):
        await self._handle_user_error(update, error)
    else:
        await self._handle_system_error(update, error)
```

### Documentation
- [Telegram Bot Middleware](https://docs.python-telegram-bot.org/en/stable/telegram.ext.middleware.html)
- [Python Rate Limiting Patterns](https://github.com/vutran1710/PyrateLimiter)
- [Error Handling Best Practices](https://docs.python.org/3/tutorial/errors.html)

### Existing Patterns
- **Async/Await:** All handlers use async/await pattern
- **Dependency Injection:** Handlers receive dependencies in constructor
- **Structured Logging:** Uses loguru with context parameters
- **Settings Management:** Pydantic settings with validation

### Known Pitfalls
⚠️ **Important:**
- Telegram middleware must be async and not block the event loop
- Rate limiting state should survive bot restarts for production
- Error messages must be in Russian to match existing UX
- Don't log sensitive information in error details
- Rate limiting should apply to all user interactions, not just commands

---

## ACCEPTANCE CRITERIA

### Scenario Criteria (Given-When-Then)

#### Scenario 1: Rate limit enforcement
```gherkin
Given user sends 10 requests within 1 minute
When user sends 11th request
Then system blocks the request
And sends "⏸️ Слишком много запросов" message
And indicates wait time of 1 minute
```

#### Scenario 2: Rate limit reset
```gherkin
Given user exceeded rate limit
When 1 minute passes
Then user can send requests again
And rate limit counter resets
```

#### Scenario 3: Network error handling
```gherkin
Given OpenRouter API is unreachable
When user submits practice exercise
Then system shows "⏱️ Запрос занял слишком много времени"
And suggests retrying or simplifying prompt
And logs error with user_id and context
```

#### Scenario 4: User input error
```gherkin
Given user sends invalid callback data
When system processes the callback
Then system shows "🔄 Что-то пошло не так"
And suggests returning to main menu
And logs error without crashing
```

### Rules and Constraints
- [ ] Rate limit: exactly 10 requests per minute per user
- [ ] Error messages: in Russian with appropriate emojis
- [ ] Rate limit messages: include remaining wait time
- [ ] Error logging: include user_id, action, error type
- [ ] System errors: never crash the bot, always recover gracefully

### Testing
- [ ] Unit tests for rate limiting logic (>=90% coverage)
- [ ] Integration tests for middleware
- [ ] Error handler tests for different error types
- [ ] Manual testing: exceed rate limits, trigger errors
- [ ] Load testing: concurrent users hitting rate limits

### Code Review
- [ ] Async patterns used correctly throughout
- [ ] Error handling follows existing patterns
- [ ] No hardcoded values (use settings)
- [ ] Type hints added for all new functions
- [ ] Docstrings in Google style

### Performance
- [ ] Rate limit check: <10ms per request
- [ ] Error handling: <5ms overhead
- [ ] Memory usage: <50MB for 1000 users
- [ ] No performance regression in existing functionality

---

## IMPLEMENTATION PLAN

### Execution Stages

#### Stage 1: Rate Limiting Infrastructure
**Description:** Create core rate limiting components
**Tasks:**
- [ ] Create `rate_limit_service.py` with sliding window algorithm
- [ ] Implement in-memory storage for request timestamps
- [ ] Add rate limit checking and enforcement logic
- [ ] Write comprehensive unit tests

**Validation:**
- Unit tests pass with 90%+ coverage
- Rate limiting logic works correctly for various scenarios

#### Stage 2: Rate Limiting Middleware
**Description:** Integrate rate limiting into Telegram bot
**Tasks:**
- [ ] Create `rate_limiter.py` middleware class
- [ ] Implement Telegram middleware interface
- [ ] Add rate limit exceeded message formatting
- [ ] Register middleware in main.py

**Validation:**
- Middleware loads without errors
- Rate limiting blocks requests correctly
- User receives appropriate messages

#### Stage 3: Enhanced Error Handling
**Description:** Improve error handler with classification and messaging
**Tasks:**
- [ ] Enhance `error_handler` in `base_handlers.py`
- [ ] Add error classification logic (User/API/System)
- [ ] Implement user-friendly message sending
- [ ] Add structured error logging

**Validation:**
- Different error types produce appropriate responses
- Error messages are user-friendly and helpful
- Logging includes required context

#### Stage 4: Integration Testing
**Description:** Test complete functionality
**Tasks:**
- [ ] Write integration tests for rate limiting
- [ ] Test error handling in various scenarios
- [ ] Manual testing with real bot interactions
- [ ] Performance testing under load

**Validation:**
- All acceptance criteria met
- No regressions in existing functionality
- System handles edge cases gracefully

### Action Order
1. Implement rate limiting service (core logic)
2. Create middleware and integrate into bot
3. Enhance error handler with classification
4. Add user messaging for errors
5. Comprehensive testing and validation

### Dependencies
- Python 3.11+ (already met)
- python-telegram-bot middleware support (already available)
- Existing settings and logging infrastructure

---

## TESTING AND VALIDATION

### Unit Tests
```python
# tests/core/test_rate_limit_service.py
@pytest.mark.asyncio
async def test_rate_limit_allows_initial_requests():
    """Test that initial requests are allowed."""
    service = RateLimitService(requests_per_minute=10)
    
    # Given
    user_id = 12345
    
    # When
    for i in range(10):
        allowed = await service.check_limit(user_id)
        assert allowed is True

@pytest.mark.asyncio
async def test_rate_limit_blocks_excess_requests():
    """Test that 11th request is blocked."""
    service = RateLimitService(requests_per_minute=10)
    
    # Given
    user_id = 12345
    
    # When - send 11 requests
    for i in range(11):
        allowed = await service.check_limit(user_id)
    
    # Then - 11th should be blocked
    assert allowed is False

def test_error_classification():
    """Test error type classification."""
    handler = BaseBotHandlers(...)
    
    # Network error
    network_error = httpx.TimeoutException("timeout")
    category = handler._classify_error(network_error)
    assert category == "api_error"
    
    # User error
    user_error = ValueError("invalid input")
    category = handler._classify_error(user_error)
    assert category == "user_error"
```

### Commands to Run
```bash
# Run rate limiting tests
pytest tests/core/test_rate_limit_service.py -v

# Run error handling tests
pytest tests/bot/test_error_handler.py -v

# Run integration tests
pytest tests/integration/test_rate_limiting.py -v

# Full test suite
pytest --cov --cov-fail-under=85

# Manual testing
python -m src.main  # Start bot and test rate limits
```

### Manual Testing Scenarios

1. **Rate Limit Testing**
   - Send 10 messages quickly to bot
   - Send 11th message
   - Verify: blocked with appropriate message
   - Wait 1 minute, try again
   - Verify: requests allowed again

2. **Error Handling Testing**
   - Submit invalid callback data
   - Verify: user-friendly error message
   - Check logs: appropriate error logging

3. **Load Testing**
   - Simulate multiple users hitting rate limits
   - Verify: system remains stable
   - Check memory usage under load

---

## ADDITIONAL CONSIDERATIONS

### Risks
- **Risk: Rate limiting blocks legitimate users**
  - Mitigation: Clear messaging, reasonable limits (10/min), automatic reset
  
- **Risk: Error handling changes break existing functionality**
  - Mitigation: Comprehensive testing, gradual rollout, rollback plan

- **Risk: Memory usage for rate limiting state**
  - Mitigation: Use Redis for production, implement cleanup for inactive users

### Assumptions
- In-memory storage sufficient for MVP (development environment)
- Russian language appropriate for all users
- 10 requests/minute provides good balance of usability vs protection
- Error classification covers all major error types

### Limitations
- Rate limiting state lost on bot restart (MVP limitation)
- Error messages fixed (not configurable)
- No per-endpoint rate limits (global per user)

### Future Improvements
- [ ] Redis-based rate limiting for production persistence
- [ ] Configurable error messages
- [ ] Per-endpoint rate limits
- [ ] Rate limit analytics and monitoring
- [ ] Automatic rate limit adjustment based on load

### Questions and Unresolved Issues
- [ ] Should rate limiting apply to all message types (text, callbacks, commands)?
- [ ] What specific error messages should be shown for different API failures?
- [ ] Should we implement exponential backoff for retries?
- [ ] How to handle rate limiting in webhook mode vs polling mode?

---

## COMPLETION CHECKLIST

### Development
- [ ] `rate_limit_service.py` created with sliding window algorithm
- [ ] `rate_limiter.py` middleware implemented for Telegram
- [ ] Enhanced `error_handler` with error classification
- [ ] User-friendly error messages in Russian
- [ ] Middleware registered in `main.py`
- [ ] Rate limiting settings integrated
- [ ] Structured error logging implemented

### Testing
- [ ] Unit tests for rate limiting (>=90% coverage)
- [ ] Unit tests for error classification
- [ ] Integration tests for middleware
- [ ] Manual testing of rate limits
- [ ] Error scenario testing
- [ ] Performance testing completed

### Documentation
- [ ] Docstrings added to all new functions
- [ ] Error handling documented in code
- [ ] Rate limiting behavior documented
- [ ] README updated with new features

### Code Quality
- [ ] Ruff linting passes
- [ ] mypy type checking passes
- [ ] No TODO/FIXME in production code
- [ ] Code review completed
- [ ] Async patterns used correctly

### Finalization
- [ ] All acceptance criteria verified
- [ ] No regressions in existing functionality
- [ ] Settings validated for production use
- [ ] Error handling tested in various scenarios
- [ ] Branch merged to develop
- [ ] Task completed and documented

---

## CONCLUSION

This implementation will address critical gaps in production readiness by adding:
- **Rate Limiting:** Protection against abuse with user-friendly messaging
- **Enhanced Error Handling:** Clear communication during failures
- **System Reliability:** Graceful error recovery and appropriate logging

The solution follows existing project patterns (async, dependency injection, structured logging) and integrates seamlessly with the current architecture. Testing will ensure reliability and performance meet production standards.

**Estimated Timeline:** 6-8 hours across 4 development stages
**Risk Level:** Medium (requires careful error handling implementation)
**Dependencies:** None (uses existing infrastructure)

---

**Document Version:** 1.0.0  
**Created:** 2025-11-08  
**Author:** AI Assistant  
**Review Required:** Yes  
**Testing Required:** Comprehensive (unit + integration + manual)