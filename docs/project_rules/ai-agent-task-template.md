# Technical Task Template for AI Agent

> **Version:** 1.0.0  
> **Created:** 2025-11-05  
> **Purpose:** Universal template document for assigning tasks to AI agents

---

## 📋 Table of Contents

1. [About the Template](#about-the-template)
2. [Document Structure](#document-structure)
3. [Usage Rules](#usage-rules)
4. [Example of Completion](#example-of-completion)

---

## About the Template

### Goal

This template serves to create clear, structured technical tasks for AI agents, ensuring:
- **Clarity of execution plan**
- **Understanding of business goals** and requirements
- **Checklist** for verification of completion
- **Sufficient context** for successful implementation

### Philosophy of Context Engineering

The template is based on the principles of **Context Engineering** — a disciplined approach to creating context for AI agents. Unlike simple "prompt engineering", Context Engineering provides AI with a complete information environment for solving the task.

**Key principle:** Garbage In, Garbage Out
- The higher quality the context — the better the result
- AI agent cannot read minds — it needs details
- Treat AI as a new developer who needs a detailed briefing

---

## Document Structure

Each task assignment to an AI agent should include the following sections:

### 1. METADATA

```markdown
## METADATA

**Task ID:** [Unique identifier]
**Name:** [Brief task description]
**Created:** [YYYY-MM-DD]
**Priority:** [Critical/High/Medium/Low]
**Complexity Estimate:** [1-10]
**Estimated Time:** [Estimate in hours]
```

### 2. BUSINESS CONTEXT

```markdown
## BUSINESS CONTEXT

### Problem Description
[Clearly describe the problem or need that the task solves]

### Business Goals
- [Goal 1]
- [Goal 2]
- [Goal 3]

### Target Audience
[Who will use the result: users, developers, managers, etc.]

### Business Value
[What value will the implementation bring: time savings, UX improvement, conversion growth, etc.]
```

### 3. TECHNICAL SPECIFICATION

```markdown
## TECHNICAL SPECIFICATION

### Functional Requirements

#### Main Functionality
[Describe in detail what should be implemented]

**Example:**
- As a user, I want to [action], so that [goal]
- As a developer, I want to [action], so that [goal]

#### Detailed Requirements
1. **[Requirement 1]**
   - Description: [Detailed description]
   - Input data: [What is the input]
   - Output data: [What is the output]
   - Constraints: [Any constraints]

2. **[Requirement 2]**
   - [Similarly]

### Non-Functional Requirements

#### Performance
- [Speed requirements]
- [Load requirements]

#### Security
- [Authentication requirements]
- [Data processing requirements]
- [Logging requirements]

#### Reliability
- [Error handling requirements]
- [Recovery requirements]

#### Compatibility
- [Compatibility with existing systems]
- [Technology versions]
```

### 4. TECHNICAL CONTEXT

```markdown
## TECHNICAL CONTEXT

### System Architecture
[Description of the project's overall architecture]

```
[ASCII diagram or link to documentation]
```

### Technology Stack
- **Backend:** [Technologies]
- **Frontend:** [Technologies]
- **Database:** [Technologies]
- **Infrastructure:** [Technologies]

### Project Structure
```
project/
├── src/
│   ├── [description of structure]
│   └── ...
├── tests/
└── ...
```

### Files to Modify
1. **`path/to/file1.py`**
   - Purpose: [What this file does]
   - Where to make changes: [Specific functions/classes]
   - Notes: [Important details]

2. **`path/to/file2.py`**
   - [Similarly]

### Related Components
- [Component 1]: [How related to the task]
- [Component 2]: [How related to the task]
```

### 5. EXAMPLES AND DOCUMENTATION

```markdown
## EXAMPLES AND DOCUMENTATION

### Code Examples
[Provide examples of similar implementations in the project]

#### Example 1: [Name]
```python
# Example code demonstrating the pattern
def example_function():
    pass
```
**Explanation:** [Why this example is important]

### Documentation
- [Link to official API documentation]
- [Link to internal project documentation]
- [Link to specifications]

### Existing Patterns
[Describe patterns already used in the project]
- Pattern 1: [Description and where it's used]
- Pattern 2: [Description and where it's used]

### Known Pitfalls
⚠️ **Important:**
- [Common mistake 1 and how to avoid it]
- [Common mistake 2 and how to avoid it]
- [Project-specific gotchas]
```

### 6. ACCEPTANCE CRITERIA

```markdown
## ACCEPTANCE CRITERIA

### Scenario Criteria (Given-When-Then)

#### Scenario 1: [Name]
```gherkin
Given [Initial condition/context]
When [User action]
Then [Expected result]
And [Additional checks]
```

#### Scenario 2: [Name]
```gherkin
Given [Initial condition]
When [Action]
Then [Result]
```

### Rules and Constraints
- [ ] [Rule 1: what should always be executed]
- [ ] [Rule 2: data validation]
- [ ] [Rule 3: error handling]

### Testing
- [ ] All unit tests pass successfully
- [ ] Test coverage >= [X%]
- [ ] Integration tests pass successfully
- [ ] Manual testing completed

### Code Review
- [ ] Code conforms to project style guide
- [ ] No hardcoded values
- [ ] Necessary comments added
- [ ] Documentation updated

### Performance
- [ ] Operation execution time <= [X seconds]
- [ ] Memory usage <= [X MB]
- [ ] No memory leaks
```

### 7. IMPLEMENTATION PLAN

```markdown
## IMPLEMENTATION PLAN

### Execution Stages

#### Stage 1: [Name]
**Description:** [What we're doing]
**Tasks:**
- [ ] Task 1.1
- [ ] Task 1.2
- [ ] Task 1.3

**Validation:**
- Stage verification criterion

#### Stage 2: [Name]
**Description:** [What we're doing]
**Tasks:**
- [ ] Task 2.1
- [ ] Task 2.2

**Validation:**
- Stage verification criterion

### Action Order
1. [First step]
2. [Second step]
3. [Third step]

### Dependencies
- [Dependency 1]: must be completed before start
- [Dependency 2]: must be completed before stage N
```

### 8. TESTING AND VALIDATION

```markdown
## TESTING AND VALIDATION

### Unit Tests
```python
# Examples of tests that should be written
def test_example():
    # Given
    input_data = ...
    
    # When
    result = function_to_test(input_data)
    
    # Then
    assert result == expected_output
```

### Commands to Run
```bash
# Command to run tests
pytest tests/test_feature.py

# Command to check coverage
pytest --cov=src tests/

# Command for linter
ruff check src/
```

### Manual Testing Scenarios
1. **Scenario 1:** [Description]
   - Steps: [Step by step]
   - Expected result: [What should happen]

2. **Scenario 2:** [Description]
   - Steps: [Step by step]
   - Expected result: [What should happen]
```

### 9. ADDITIONAL CONSIDERATIONS

```markdown
## ADDITIONAL CONSIDERATIONS

### Risks
- **Risk 1:** [Risk description and mitigation plan]
- **Risk 2:** [Risk description and mitigation plan]

### Assumptions
- [Assumption 1]
- [Assumption 2]

### Limitations
- [Limitation 1]
- [Limitation 2]

### Future Improvements
[What can be improved in the future, but not included in the current task]
- [Improvement 1]
- [Improvement 2]

### Questions and Unresolved Issues
- [ ] [Question 1 requiring clarification]
- [ ] [Question 2 requiring solution]
```

### 10. COMPLETION CHECKLIST

```markdown
## COMPLETION CHECKLIST

### Development
- [ ] Code written and meets requirements
- [ ] Error handling implemented
- [ ] Input data validation added
- [ ] Logging configured

### Testing
- [ ] Unit tests written
- [ ] Integration tests written
- [ ] All tests pass
- [ ] Code coverage >= [X%]

### Documentation
- [ ] Code documented (docstrings)
- [ ] README updated
- [ ] API documentation updated
- [ ] Changelog updated

### Code Quality
- [ ] Linter reports no errors
- [ ] Code review passed
- [ ] No TODO/FIXME in code
- [ ] Security verified

### Finalization
- [ ] Changes committed with clear messages
- [ ] Pull request created
- [ ] CI/CD pipeline passes
- [ ] Task marked as "Ready for Review"
```

---

## Usage Rules

### For Task Creator

#### 1. Be as Specific as Possible

❌ **Bad:**
```markdown
## TECHNICAL SPECIFICATION
Create a user authentication system.
```

✅ **Good:**
```markdown
## TECHNICAL SPECIFICATION
Create a user authentication system using JWT tokens,
with support for refresh tokens, OAuth2 integration (Google, GitHub),
rate limiting to prevent brute force attacks,
and logging of all authentication attempts for security audit.
```

#### 2. Provide Examples

Always include examples of:
- Existing code from the project
- Desired behavior
- Data formats
- API endpoints

#### 3. Specify File Paths

❌ **Bad:** "Change the settings file"

✅ **Good:** 
```markdown
File: `src/promptheus/core/config/settings.py`
Function: `get_database_settings()`
Lines: 45-67
```

#### 4. Describe Context

- Why is this task important?
- How is it connected to other parts of the system?
- What dependencies exist?
- What could go wrong?

#### 5. Define Success Criteria

Be specific in acceptance criteria:
- Use Given-When-Then for scenarios
- Add measurable metrics
- Define boundaries (no more than X seconds, at least Y%)

### For AI Agent

#### 1. Carefully Review the Entire Document

- Read the document completely before starting
- Pay attention to the "Known Pitfalls" section
- Study the code examples

#### 2. Follow the Implementation Plan

- Execute stages sequentially
- Perform validation after each stage
- Mark completed tasks

#### 3. Adhere to Project Standards

- Use existing patterns
- Follow the style guide
- Apply the same libraries and approaches

#### 4. Validate at Every Step

- Run tests after each change
- Check with linter
- Ensure you haven't broken existing functionality

#### 5. Iterate on Errors

- If tests fail — fix and retry
- If unexpected issues arise — analyze and adapt the plan
- Don't skip failed validations

### General Principles

#### Principle 1: Context Completeness

Each section should be filled in. If a section doesn't apply — indicate "N/A" with an explanation.

#### Principle 2: Specificity > Generality

Always choose specific formulations instead of general ones.

#### Principle 3: Measurability

All criteria must be verifiable and measurable.

#### Principle 4: Traceability

It should be possible to track whether each requirement has been met.

---

## Example of Completion

### Example: Adding User Progress Export Feature

```markdown
## METADATA

**Task ID:** PRMT-145
**Name:** Add user progress export to CSV
**Created:** 2025-11-05
**Priority:** Medium
**Complexity Estimate:** 6/10
**Estimated Time:** 4-6 hours

---

## BUSINESS CONTEXT

### Problem Description
Users and administrators cannot export learning progress data for analysis
in external tools (Excel, BI systems). This hinders learning effectiveness
analysis and decision-making.

### Business Goals
- Provide users with the ability to analyze their progress
- Give administrators a reporting tool
- Improve data transparency in learning

### Target Audience
- **Primary:** End users of the platform
- **Secondary:** Administrators and managers

### Business Value
- Increase user satisfaction (requested by 15+ users)
- Simplify report creation for administrators
- Competitive advantage (competitors have this feature)

---

## TECHNICAL SPECIFICATION

### Functional Requirements

#### Main Functionality
As a user, I want to export my learning progress to a CSV file,
so that I can analyze data in Excel or other tools.

#### Detailed Requirements

1. **API Endpoint for Export**
   - Description: Create endpoint `/api/v1/users/{user_id}/progress/export`
   - Input data: 
     - `user_id` (path parameter)
     - `format` (query parameter, default: 'csv', future: 'json', 'xlsx')
     - `date_from` (query parameter, optional)
     - `date_to` (query parameter, optional)
   - Output data: CSV file with headers
   - Constraints: 
     - Only authenticated users
     - User can export only their own data (or all if admin)
     - Maximum export period: 1 year

2. **CSV File Format**
   - Columns:
     - `lesson_id`: Lesson ID
     - `lesson_title`: Lesson title
     - `category`: Category (beginner/intermediate/advanced)
     - `completion_date`: Completion date (ISO 8601)
     - `score`: Score (0-100)
     - `time_spent_minutes`: Time spent on lesson
     - `attempts`: Number of attempts
   - Encoding: UTF-8
   - Delimiter: comma
   - Date format: YYYY-MM-DD HH:MM:SS

3. **UI Component**
   - "Export to CSV" button on progress page
   - On click — automatic file download
   - File name: `progress_export_{user_id}_{timestamp}.csv`

### Non-Functional Requirements

#### Performance
- CSV generation for 1000 records <= 2 seconds
- Endpoint should support up to 10 concurrent requests

#### Security
- Access rights check via `@require_auth` decorator
- user_id validation to prevent IDOR
- Logging of all export requests

#### Reliability
- Graceful handling when no data exists (empty CSV with headers)
- Database error handling with clear messages
- Retry logic for temporary database failures

---

## TECHNICAL CONTEXT

### System Architecture
```
┌─────────────┐      ┌──────────────┐      ┌──────────────┐
│  Frontend   │─────▶│   FastAPI    │─────▶│  PostgreSQL  │
│  (React)    │      │   Backend    │      │   Database   │
└─────────────┘      └──────────────┘      └──────────────┘
                            │
                            ▼
                     ┌──────────────┐
                     │ Export       │
                     │ Service      │
                     └──────────────┘
```

### Technology Stack
- **Backend:** Python 3.12, FastAPI, SQLAlchemy, Pydantic
- **Database:** PostgreSQL 15
- **Testing:** pytest, pytest-cov

### Project Structure
```
src/promptheus/
├── api/
│   └── v1/
│       └── endpoints/
│           └── users.py          ← Add endpoint here
├── services/
│   └── export_service.py         ← CREATE: new service
├── models/
│   └── user_progress.py          ← Use existing model
└── schemas/
    └── export_schemas.py         ← CREATE: Pydantic schemas
```

### Files to Modify

1. **`src/promptheus/api/v1/endpoints/users.py`**
   - Purpose: Definition of API endpoints for users
   - Where to make changes: Add new endpoint after existing ones
   - Notes: Use existing pattern with `APIRouter`

2. **`src/promptheus/services/export_service.py`** (CREATE)
   - Purpose: Business logic for data export
   - Notes: Isolate CSV generation logic from API layer

3. **`src/promptheus/schemas/export_schemas.py`** (CREATE)
   - Purpose: Pydantic schemas for export request validation

4. **`tests/services/test_export_service.py`** (CREATE)
   - Purpose: Unit tests for export service

---

## EXAMPLES AND DOCUMENTATION

### Code Examples

#### Example 1: Existing endpoint in users.py
```python
@router.get("/{user_id}/progress", response_model=UserProgressResponse)
async def get_user_progress(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> UserProgressResponse:
    """Get user's learning progress."""
    # Authorization check
    if current_user.id != user_id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Access denied")
    
    progress = await progress_service.get_progress(db, user_id)
    return progress
```

**Explanation:** Use this pattern for authorization checks

#### Example 2: CSV generation in another project (reference)
```python
import csv
from io import StringIO
from fastapi.responses import StreamingResponse

def generate_csv(data: list[dict]) -> StreamingResponse:
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=data[0].keys())
    writer.writeheader()
    writer.writerows(data)
    output.seek(0)
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=export.csv"}
    )
```

### Documentation
- [FastAPI Response Types](https://fastapi.tiangolo.com/advanced/custom-response/)
- [Python CSV Module](https://docs.python.org/3/library/csv.html)
- [Promptheus API Docs](../system-architecture-document.md)

### Existing Patterns
- **Dependency Injection:** Using `Depends()` for DB, auth
- **Service Layer:** Business logic in `services/`, not in endpoints
- **Error Handling:** Using `HTTPException` with clear detail
- **Testing:** Pytest with fixtures in `conftest.py`

### Known Pitfalls
⚠️ **Important:**
- Database queries for large volumes — use pagination in SQLAlchemy
- CSV encoding issues — always explicitly specify UTF-8
- Don't forget to add endpoint to router in `api/v1/__init__.py`
- Test with real Cyrillic data

---

## ACCEPTANCE CRITERIA

### Scenario Criteria

#### Scenario 1: Successful data export
```gherkin
Given user is authenticated and has completed lessons
When user sends GET /api/v1/users/123/progress/export
Then system returns CSV file
And file contains correct headers
And file contains all user's progress records
And HTTP status code is 200
And Content-Type: text/csv
```

#### Scenario 2: Export with date filtering
```gherkin
Given user is authenticated
When user sends request with date_from=2025-01-01&date_to=2025-11-01
Then system returns only records in the specified range
And all dates in the file are between date_from and date_to
```

#### Scenario 3: Attempt to access others' data
```gherkin
Given user with user_id=123 is authenticated
When user requests /api/v1/users/456/progress/export
Then system returns HTTP 403 Forbidden
And export attempt is logged for audit
```

### Rules and Constraints
- [ ] Only authenticated users can export data
- [ ] Regular users can export only their own data
- [ ] Administrators can export data of any user
- [ ] Date range cannot exceed 1 year
- [ ] CSV file always in UTF-8 encoding

### Testing
- [ ] Unit tests cover export_service (>= 90%)
- [ ] Integration tests for endpoint
- [ ] Test with empty data (no progress)
- [ ] Test with large data volume (1000+ records)
- [ ] Test with Cyrillic characters
- [ ] Test access rights verification

### Code Review
- [ ] Code conforms to PEP 8
- [ ] Type hints added everywhere (type hints)
- [ ] Docstrings in Google style for all functions
- [ ] No hardcoding (magic numbers, strings)

### Performance
- [ ] CSV generation for 1000 records <= 2 seconds
- [ ] Memory usage <= 100MB for any export

---

## IMPLEMENTATION PLAN

### Execution Stages

#### Stage 1: Creating the service layer
**Description:** Implement CSV generation logic
**Tasks:**
- [ ] Create `export_service.py`
- [ ] Implement `generate_progress_csv()`
- [ ] Add date filtering function
- [ ] Write unit tests for the service

**Validation:**
- All unit tests pass
- Coverage >= 90%

#### Stage 2: API endpoint
**Description:** Create REST API endpoint
**Tasks:**
- [ ] Add endpoint to `users.py`
- [ ] Implement parameter validation
- [ ] Add authorization check
- [ ] Configure StreamingResponse

**Validation:**
- Endpoint accessible via Swagger UI
- Manual testing with Postman successful

#### Stage 3: Testing
**Description:** Complete functionality testing
**Tasks:**
- [ ] Write integration tests
- [ ] Test with large data
- [ ] Test Cyrillic characters
- [ ] Test edge cases

**Validation:**
- All tests pass
- No errors on edge cases

#### Stage 4: Documentation
**Description:** Update documentation
**Tasks:**
- [ ] Add endpoint description to API docs
- [ ] Update README
- [ ] Add usage examples

**Validation:**
- Documentation is current
- Examples work correctly

---

## TESTING AND VALIDATION

### Unit Tests
```python
# tests/services/test_export_service.py
import pytest
from src.promptheus.services.export_service import generate_progress_csv

def test_generate_csv_with_data(sample_progress_data):
    """Test CSV generation with valid data."""
    # Given
    progress_data = sample_progress_data
    
    # When
    csv_content = generate_progress_csv(progress_data)
    
    # Then
    assert "lesson_id,lesson_title" in csv_content
    assert len(csv_content.split('\n')) == len(progress_data) + 2  # header + data + empty line

def test_generate_csv_empty_data():
    """Test CSV generation with no data."""
    # Given
    progress_data = []
    
    # When
    csv_content = generate_progress_csv(progress_data)
    
    # Then
    assert "lesson_id,lesson_title" in csv_content  # Headers still present
    assert len(csv_content.split('\n')) == 2  # Only header + empty line
```

### Commands to Run
```bash
# Run all tests
pytest

# Run only export tests
pytest tests/services/test_export_service.py -v

# With coverage
pytest --cov=src/promptheus/services/export_service tests/services/test_export_service.py

# Linter
ruff check src/promptheus/services/export_service.py
ruff check src/promptheus/api/v1/endpoints/users.py
```

### Manual Testing Scenarios

1. **Basic export**
   - Log in as user with progress
   - Open Swagger UI `/docs`
   - Execute GET /api/v1/users/{your_user_id}/progress/export
   - Check: file downloaded, opens in Excel, data correct

2. **Export with filtering**
   - Add date_from and date_to parameters
   - Check: only records in date range

3. **Attempt to access others' data**
   - Log in as user1
   - Request user2 data
   - Check: got 403 Forbidden

---

## ADDITIONAL CONSIDERATIONS

### Risks
- **Risk: Large data volume may cause timeout**
  - Mitigation: Add pagination if user has > 10000 records
  
- **Risk: Encoding issues in Windows Excel**
  - Mitigation: Test opening CSV in different Excel versions

### Assumptions
- Users will export data infrequently (no caching needed)
- Most exports will be < 1000 records
- CSV format is sufficient for MVP

### Limitations
- Only CSV format in first version (JSON/XLSX — later)
- Maximum export period: 1 year
- No option to select specific columns

### Future Improvements
- [ ] Add JSON and XLSX formats
- [ ] Scheduled exports (automatic email sending)
- [ ] Visual graphs in export
- [ ] Option to select columns for export
- [ ] API for bulk export (multiple users)

---

## COMPLETION CHECKLIST

### Development
- [ ] `export_service.py` created with CSV generation function
- [ ] Endpoint `/api/v1/users/{user_id}/progress/export` created
- [ ] Authorization check implemented
- [ ] Parameter validation added (dates)
- [ ] Date filtering implemented
- [ ] Error handling (empty data, invalid dates, etc.)
- [ ] Export request logging added

### Testing
- [ ] Unit tests for `export_service` (>= 90% coverage)
- [ ] Integration tests for endpoint
- [ ] Test: successful export with data
- [ ] Test: export empty data
- [ ] Test: date filtering
- [ ] Test: access rights verification (403)
- [ ] Test: Cyrillic characters
- [ ] Test: performance (1000 records)

### Documentation
- [ ] Docstrings added to all functions
- [ ] OpenAPI schema updated (Swagger)
- [ ] Usage examples in documentation
- [ ] CHANGELOG updated

### Code Quality
- [ ] Ruff reports no errors
- [ ] Type hints everywhere
- [ ] No TODO/FIXME in code
- [ ] Code review passed
- [ ] No security issues

### Finalization
- [ ] Branch created: `feature/PRMT-145-export-progress`
- [ ] Commits with clear messages
- [ ] Pull request created
- [ ] CI/CD pipeline passes
- [ ] Task in Jira moved to "Ready for Review"
```

---

## Template Adaptation

### For Different Task Types

#### For Bug Fix
- **Simplify "Business Context"**: focus on bug description
- **Add "Reproduction" section**: steps to reproduce
- **Acceptance Criteria**: "bug no longer reproduces"

#### For Refactoring
- **Minimize functional requirements**
- **Add "Current vs Desired" section**
- **Criteria**: cleaner code, same tests, functionality unchanged

#### For Research Task (Spike)
- **Change "Acceptance Criteria"** to "Deliverables": findings document
- **Remove "Implementation Plan"**, add "Research Plan"
- **Define time-box**: maximum time for research

### For Different Projects

#### Small Project / Simple Task
You can simplify the template, keeping:
- Metadata (minimum)
- Technical Specification
- Acceptance Criteria (Given-When-Then)
- Completion Checklist

#### Large Project / Critical Task
Use the full template, add:
- "Stakeholders" section with responsible parties
- "Impact Analysis" section for assessing impact on other systems
- Detailed rollback plan

---

## Conclusion

This template is based on modern best practices:
- **Context Engineering** — providing AI with complete context
- **PRP (Product Requirements Prompt)** — comprehensive task assignment approach
- **Given-When-Then** — clear scenario-based acceptance criteria
- **Agile/Scrum** — iterative approach with validation at each stage

**Key rule:** The quality of AI agent results is directly proportional to the quality of provided context.

Invest time in properly filling out the template — it will save hours on bug fixes and rework.

---

**Document Version:** 1.0.0  
**Last Updated:** 2025-11-05  
**Template Author:** AI Assistant based on industry best practices  
**License:** MIT (adapt for your project)
