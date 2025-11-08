# Fix Issues 16.1-16.2: Dependency Injection and Custom Exceptions

## METADATA

**Task ID:** PRMT-161
**Name:** Fix Dependency Injection Pattern and Implement Custom Exceptions
**Created:** 2025-11-08
**Priority:** High
**Complexity Estimate:** 7/10
**Estimated Time:** 6-8 hours

---

## BUSINESS CONTEXT

### Problem Description
The codebase has inconsistencies in dependency injection patterns and lacks domain-specific exception handling, which affects code maintainability, testability, and error handling quality.

### Business Goals
- Ensure consistent dependency injection throughout the application
- Improve error handling with domain-specific exceptions
- Enhance code maintainability and testability
- Align implementation with documented standards

### Target Audience
- **Primary:** Developers maintaining and extending the codebase
- **Secondary:** QA team testing error scenarios

### Business Value
- Reduces bugs from improper dependency management
- Improves debugging with clear, contextual error messages
- Enables better testing through proper DI patterns
- Aligns with architectural standards for long-term maintainability

---

## TECHNICAL SPECIFICATION

### Functional Requirements

#### Main Functionality
Fix dependency injection inconsistencies and implement custom exception hierarchy for domain-specific error handling.

#### Detailed Requirements

1. **Dependency Injection Audit and Fixes**
   - Description: Review all components for proper constructor injection
   - Input data: Current codebase components
   - Output data: Updated components with consistent DI
   - Constraints: Must maintain existing functionality

2. **Custom Exception Hierarchy**
   - Description: Create domain-specific exceptions for different error categories
   - Input data: Error scenarios identified in codebase
   - Output data: Exception classes with proper inheritance
   - Constraints: Must follow Python exception best practices

3. **Error Handling Updates**
   - Description: Update error handling to use custom exceptions
   - Input data: Current generic exception usage
   - Output data: Contextual error messages and proper exception types

### Non-Functional Requirements

#### Performance
- No performance impact on existing functionality
- Exception creation should be lightweight

#### Security
- Exception messages should not leak sensitive information
- Proper error logging without exposing internal details

#### Reliability
- Exception handling should not break existing error flows
- Backward compatibility maintained

#### Compatibility
- Compatible with existing logging and error handling infrastructure
- No breaking changes to public APIs

---

## TECHNICAL CONTEXT

### System Architecture
```
┌─────────────────┐      ┌──────────────────┐      ┌─────────────────┐
│   Bot Handlers  │─────▶│ Dependency       │─────▶│   Core Logic    │
│                 │      │   Container      │      │                 │
│  • Commands     │      │                  │      │  • Assessment   │
│  • Callbacks    │      │  • Factories     │      │  • Progress     │
│  • Messages     │      │  • Sessions      │      │  • Learning     │
└─────────────────┘      └──────────────────┘      └─────────────────┘
         │                        │                        │
         ▼                        ▼                        ▼
┌─────────────────┐      ┌──────────────────┐      ┌─────────────────┐
│ Custom          │      │ Async            │      │ Domain          │
│ Exceptions      │      │ Repositories     │      │ Exceptions      │
│                 │      │                  │      │                 │
│ • Validation    │      │ • User           │      │ • Business      │
│ • Business      │      │ • Lesson         │      │ • System        │
│ • System        │      │ • Progress       │      │                 │
└─────────────────┘      └──────────────────┘      └─────────────────┘
```

### Technology Stack
- **Language:** Python 3.11+
- **Framework:** Async Python with dependency injection
- **Architecture:** Layered architecture with DI container
- **Testing:** pytest with dependency mocking

### Project Structure
```
src/promptheus/
├── core/
│   ├── exceptions.py         ← CREATE: domain exceptions
│   ├── assessment_engine.py  ← UPDATE: use custom exceptions
│   └── dependency_container.py ← AUDIT: DI patterns
├── bot/
│   ├── base_handlers.py      ← UPDATE: use custom exceptions
│   └── handlers.py           ← AUDIT: DI completeness
├── data/
│   ├── models.py             ← UPDATE: validation exceptions
│   └── async_repositories.py ← AUDIT: session injection
└── config/
    └── settings.py           ← AUDIT: configuration exceptions
```

### Files to Modify

1. **`src/promptheus/core/exceptions.py`** (CREATE)
   - Purpose: Define domain-specific exception hierarchy
   - Notes: Base exceptions for different error categories

2. **`src/promptheus/core/assessment_engine.py`**
   - Purpose: Update to use custom exceptions instead of ValueError
   - Where to make changes: Validation methods, error handling
   - Notes: Replace generic exceptions with domain-specific ones

3. **`src/promptheus/bot/base_handlers.py`**
   - Purpose: Update error classification and handling
   - Where to make changes: `_classify_error` method, error handlers
   - Notes: Integrate custom exceptions into error handling flow

4. **`src/promptheus/data/models.py`**
   - Purpose: Add validation exceptions for model constraints
   - Where to make changes: Model validation methods
   - Notes: Use custom exceptions for business rule violations

5. **`src/promptheus/config/settings.py`**
   - Purpose: Update configuration validation
   - Where to make changes: Validation methods
   - Notes: Use custom exceptions for configuration errors

---

## EXAMPLES AND DOCUMENTATION

### Code Examples

#### Example 1: Current Generic Exception Usage
```python
# Current approach in assessment_engine.py
if len(questions) != 5:
    raise ValueError(f"Assessment must have exactly 5 questions, found {len(questions)}")
```

#### Example 2: Proposed Custom Exception Usage
```python
# New approach with domain exceptions
from promptheus.core.exceptions import ValidationError, AssessmentError

if len(questions) != 5:
    raise AssessmentError(
        f"Invalid assessment configuration: expected 5 questions, got {len(questions)}",
        details={"expected": 5, "actual": len(questions)}
    )
```

#### Example 3: Exception Hierarchy
```python
# exceptions.py
class PromptheusError(Exception):
    """Base exception for all Promptheus errors."""
    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message)
        self.details = details or {}

class ValidationError(PromptheusError):
    """Raised when input validation fails."""

class BusinessError(PromptheusError):
    """Raised when business rules are violated."""

class AssessmentError(BusinessError):
    """Raised when assessment operations fail."""

class SystemError(PromptheusError):
    """Raised when system-level errors occur."""
```

### Documentation
- [Python Exception Hierarchy](https://docs.python.org/3/library/exceptions.html)
- [Custom Exceptions Best Practices](https://docs.python.org/3/tutorial/errors.html)
- [Promptheus Development Standards](../docs/development-standards.md) - Error Handling section

### Existing Patterns
- **Exception Handling:** Base handlers already classify errors into categories
- **Dependency Injection:** Container pattern with factory methods for repositories
- **Error Logging:** Structured logging with context in all components

### Known Pitfalls
⚠️ **Important:**
- Don't break existing error handling flows - maintain backward compatibility
- Exception messages should be user-friendly but not leak sensitive data
- Custom exceptions should inherit from appropriate base classes
- Avoid over-engineering - only create exceptions for frequently occurring error scenarios

---

## ACCEPTANCE CRITERIA

### Scenario Criteria (Given-When-Then)

#### Scenario 1: Assessment validation error
```gherkin
Given assessment engine receives invalid question count
When evaluate_answers is called
Then AssessmentError is raised with descriptive message
And error details include expected vs actual counts
```

#### Scenario 2: Model validation error
```gherkin
Given user model receives invalid skill level
When skill_level is set to invalid value
Then ValidationError is raised with allowed values
```

#### Scenario 3: Configuration error
```gherkin
Given settings receive invalid webhook URL
When settings are validated
Then ConfigurationError is raised with validation details
```

#### Scenario 4: Dependency injection verification
```gherkin
Given all components are initialized via container
When application starts
Then no direct database access in handlers
And all repositories injected via container factory methods
```

### Rules and Constraints
- [ ] All custom exceptions inherit from PromptheusError base class
- [ ] Exception messages are descriptive but don't leak sensitive data
- [ ] Error handling maintains backward compatibility
- [ ] Dependency injection covers all database and external service access
- [ ] No breaking changes to existing APIs

### Testing
- [ ] Unit tests for all custom exception classes
- [ ] Integration tests for error handling flows
- [ ] Tests verify exception details and messages
- [ ] Dependency injection tests ensure proper injection
- [ ] Regression tests confirm no breaking changes

### Code Review
- [ ] Exception hierarchy follows Python conventions
- [ ] All public methods document raised exceptions
- [ ] Error messages are internationalizable (no hardcoded strings)
- [ ] Dependency injection is complete and consistent

### Performance
- [ ] Exception creation doesn't impact normal operation performance
- [ ] Error handling doesn't add significant latency
- [ ] Memory usage remains within acceptable limits

---

## IMPLEMENTATION PLAN

### Execution Stages

#### Stage 1: Create Exception Hierarchy
**Description:** Define and implement custom exception classes
**Tasks:**
- [ ] Create `src/promptheus/core/exceptions.py` with base and specific exceptions
- [ ] Add proper docstrings and type hints
- [ ] Create unit tests for exception classes
- [ ] Update imports in affected modules

**Validation:**
- All exception classes can be imported successfully
- Exception hierarchy is correct (isinstance checks work)
- Unit tests pass

#### Stage 2: Update Core Components
**Description:** Replace generic exceptions with custom ones in core logic
**Tasks:**
- [ ] Update `assessment_engine.py` to use `AssessmentError`
- [ ] Update `settings.py` to use `ConfigurationError`
- [ ] Update model validation in `models.py`
- [ ] Add proper error details to exceptions

**Validation:**
- All existing tests still pass
- New exception types are raised in error scenarios
- Error messages are more descriptive

#### Stage 3: Update Error Handling
**Description:** Integrate custom exceptions into error handling flow
**Tasks:**
- [ ] Update `base_handlers.py` error classification
- [ ] Add handling for custom exception types
- [ ] Update error messages for user-facing errors
- [ ] Test error handling integration

**Validation:**
- Error handler correctly processes custom exceptions
- User receives appropriate error messages
- Logging includes exception details

#### Stage 4: Dependency Injection Audit
**Description:** Verify and fix any DI inconsistencies
**Tasks:**
- [ ] Audit all handler methods for direct database access
- [ ] Ensure repositories are always injected via container
- [ ] Update any missed injection points
- [ ] Add tests for DI completeness

**Validation:**
- No direct `get_db()` calls in handlers
- All database operations go through injected repositories
- Container factory methods are used consistently

#### Stage 5: Testing and Validation
**Description:** Comprehensive testing of changes
**Tasks:**
- [ ] Run full test suite to ensure no regressions
- [ ] Add integration tests for error scenarios
- [ ] Test dependency injection in isolation
- [ ] Manual testing of error flows

**Validation:**
- All tests pass
- Code coverage maintained
- Manual error scenarios work correctly

---

## TESTING AND VALIDATION

### Unit Tests
```python
# tests/core/test_exceptions.py
import pytest
from promptheus.core.exceptions import (
    PromptheusError,
    ValidationError,
    AssessmentError,
    ConfigurationError
)

def test_exception_hierarchy():
    """Test that exceptions inherit correctly."""
    error = AssessmentError("Test message")
    assert isinstance(error, AssessmentError)
    assert isinstance(error, PromptheusError)
    assert isinstance(error, Exception)

def test_exception_with_details():
    """Test exception with additional details."""
    details = {"field": "skill_level", "value": "invalid"}
    error = ValidationError("Invalid value", details=details)
    assert error.details == details
    assert str(error) == "Invalid value"
```

### Commands to Run
```bash
# Run exception tests
pytest tests/core/test_exceptions.py -v

# Run assessment engine tests
pytest tests/core/test_assessment_engine.py -v

# Run full test suite
pytest --cov=src/promptheus

# Check for import errors
python -c "from promptheus.core.exceptions import *; print('Imports OK')"
```

### Manual Testing Scenarios

1. **Assessment Error Testing**
   - Modify assessment questions to have wrong count
   - Trigger assessment evaluation
   - Verify AssessmentError is raised with correct details

2. **Configuration Error Testing**
   - Set invalid webhook URL in settings
   - Start application
   - Verify ConfigurationError during validation

3. **Dependency Injection Testing**
   - Check that handlers receive all dependencies via constructor
   - Verify no direct database imports in handler files

---

## ADDITIONAL CONSIDERATIONS

### Risks
- **Risk: Breaking existing error handling**
  - Mitigation: Maintain exception type compatibility, test thoroughly
  
- **Risk: Performance impact from exception details**
  - Mitigation: Keep exception details lightweight, avoid large objects

### Assumptions
- Existing error handling flows don't rely on specific exception types
- Custom exceptions won't break logging or monitoring
- Dependency injection is mostly correct, only minor fixes needed

### Limitations
- Only addressing issues 16.1 and 16.2 from the mismatches document
- Not changing exception handling architecture, only exception types
- Maintaining backward compatibility with existing error flows

### Future Improvements
- [ ] Add error codes for internationalization
- [ ] Implement error tracking and metrics
- [ ] Add automatic error reporting for system errors
- [ ] Create error response standardization

### Questions and Unresolved Issues
- [ ] Should exceptions include error codes for API responses?
- [ ] Do we need different exception types for different severity levels?
- [ ] Should validation errors be separated by domain (user, lesson, etc.)?

---

## COMPLETION CHECKLIST

### Development
- [ ] `src/promptheus/core/exceptions.py` created with complete hierarchy
- [ ] `assessment_engine.py` updated to use AssessmentError
- [ ] `settings.py` updated to use ConfigurationError
- [ ] `base_handlers.py` updated for custom exception handling
- [ ] `models.py` updated with validation exceptions
- [ ] All components use proper dependency injection
- [ ] No direct database access in handlers

### Testing
- [ ] Unit tests for all exception classes
- [ ] Tests for error handling integration
- [ ] Tests for dependency injection correctness
- [ ] Integration tests for error scenarios
- [ ] Full test suite passes without regressions
- [ ] Code coverage >= 80%

### Documentation
- [ ] Exception classes fully documented
- [ ] Error handling patterns documented
- [ ] Updated docstrings for changed methods
- [ ] Exception usage examples added

### Code Quality
- [ ] Ruff linting passes
- [ ] Type hints complete for new code
- [ ] No TODO/FIXME comments added
- [ ] Code review completed

### Finalization
- [ ] Branch created: `feature/PRMT-161-fix-di-exceptions`
- [ ] Commits with clear conventional commit messages
- [ ] Pull request created with detailed description
- [ ] CI/CD pipeline passes
- [ ] Ready for review and merge