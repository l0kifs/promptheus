# Technical Task: Fix Issues 14.1-14.2 - Docker Support and Health Check

## METADATA

**Task ID:** PRMT-141-142
**Name:** Add Docker Support, Health Check Endpoint, and FastAPI Foundation
**Created:** 2025-11-08
**Priority:** High
**Complexity Estimate:** 8/10
**Estimated Time:** 8-10 hours

## BUSINESS CONTEXT

### Problem Description
The application lacks critical production deployment capabilities and monitoring infrastructure. Issues 14.1 and 14.2 from the documentation mismatches document identify missing Docker support and health check endpoints, which are essential for reliable production deployment and system monitoring. Additionally, the architecture needs to be prepared for future API extensions with admin and user commands.

### Business Goals
- Enable containerized deployment for consistent environments
- Provide system health monitoring for production operations
- Support automated deployment and scaling
- Ensure production readiness for the bot application
- Establish FastAPI foundation for future admin and user API endpoints

### Target Audience
- **Primary:** DevOps engineers and system administrators deploying the application
- **Secondary:** Developers needing local development environments
- **Tertiary:** Monitoring systems, health check services, and future API consumers

### Business Value
- **Deployment Reliability:** Docker ensures consistent deployment across environments
- **Monitoring:** Health checks enable automated monitoring and alerting
- **Scalability:** Containerization supports horizontal scaling
- **Developer Experience:** Simplified local development setup
- **Future Extensibility:** FastAPI foundation enables admin and user API endpoints

## TECHNICAL SPECIFICATION

### Functional Requirements

#### Main Functionality
Implement Docker containerization and health check monitoring for the Promptheus Telegram bot application using FastAPI for future API extensibility.

#### Detailed Requirements

1. **Docker Containerization**
   - Description: Create Dockerfile and docker-compose.yml for containerized deployment
   - Input data: Application source code, dependencies, configuration
   - Output data: Docker image and container orchestration
   - Constraints:
     - Multi-stage build for optimized image size
     - Support for both development and production environments
     - Proper handling of SQLite database persistence
     - Environment variable configuration

2. **Health Check Endpoint**
   - Description: Implement HTTP health check endpoint at `/health` using FastAPI
   - Input data: None (GET request)
   - Output data: JSON response with system status
   - Constraints:
     - Must run alongside the Telegram bot (not replace it)
     - Check database connectivity
     - Check Telegram API reachability
     - Check OpenRouter API reachability
     - Include application version
     - Response time < 5 seconds
     - Foundation for future admin and user API endpoints

### Non-Functional Requirements

#### Performance
- Docker build time < 5 minutes
- Container startup time < 30 seconds
- Health check response time < 2 seconds
- Memory usage < 512MB per container

#### Security
- Non-root user in container
- Minimal attack surface (Alpine Linux base)
- No sensitive data in Docker layers
- Secure environment variable handling

#### Reliability
- Container must handle graceful shutdown
- Health checks must not interfere with bot operations
- Database connection pooling for health checks
- Proper error handling for external service checks

#### Compatibility
- Compatible with existing deployment infrastructure
- Support for both polling and webhook bot modes
- Environment-specific configuration

## TECHNICAL CONTEXT

### System Architecture
```
┌─────────────────┐    ┌──────────────────┐
│   Docker        │    │   Health Check   │
│  Container      │    │     Server       │
│                 │    │                  │
│ ┌─────────────┐ │    │ GET /health      │
│ │ Telegram    │ │    │                  │
│ │    Bot      │◄┼────┼──┐               │
│ │ Application │ │    │  │               │
│ └─────────────┘ │    │  │               │
│        │        │    │  │               │
│ ┌──────▼──────┐ │    │  │               │
│ │ PostgreSQL  │ │    │  │               │
│ │  Database   │ │    │  │               │
│ └─────────────┘ │    │  │               │
└─────────────────┘    │  │               │
                       │  │               │
                       └─◄┼───────────────┘
                         │
                ┌────────▼────────┐
                │ External APIs   │
                │ • Telegram API  │
                │ • OpenRouter API│
                └─────────────────┘
```
```
┌─────────────────┐    ┌──────────────────┐
│   Docker        │    │   Health Check   │
│  Container      │    │     Server       │
│                 │    │                  │
│ ┌─────────────┐ │    │ GET /health      │
│ │ Telegram    │ │    │                  │
│ │    Bot      │◄┼────┼──┐               │
│ │ Application │ │    │  │               │
│ └─────────────┘ │    │  │               │
│        │        │    │  │               │
│ ┌──────▼──────┐ │    │  │               │
│ │  Database   │ │    │  │               │
│ │ (SQLite)    │ │    │  │               │
│ └─────────────┘ │    │  │               │
└─────────────────┘    │  │               │
                       │  │               │
                       └─◄┼───────────────┘
                         │
                ┌────────▼────────┐
                │ External APIs   │
                │ • Telegram API  │
                │ • OpenRouter API│
                └─────────────────┘
```

### Technology Stack
- **Containerization:** Docker 24+, Docker Compose 2.20+
- **Base Image:** Python 3.11 Alpine Linux
- **HTTP Server:** FastAPI (async web framework for future API extensions)
- **Database:** PostgreSQL (production-ready from MVP)
- **Monitoring:** HTTP health endpoint

### Project Structure
```
promptheus/
├── Dockerfile                    ← CREATE: Multi-stage build
├── docker-compose.yml            ← CREATE: Development setup
├── docker-compose.prod.yml       ← CREATE: Production setup
├── .dockerignore                 ← CREATE: Build optimization
├── src/promptheus/
│   ├── main.py                   ← MODIFY: Add FastAPI server
│   ├── health.py                 ← CREATE: Health check logic
│   ├── api/                      ← CREATE: FastAPI routers for future admin/user APIs
│   │   └── health.py             ← CREATE: Health endpoint router
│   └── config/settings.py        ← MODIFY: Add health check settings
└── tests/
    ├── test_docker.py            ← CREATE: Docker integration tests
    └── test_health.py            ← CREATE: Health check tests
```

### Files to Modify

1. **`src/promptheus/main.py`**
   - Purpose: Main application entry point
   - Where to make changes: Add FastAPI server startup alongside bot
   - Notes: Use asyncio.gather to run both FastAPI server and Telegram bot concurrently

2. **`src/promptheus/config/settings.py`**
   - Purpose: Application configuration
   - Where to make changes: Add health check port and host settings
   - Notes: Add validation for health check configuration

3. **New Files to Create:**
   - `Dockerfile`: Multi-stage Docker build with PostgreSQL client
   - `docker-compose.yml`: Development setup with PostgreSQL service
   - `docker-compose.prod.yml`: Production setup with PostgreSQL
   - `.dockerignore`: Build context optimization
   - `src/promptheus/health.py`: Health check business logic
   - `src/promptheus/api/health.py`: FastAPI router for health endpoints
   - `tests/test_health.py`: Health check unit tests
   - `tests/test_docker.py`: Docker integration tests

### Related Components
- **Dependency Container:** Will need to provide health check service
- **Database Connection:** Health checks need database access
- **AI Client:** Health checks need to verify OpenRouter connectivity
- **Telegram Client:** Health checks need to verify Telegram API access

## EXAMPLES AND DOCUMENTATION

### Code Examples

#### Example 1: Existing asyncio application structure (main.py)
```python
async def main() -> None:
    # Initialize components
    container = DependencyContainer.get_instance()
    await container.initialize()
    
    # Create application
    application = Application.builder().token(settings.telegram_bot_token).build()
    
    # Add handlers
    # ... handler registration ...
    
    # Start bot
    await application.initialize()
    await application.start()
    await start_bot_polling(application, settings)
    
    # Keep running
    await asyncio.Event().wait()
```

**Explanation:** Need to modify this to run HTTP server alongside bot using asyncio.gather

#### Example 2: FastAPI health check endpoint (reference implementation)
```python
from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI()

@app.get("/health")
async def health_check():
    return JSONResponse({
        "status": "healthy",
        "database": "connected",
        "telegram_api": "reachable",
        "openrouter_api": "reachable",
        "version": "0.1.0"
    })
```

### Documentation
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Docker Compose](https://docs.docker.com/compose/)
- [Python Alpine Docker Images](https://hub.docker.com/_/python)

### Existing Patterns
- **Async/Await:** All I/O operations use async patterns
- **Dependency Injection:** Components receive dependencies via container
- **Error Handling:** Structured logging with context
- **Configuration:** Pydantic settings with validation

### Known Pitfalls
⚠️ **Important:**
- **Asyncio Event Loop:** FastAPI server and Telegram bot must share the same event loop
- **Port Conflicts:** Health check port must not conflict with webhook port
- **Database Connections:** Health checks should not exhaust PostgreSQL connection pool
- **External API Calls:** Health checks to external APIs should have timeouts
- **Container Security:** Use non-root user and minimal base image
- **PostgreSQL in Docker:** Proper volume mounting for data persistence and connection handling

## ACCEPTANCE CRITERIA

### Scenario Criteria (Given-When-Then)

#### Scenario 1: Successful Docker build and run
```gherkin
Given application source code and dependencies
When docker build command is executed
Then Docker image builds successfully
And container starts without errors
And bot responds to /start command
And health endpoint returns 200 status
```

#### Scenario 2: Health check with all services healthy
```gherkin
Given all external services are available
When GET request is made to /health endpoint
Then response status is 200
And response contains "status": "healthy"
And response contains "database": "connected"
And response contains "telegram_api": "reachable"
And response contains "openrouter_api": "reachable"
And response contains version information
```

#### Scenario 3: Health check with database failure
```gherkin
Given database is unreachable
When GET request is made to /health endpoint
Then response status is 503
And response contains "status": "unhealthy"
And response contains "database": "disconnected"
```

#### Scenario 4: Docker container persistence
```gherkin
Given PostgreSQL database with user data
When container is restarted
Then user data persists across restarts
And bot resumes operation normally
And database connections are properly handled
```

### Rules and Constraints
- [ ] Docker image size < 500MB
- [ ] Health check response time < 2 seconds
- [ ] Container uses non-root user
- [ ] No sensitive data in Docker image layers
- [ ] Health checks do not interfere with bot operations
- [ ] Support both polling and webhook bot modes
- [ ] Environment-specific docker-compose configurations

### Testing
- [ ] Unit tests for health check logic (>= 90% coverage)
- [ ] Integration tests for HTTP endpoint
- [ ] Docker build tests in CI/CD
- [ ] Manual testing of containerized application
- [ ] Load testing of health endpoint
- [ ] Test with external service failures

### Code Review
- [ ] Dockerfile follows security best practices
- [ ] Async code patterns consistent with existing codebase
- [ ] Error handling matches project standards
- [ ] Configuration validation added
- [ ] No hardcoded values

### Performance
- [ ] Docker build time < 5 minutes
- [ ] Container startup time < 30 seconds
- [ ] Health check response time < 2 seconds
- [ ] Memory usage < 512MB

## IMPLEMENTATION PLAN

### Execution Stages

#### Stage 1: Health Check Infrastructure
**Description:** Implement FastAPI server and health check logic with router structure
**Tasks:**
- [ ] Add FastAPI and uvicorn dependencies to pyproject.toml
- [ ] Create FastAPI health router in api/health.py
- [ ] Create health check business logic in health.py
- [ ] Add health check settings to settings.py
- [ ] Integrate FastAPI server into main.py alongside bot
- [ ] Implement database connectivity check (PostgreSQL)
- [ ] Implement external API reachability checks
- [ ] Add proper error handling and timeouts

**Validation:**
- FastAPI server starts successfully
- /health endpoint responds with correct JSON
- All health checks work in isolation

#### Stage 2: Docker Containerization
**Description:** Create Docker configuration for containerized deployment with PostgreSQL
**Tasks:**
- [ ] Create multi-stage Dockerfile with PostgreSQL asyncpg driver
- [ ] Create .dockerignore for build optimization
- [ ] Create docker-compose.yml for development with PostgreSQL service
- [ ] Create docker-compose.prod.yml for production with PostgreSQL
- [ ] Configure volume mounting for PostgreSQL data persistence
- [ ] Test Docker build and container startup

**Validation:**
- Docker image builds successfully
- Container starts and bot is operational
- PostgreSQL database connections work correctly
- Database persistence works across container restarts

#### Stage 3: Integration and Testing
**Description:** Integrate components and validate end-to-end functionality
**Tasks:**
- [ ] Write comprehensive unit tests for health checks
- [ ] Write integration tests for Docker setup
- [ ] Test health checks with service failures
- [ ] Validate docker-compose configurations
- [ ] Manual testing of complete system

**Validation:**
- All tests pass
- Docker containers work in both environments
- Health checks accurately report system status
- No performance degradation

#### Stage 4: Documentation and Optimization
**Description:** Finalize implementation and documentation
**Tasks:**
- [ ] Update README with Docker instructions
- [ ] Add health check documentation
- [ ] Optimize Docker image size
- [ ] Add docker-compose environment examples
- [ ] Update deployment documentation

**Validation:**
- Documentation is complete and accurate
- Docker setup works for new developers
- Production deployment is ready

### Action Order
1. Implement FastAPI health check router and endpoints
2. Create health check business logic
3. Add health check settings and validation
4. Integrate FastAPI server into main.py alongside bot
5. Create Dockerfile with multi-stage build and PostgreSQL client
6. Create docker-compose configurations with PostgreSQL service
7. Add .dockerignore and optimize build
8. Write comprehensive tests
9. Test integration and performance
10. Update documentation

### Dependencies
- FastAPI library for HTTP server (add to pyproject.toml)
- uvicorn for ASGI server
- PostgreSQL async driver (asyncpg)
- Docker and docker-compose installed on development machines
- PostgreSQL service in docker-compose
- External services (Telegram API, OpenRouter API) accessible during health checks

## TESTING AND VALIDATION

### Unit Tests
```python
# tests/test_health.py
@pytest.mark.asyncio
async def test_health_check_all_healthy():
    """Test health check when all services are available."""
    # Given
    health_service = HealthService(
        db_session=mock_session,
        telegram_client=mock_telegram,
        ai_client=mock_ai
    )
    
    # When
    result = await health_service.check_health()
    
    # Then
    assert result["status"] == "healthy"
    assert result["database"] == "connected"
    assert result["telegram_api"] == "reachable"
    assert result["openrouter_api"] == "reachable"

@pytest.mark.asyncio
async def test_health_check_database_failure():
    """Test health check when database is unavailable."""
    # Given
    health_service = HealthService(
        db_session=mock_failing_session,
        telegram_client=mock_telegram,
        ai_client=mock_ai
    )
    
    # When
    result = await health_service.check_health()
    
    # Then
    assert result["status"] == "unhealthy"
    assert result["database"] == "disconnected"
```

### Commands to Run
```bash
# Build Docker image
docker build -t promptheus .

# Run container
docker run -p 8080:8080 promptheus

# Test health endpoint
curl http://localhost:8080/health

# Run with docker-compose
docker compose up --build

# Run tests
pytest tests/test_health.py -v
pytest tests/test_docker.py -v
```

### Manual Testing Scenarios

1. **Docker Development Setup**
   - Clone repository
   - Run `docker compose up --build`
   - Check bot responds to commands
   - Verify health endpoint returns healthy status
   - Stop container and verify database persistence

2. **Health Check Validation**
   - Start application normally
   - Call `curl http://localhost:8080/health`
   - Verify JSON response format
   - Simulate database failure and check response
   - Simulate API failures and check response

3. **Production-like Testing**
   - Use docker-compose.prod.yml
   - Test with environment variables
   - Verify webhook mode works in container
   - Check logs and monitoring

## ADDITIONAL CONSIDERATIONS

### Risks
- **Asyncio Complexity:** Running FastAPI server and Telegram bot in same event loop
  - Mitigation: Thorough testing of concurrent operations
- **Database Connection Pooling:** Health checks might exhaust PostgreSQL connection pool
  - Mitigation: Use dedicated connection for health checks
- **External API Timeouts:** Health checks to external APIs might be slow
  - Mitigation: Short timeouts and async implementation
- **Docker Image Size:** Python applications can create large images
  - Mitigation: Multi-stage build and Alpine Linux base
- **PostgreSQL Container Management:** Database persistence and networking in Docker
  - Mitigation: Proper volume mounting and connection string configuration

### Assumptions
- Health check port (8080) won't conflict with webhook port (8443)
- External APIs support health check requests without side effects
- PostgreSQL database can be containerized with proper volume mounting
- FastAPI is compatible with existing asyncio event loop
- PostgreSQL connection pooling works correctly in containerized environment

### Limitations
- Health checks are basic connectivity tests (not full functionality tests)
- Docker setup optimized for single-container deployment with PostgreSQL
- No horizontal scaling support in initial implementation
- Health checks may consume API rate limits
- FastAPI server runs alongside bot (not as separate service)

### Future Improvements
- [ ] Add more detailed health metrics (response times, queue lengths)
- [ ] Implement admin API endpoints (user management, analytics, system control)
- [ ] Add user API endpoints (progress export, preferences, statistics)
- [ ] Implement Kubernetes health checks and probes
- [ ] Add health check for background tasks (session cleanup)
- [ ] Support for custom health check endpoints
- [ ] Integration with external monitoring services

### Questions and Unresolved Issues
- [ ] Should health checks consume API rate limits?
- [ ] What is the acceptable timeout for external API health checks?
- [ ] Should health checks be cached to reduce API calls?
- [ ] How to handle health checks during bot initialization?
- [ ] What admin API endpoints should be prioritized for future development?
- [ ] Should user API endpoints be authenticated via Telegram user ID?

## COMPLETION CHECKLIST

### Development
- [ ] FastAPI and uvicorn added to pyproject.toml dependencies
- [ ] Health check business logic implemented in health.py
- [ ] FastAPI server integrated into main.py alongside bot
- [ ] Health check settings added to settings.py with validation
- [ ] Dockerfile created with multi-stage build and PostgreSQL client
- [ ] docker-compose.yml created for development with PostgreSQL service
- [ ] docker-compose.prod.yml created for production with PostgreSQL
- [ ] .dockerignore created for build optimization
- [ ] Database volume mounting configured for PostgreSQL persistence
- [ ] Environment variable handling in containers

### Testing
- [ ] Unit tests for health check logic (>= 90% coverage)
- [ ] Integration tests for HTTP endpoint
- [ ] Docker build integration tests
- [ ] Manual testing of containerized application
- [ ] Health check testing with service failures
- [ ] Performance testing of health endpoint
- [ ] Cross-platform Docker testing (Linux/Windows)

### Documentation
- [ ] README updated with Docker setup instructions
- [ ] FastAPI health check API documented
- [ ] docker-compose usage examples added
- [ ] Environment variable documentation
- [ ] PostgreSQL connection configuration documented
- [ ] Troubleshooting guide for Docker issues

### Code Quality
- [ ] Dockerfile follows security best practices
- [ ] FastAPI async patterns consistent with existing codebase
- [ ] Error handling matches project standards
- [ ] No hardcoded values in Docker configuration
- [ ] PostgreSQL connection handling follows best practices
- [ ] Code review passed for all changes

### Finalization
- [ ] All acceptance criteria met
- [ ] Docker images pushed to registry (future)
- [ ] CI/CD pipeline updated to build Docker images
- [ ] Deployment documentation updated
- [ ] Task marked as "Ready for Review"