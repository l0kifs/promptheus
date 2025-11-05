# Plan to Fix Issue 1.1: Violation of layered architecture and dependency injection

## Issue 1.1: Layered Architecture (SAD §1, §2)

### Problem description
- **Documentation**: Clear separation into layers (Bot Interface → Application Core → AI Integration / Data Access), dependency injection, stateless design
- **Implementation**: Violation of DI (direct use of `get_db()` in handlers), creation of repositories inside methods, state is stored in memory instead of DB

### Severity: 🔴 High
- Blocks scalability and testability
- Violates SOLID principles
- Increases coupling between components

---

## Detailed Fix Plan

### Phase 1: Prepare DI infrastructure

#### 1.1 Create a dependency container
- [ ] Create class `DependencyContainer` in `src/promptheus/core/dependency_container.py`
- [ ] Implement Singleton pattern for the container
- [ ] Add methods to create and manage component lifecycles
- [ ] Integrate with `main.py` to initialize the container on startup

#### 1.2 Refactor repositories for async
- [ ] Migrate to SQLAlchemy async (sqlalchemy[asyncio])
- [ ] Change all repository methods to async
- [ ] Update `get_db()` to an async context manager
- [ ] Test async repositories

#### 1.3 Create component factories
- [ ] Create a factory for `UserRepository`
- [ ] Create a factory for `LessonRepository`
- [ ] Create a factory for `ProgressRepository`
- [ ] Create a factory for `SessionRepository`

### Phase 2: Refactor Bot Interface Layer

#### 2.1 Update BotHandlers
- [ ] Change `BotHandlers` constructor to accept dependencies via DI
- [ ] Remove all calls to `get_db()` from handlers' methods
- [ ] Replace repository creation with injection from the container
- [ ] Update all async methods to work with async repositories

#### 2.2 Update Application Core Layer
- [ ] Change `AssessmentEngine` to accept `UserRepository` via DI
- [ ] Change `ProgressTracker` to accept repositories via DI
- [ ] Change `LearningFlowOrchestrator` to accept all dependencies via DI
- [ ] Update all methods to async

#### 2.3 Update AI Integration Layer
- [ ] Ensure `OpenRouterClient` is integrated correctly
- [ ] Add `OpenRouterClient` to the dependency container
- [ ] Update injection into components that use it

### Phase 3: Implement stateless design

#### 3.1 Refactor session state
- [ ] Move all data from `context.user_data` to `UserSession.context_data`
- [ ] Create methods for serialization/deserialization of state
- [ ] Update all handlers to use DB-backed state instead of in-memory

#### 3.2 Update session recovery logic
- [ ] Change `start_command` to load state from the DB
- [ ] Add resume logic that precisely restores the user's position
- [ ] Update all callback handlers to save state to the DB

#### 3.3 Add session cleanup
- [ ] Create a background task to clean up old sessions
- [ ] Implement logic to delete sessions older than 30 days
- [ ] Add metrics to monitor the number of active sessions

### Phase 4: Testing and validation

#### 4.1 Update unit tests
- [ ] Change all tests to work with async repositories
- [ ] Add a mock for the dependency container
- [ ] Test DI in isolation

#### 4.2 Update integration tests
- [ ] Create end-to-end tests with DI
- [ ] Test stateless behavior
- [ ] Validate session persistence

#### 4.3 Manual testing
- [ ] Test the onboarding flow with bot restart
- [ ] Test lesson flow with resume capability
- [ ] Test concurrent users (if possible)

### Phase 5: Migration and deployment

#### 5.1 Prepare migration
- [ ] Create an Alembic migration to add missing indices (if needed)
- [ ] Test migration on a copy of production data
- [ ] Prepare rollback plan

#### 5.2 Update configuration
- [ ] Update `main.py` to use the new container
- [ ] Add settings for session cleanup to config
- [ ] Update Docker configuration (if present)

#### 5.3 Post-release monitoring
- [ ] Monitor DI-related errors
- [ ] Track performance of async operations
- [ ] Monitor memory usage (stateless should reduce it)

---

## Success criteria

### Functional criteria
- [ ] All handlers use DI instead of creating dependencies directly
- [ ] Session state is stored in the DB and is not lost on restart
- [ ] Async repositories work correctly
- [ ] Resume capability restores the user's exact position

### Technical criteria
- [ ] Test coverage >80% for new components
- [ ] No blocking operations in async context
- [ ] All components follow SOLID principles
- [ ] Stateless design confirmed by tests

### Quality criteria
- [ ] Code is readable and maintainable
- [ ] Logging is sufficient for debugging
- [ ] Documentation is updated (docstrings, comments)
- [ ] Performance did not degrade

---

## Risks and mitigation

### Risks
- **Downtime**: Possible issues during deployment
- **Performance**: Async may add overhead
- **Data loss**: Errors during session state migration

### Mitigation
- **Testing**: Full testing before release
- **Gradual rollout**: Feature flags for phased enabling
- **Backup**: Full backup before migration
- **Monitoring**: Detailed logging and metrics

---

## Effort estimates

### Time estimates
- Phase 1: 2-3 days (DI infrastructure)
- Phase 2: 3-4 days (layer refactor)
- Phase 3: 2-3 days (stateless design)
- Phase 4: 2-3 days (testing)
- Phase 5: 1-2 days (migration)

**Total**: 10-15 developer days

### Commands to run
```bash
# After completing each phase
pytest tests/ -v --cov
ruff check .
mypy src/

# Session tests
pytest tests/test_session_persistence.py
pytest tests/test_dependency_injection.py
```

---

## Next steps after fix

1. **Issue 1.2**: Async/await pattern (repositories sync)
2. **Issue 1.3**: Session state persistence
3. **Issue 2.1**: Rate limiting implementation
4. **Issue 4.1**: Database constraints (UNIQUE indexes)

---

**Responsible**: Architecture developer  
**Creation date**: 2025-11-04  
**Status**: Ready for implementation

