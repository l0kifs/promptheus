## METADATA

**Task ID:** LOG-12-1-2
**Name:** Fix Structured Logging and Log Levels (Issues 12.1-12.2)
**Created:** 2025-11-08
**Priority:** Medium
**Complexity Estimate:** 4/10
**Estimated Time:** 2-3 hours

---

## BUSINESS CONTEXT

### Problem Description
The current logging implementation does not match the documented requirements for structured logging and log levels. This affects system observability, debugging capabilities, and production monitoring.

### Business Goals
- Ensure consistent logging across development and production environments
- Enable proper log analysis and monitoring for system health
- Maintain security by not exposing sensitive information in logs
- Support debugging during development while reducing noise in production

### Target Audience
- **Primary:** Developers (for debugging and monitoring)
- **Secondary:** System administrators (for production monitoring)
- **Tertiary:** DevOps team (for log aggregation and alerting)

### Business Value
- Improved debugging efficiency during development
- Better production monitoring and issue detection
- Compliance with logging standards for maintainability
- Reduced log storage costs by appropriate level filtering

---

## TECHNICAL SPECIFICATION

### Functional Requirements

#### Main Functionality
Fix logging configuration to match documented requirements:
1. Implement JSON structured logging for file outputs
2. Configure appropriate log levels per environment (DEBUG for dev, WARNING for prod)
3. Ensure all log statements include required structured fields

#### Detailed Requirements

1. **JSON Structured Logging**
   - Description: File logs must be in JSON format with consistent structure
   - Input data: Log messages with structured data (user_id, action, etc.)
   - Output data: JSON log entries with timestamp, level, message, and extra fields
   - Constraints: Must include standard fields (timestamp, level, user_id where applicable)

2. **Environment-Based Log Levels**
   - Description: Console and file log levels must respect environment settings
   - Input data: `environment` setting ("development" or "production")
   - Output data: Appropriate log filtering (DEBUG for dev, WARNING for prod)
   - Constraints: File logs should never be more verbose than console logs

3. **Structured Log Fields**
   - Description: All log statements should include relevant context fields
   - Required fields: timestamp, level, user_id (when applicable), action, duration_ms (for operations)
   - Optional fields: lesson_id, error details, context data
   - Constraints: No sensitive data (API keys, personal information) in logs

### Non-Functional Requirements

#### Performance
- Log operations should not impact application performance (<1ms per log entry)
- JSON serialization should be efficient for high-frequency logging
- Log file rotation should not cause application pauses

#### Security
- No API keys, tokens, or sensitive user data in log messages
- Log files should have appropriate permissions (readable by application only)
- Log content should not expose system vulnerabilities

#### Reliability
- Logging failures should not crash the application
- Log buffering should handle temporary disk I/O issues
- Structured logging should validate JSON format

#### Compatibility
- Must work with existing loguru-based logging throughout the codebase
- Should integrate with potential future log aggregation systems
- Must support loguru's structured logging features (kwargs)

---

## TECHNICAL CONTEXT

### System Architecture
```
Logging System
├── Console Output (colored, human-readable)
│   ├── Development: DEBUG level
│   └── Production: WARNING level
└── File Output (JSON structured)
    ├── Development: DEBUG level
    └── Production: WARNING level
        └── Fields: timestamp, level, user_id, action, etc.
```

### Technology Stack
- **Logging Library:** loguru (already in use)
- **Configuration:** Pydantic Settings (environment-based)
- **File Format:** JSON for structured logging
- **Rotation:** Daily rotation with 30-day retention

### Project Structure
```
src/promptheus/
├── main.py                    ← Logging configuration here
├── config/
│   └── settings.py            ← Environment settings
├── data/
│   └── async_repositories.py  ← Repository logging
├── core/
│   ├── progress_tracker.py    ← Business logic logging
│   └── dependency_container.py ← Container logging
└── bot/
    └── assessment_handlers.py ← Handler logging
```

### Files to Modify

1. **`src/promptheus/main.py`**
   - Purpose: Main logging configuration
   - Where to make changes: `configure_logging()` function
   - Notes: Update file handler to use JSON format and environment-based levels

2. **`src/promptheus/config/settings.py`**
   - Purpose: Application settings
   - Where to make changes: Add log level configuration per environment
   - Notes: May need to add computed properties for log levels

### Related Components
- **Settings System:** Environment detection and configuration loading
- **Repository Layer:** Database operation logging (already partially structured)
- **Business Logic:** Progress tracking and assessment logging
- **Error Handling:** Exception logging in handlers

---

## EXAMPLES AND DOCUMENTATION

### Code Examples

#### Current Implementation (Problematic)
```python
# main.py - Current file handler
logger.add(
    "logs/promptheus_{time:YYYY-MM-DD}.log",
    rotation="00:00",
    retention="30 days",
    level="DEBUG",  # Always DEBUG - ignores environment!
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    serialize=False,  # Not JSON!
)
```

#### Desired Implementation
```python
# main.py - Fixed file handler
file_log_level = "DEBUG" if settings.environment == "development" else "WARNING"

logger.add(
    "logs/promptheus_{time:YYYY-MM-DD}.log",
    rotation="00:00",
    retention="30 days",
    level=file_log_level,  # Environment-aware
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    serialize=True,  # JSON format!
)
```

#### Current Repository Logging (Good Example)
```python
# async_repositories.py - Already structured
logger.info("User created successfully", telegram_id=telegram_id)
logger.warning("Cannot update skill level: user not found", telegram_id=telegram_id)
```

### Documentation
- [TRD §8.2: Logging Standards](../docs/technical-requirements-document.md#82-logging-requirements)
- [Loguru Documentation](https://loguru.readthedocs.io/en/stable/api/logger.html#loguru.Logger.add)
- [JSON Logging Best Practices](https://www.structlog.org/en/stable/)

### Existing Patterns
- **Structured Logging:** Already used in repositories with kwargs (user_id, lesson_id, etc.)
- **Environment Detection:** `settings.environment` used for other conditional logic
- **Loguru Configuration:** Centralized in `configure_logging()` function
- **File Rotation:** Daily rotation with retention already implemented

### Known Pitfalls
⚠️ **Important:**
- JSON serialization can fail with complex objects - ensure all log data is serializable
- Environment detection must be reliable - test both dev and prod configurations
- Loguru's serialize=True changes format completely - verify log parsing tools can handle it
- File permissions may prevent log writing - ensure proper directory permissions
- Performance impact of JSON serialization - monitor in high-frequency logging scenarios

---

## ACCEPTANCE CRITERIA

### Scenario Criteria (Given-When-Then)

#### Scenario 1: Development environment logging
```gherkin
Given application is running in development environment
When logging occurs at DEBUG level
Then console shows DEBUG messages with colors
And file contains JSON-formatted DEBUG logs
And logs include structured fields (user_id, action, etc.)
```

#### Scenario 2: Production environment logging
```gherkin
Given application is running in production environment
When logging occurs at DEBUG level
Then console shows only WARNING and above
And file contains only WARNING and above in JSON format
And DEBUG messages are filtered out
```

#### Scenario 3: Structured log parsing
```gherkin
Given a log file with JSON entries
When parsing the log file
Then each entry is valid JSON
And contains timestamp, level, message fields
And contains extra fields as structured data
```

### Rules and Constraints
- [ ] File logs must be in JSON format (serialize=True)
- [ ] Console logs remain human-readable with colors
- [ ] Development: both console and file show DEBUG level
- [ ] Production: both console and file show WARNING level
- [ ] All existing structured logging (kwargs) continues to work
- [ ] No sensitive data in logs (API keys, personal info)
- [ ] Log files rotate daily and retain 30 days

### Testing
- [ ] Unit tests for logging configuration function
- [ ] Integration tests verify log levels per environment
- [ ] Manual testing: check log files in both environments
- [ ] JSON validation: ensure log files contain valid JSON
- [ ] Performance test: logging doesn't impact response times

### Code Review
- [ ] Logging configuration follows existing patterns
- [ ] Environment detection is robust
- [ ] JSON serialization doesn't break existing log statements
- [ ] Error handling for log file I/O issues
- [ ] No hardcoded values (use settings)

### Performance
- [ ] JSON serialization adds <1ms per log entry
- [ ] Log file writing doesn't block application threads
- [ ] Memory usage for log buffering remains reasonable

---

## IMPLEMENTATION PLAN

### Execution Stages

#### Stage 1: Update logging configuration
**Description:** Modify the `configure_logging()` function to use environment-aware levels and JSON serialization
**Tasks:**
- [ ] Analyze current `configure_logging()` implementation
- [ ] Add environment-based log level determination
- [ ] Change file handler to use `serialize=True`
- [ ] Test configuration changes locally

**Validation:**
- Console logging works in both environments
- File logging produces valid JSON
- Log levels are correctly applied

#### Stage 2: Update settings (if needed)
**Description:** Ensure settings support proper log level configuration
**Tasks:**
- [ ] Review current settings structure
- [ ] Add computed properties for log levels if needed
- [ ] Update settings validation

**Validation:**
- Settings load correctly in both environments
- Log level computation works as expected

#### Stage 3: Testing and validation
**Description:** Verify the changes work correctly across environments
**Tasks:**
- [ ] Test development environment (DEBUG level logging)
- [ ] Test production environment (WARNING level logging)
- [ ] Validate JSON log format
- [ ] Check existing structured logging still works

**Validation:**
- All acceptance criteria met
- No regressions in existing functionality
- Performance impact is minimal

---

## TESTING AND VALIDATION

### Unit Tests
```python
# tests/test_logging.py
import json
import tempfile
from pathlib import Path

import pytest
from loguru import logger

from promptheus.config import get_settings
from promptheus.main import configure_logging


@pytest.mark.parametrize("environment,expected_level", [
    ("development", "DEBUG"),
    ("production", "WARNING"),
])
def test_configure_logging_respects_environment(environment, expected_level):
    """Test that logging configuration uses correct level per environment."""
    # Given
    settings = get_settings()
    original_env = settings.environment
    
    # Mock environment
    settings.environment = environment
    
    # When
    configure_logging()
    
    # Then
    # Check that file handler has correct level
    # (This requires inspecting logger handlers, may need refactoring for testability)
    
    # Cleanup
    settings.environment = original_env


def test_file_logging_produces_valid_json():
    """Test that file logs are valid JSON."""
    # Given
    with tempfile.TemporaryDirectory() as temp_dir:
        log_file = Path(temp_dir) / "test.log"
        
        # Configure logging to temp file
        logger.add(
            log_file,
            level="INFO",
            serialize=True,
            format="{time} | {level} | {message}"
        )
        
        # When
        logger.info("Test message", user_id=123, action="test")
        
        # Then
        log_content = log_file.read_text()
        log_lines = log_content.strip().split('\n')
        assert len(log_lines) == 1
        
        log_entry = json.loads(log_lines[0])
        assert "timestamp" in log_entry
        assert log_entry["level"] == "INFO"
        assert log_entry["message"] == "Test message"
        assert log_entry["extra"]["user_id"] == 123
        assert log_entry["extra"]["action"] == "test"
```

### Commands to Run
```bash
# Test logging configuration
pytest tests/test_logging.py -v

# Test with development settings
ENVIRONMENT=development python -c "from promptheus.main import configure_logging; configure_logging()"

# Test with production settings
ENVIRONMENT=production python -c "from promptheus.main import configure_logging; configure_logging()"

# Validate JSON logs
python -c "
import json
with open('logs/promptheus_$(date +%Y-%m-%d).log', 'r') as f:
    for line in f:
        json.loads(line.strip())  # Should not raise exception
print('All log entries are valid JSON')
"

# Check log levels
grep -c 'DEBUG' logs/promptheus_$(date +%Y-%m-%d).log  # Should be 0 in production
```

### Manual Testing Scenarios

1. **Development environment**
   - Set `ENVIRONMENT=development`
   - Start application
   - Check console shows DEBUG messages
   - Check log file contains DEBUG messages in JSON format

2. **Production environment**
   - Set `ENVIRONMENT=production`
   - Start application
   - Check console shows only WARNING/ERROR
   - Check log file contains only WARNING/ERROR in JSON format

3. **JSON validation**
   - Parse log file with Python JSON parser
   - Verify all entries have required fields
   - Check that structured data (user_id, action) is preserved

---

## ADDITIONAL CONSIDERATIONS

### Risks
- **JSON serialization breaking existing logs:** Some data types may not serialize
- **Performance impact:** JSON serialization is slower than plain text
- **Log aggregation tools:** May need configuration updates for JSON format
- **File size increase:** JSON format is more verbose than plain text

### Assumptions
- Loguru's JSON serialization is compatible with monitoring tools
- Environment variable `ENVIRONMENT` is reliably set
- Log directory has write permissions
- No existing log parsing scripts depend on plain text format

### Limitations
- Console logs remain human-readable (not JSON) for development convenience
- Log rotation and retention settings remain unchanged
- Only affects file logging format, not console logging

### Future Improvements
- [ ] Add log sampling for high-frequency operations
- [ ] Implement log aggregation to external service (ELK stack)
- [ ] Add request ID tracing across log entries
- [ ] Implement structured logging middleware for HTTP requests

---

## COMPLETION CHECKLIST

### Development
- [ ] `configure_logging()` function updated with environment-aware levels
- [ ] File handler uses `serialize=True` for JSON format
- [ ] Settings properly determine log levels per environment
- [ ] Error handling for log configuration failures
- [ ] Documentation updated to reflect JSON log format

### Testing
- [ ] Unit tests for logging configuration
- [ ] Integration tests for both environments
- [ ] JSON format validation
- [ ] Performance impact assessment
- [ ] Manual testing in dev and prod environments

### Documentation
- [ ] Code comments updated for new configuration
- [ ] README updated if log format affects users
- [ ] API documentation updated if logging format affects integrations

### Code Quality
- [ ] Ruff linting passes
- [ ] Type hints added where needed
- [ ] No TODO/FIXME comments added
- [ ] Code review completed

### Finalization
- [ ] Changes committed with clear message
- [ ] Pull request created and approved
- [ ] CI/CD pipeline passes
- [ ] Deployed to staging and validated
- [ ] Production deployment completed
- [ ] Monitoring confirms correct log levels and format