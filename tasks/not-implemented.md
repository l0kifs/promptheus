# Unimplemented features in Promptheus

> Analysis conducted: 2025-11-04
> 
> This document contains a list of functionality described in the documentation but not yet implemented in the project's code.

---

## 1. Bot Interface Layer

### 1.1 Command handlers and callbacks
- [ ] **Webhook mode** (TRD §5.1, DP §4.2) - only polling is implemented
- [ ] **Health check endpoint** (DP §5.1) - `/health` endpoint is missing
- [ ] **`/help` command** (UXD §9) - not implemented
- [ ] **`/cancel` command** (UXD §9) - not implemented
- [ ] **`/progress` command** (UXD §9) - implemented only as a callback
- [ ] **File handler** (UXD §4.2) - no file upload handling

### 1.2 Navigation and UI
- [ ] **"Back" button** in all sections (UXD §2.2, §3) - partially implemented
- [ ] **Typing indicator** (UXD §4.3) - no delay between messages
- [ ] **Message chunking** (TRD §3.3, UXD §2.1) - theory is not split into 50-80 word chunks
- [ ] **Inline hints during practice** (US §3.1) - `hint_callback` button does not show hints
- [ ] **Progress bar visualization** (UXD §3.2) - simple text instead of a visual progress bar

---

## 2. Application Core Layer

### 2.1 Learning Flow
- [ ] **Resume capability** (TRD §2.2, US §4.2) - no precise resume from the exact spot in a lesson
- [ ] **Personalization by learning_goal** (BRD, TRD §4.1) - goal is saved but not used to filter content
- [ ] **Recommendation of the next lesson** (US §2.5) - partially implemented, no intelligent choice based on progress
- [ ] **Skip lesson functionality** (UXD §3.2) - button exists but logic is not implemented

### 2.2 Content Delivery
- [ ] **Chunking theory into 50-80 words** (TRD §3.3, UXD §2.1) - content is sent whole
- [ ] **Side-by-side examples** (UXD §3.2) - shown sequentially instead of side-by-side comparison
- [ ] **Annotations for examples** (DDD §3.2) - annotations exist in JSON but are not formatted separately
- [ ] **Hint system** (US §3.1) - callback registered but function not implemented

### 2.3 Assessment
- [ ] **Adaptive questions** (BRD) - fixed list of 5 questions
- [ ] **AI-powered answer assessment** (TRD §5.1) - uses a simple count of correct answers
- [ ] **Detailed feedback per question** (US §1.2) - only final result provided

---

## 3. AI Integration Layer

### 3.1 Prompt Management
- [ ] **Prompt Template Manager** (SAD §2.3, TRD §5.2) - no centralized prompt template manager
- [ ] **Structured prompt templates** (US §6.2) - prompts are hard-coded directly in methods
- [ ] **Response validation** (SAD §2.3) - minimal validation of JSON responses

### 3.2 Model Selection
- [ ] **Exponential backoff** (TRD §3.3, SAD §7.1) - direct fallback without delay
- [ ] **Request throttling** (TRD §5.2) - no rate limiting for AI API requests
- [ ] **Model usage tracking** (TS §11.1) - model usage is not logged
- [ ] **Cost tracking** (TRD §11.1) - no token or cost accounting

### 3.3 Response Processing
- [ ] **Structured parsing** (SAD §2.3) - JSON parsing is simplified, without schema validation
- [ ] **Parsing fallback** (AssessmentEngine) - basic fallback exists but not full-featured
- [ ] **Caching AI responses** (SAD §4.1) - no caching of responses

---

## 4. Data Access Layer

### 4.1 Repository Pattern
- [ ] **Async repositories** (TRD §5, SAD §10.2) - repositories are synchronous while app is async
- [ ] **Connection pooling configuration** (DDD §6.2) - default SQLAlchemy values
- [ ] **Query optimization** (DDD §6.1) - no indexes on complex queries
- [ ] **Batch operations** (DDD §4.2) - all operations are single-row

### 4.2 Caching
- [ ] **Session state cache** (DDD §6.3, SAD §4.1) - no in-memory cache, always reads DB
- [ ] **Lesson content cache** (DDD §6.3, US §7.2) - lessons are read from DB every time
- [ ] **User progress cache** (DDD §6.3) - write-through cache not implemented

---

## 5. Database & Migrations

### 5.1 Schema
- [ ] **Composite indexes** (DDD §6.1) - no composite indexes (user_id, status), etc.
- [ ] **GIN indexes for JSON** (DDD §3.2) - not configured for PostgreSQL
- [ ] **Constraint checks** (DDD §7.1) - CHECK constraints on score (0-100) missing
- [ ] **Timestamp timezone** (DDD §5.1) - uses utcnow instead of timezone-aware timestamps

### 5.2 Data Management
- [ ] **Lesson seeding** (TRD §6.1, DDD §3.2) - script mentioned but not validated
- [ ] **Session cleanup task** (US §5.3, DDD §10.2) - no automatic cleanup of old sessions
- [ ] **Backup strategy** (DP §6) - automated backups not configured
- [ ] **Migration testing** (DP §4.4) - no downgrade tests

---

## 6. Configuration & Settings

### 6.1 Environment
- [ ] **Secrets manager integration** (DP §7.1, TRD §7) - only .env files are used
- [ ] **Multi-environment config** (DP §2) - no separate configs for dev/staging/prod
- [ ] **Config validation on startup** (DS §8.2) - partial via Pydantic, but no fail-fast checks
- [ ] **Webhook URL config** (TRD §7.1) - variable exists but is not used

### 6.2 Feature Flags
- [ ] **Session timeout** (TRD §7.2) - setting exists in settings but is not used
- [ ] **Rate limiting config** (TRD §7.2) - value exists but rate limiting not implemented
- [ ] **Message typing delay** (TRD §7.2) - no configuration for delays

---

## 7. Testing

### 7.1 Test Coverage
- [ ] **Integration tests** (TS §3.2) - only basic unit tests present
- [ ] **E2E tests** (TS §3.3) - completely absent
- [ ] **Critical path tests** (TS §4) - key scenarios not covered
- [ ] **Performance benchmarks** (TS §6) - no pytest-benchmark tests
- [ ] **Security tests** (TS §7) - no checks for SQL injection, XSS, etc.

### 7.2 Test Infrastructure
- [ ] **Test fixtures** (TS §5.1) - minimal set
- [ ] **Mock AI responses** (TS §5.1) - no fixtures for AI responses
- [ ] **Test database isolation** (TS §5.2) - no automatic rollback of transactions
- [ ] **Load testing setup** (TS §6.2) - no locust configuration

---

## 8. Monitoring & Observability

### 8.1 Logging
- [ ] **Structured logging** (TRD §8.2, DP §5.4) - partial, not all fields structured
- [ ] **Context binding** (TRD §8.2) - no context binding to request traces
- [ ] **Log rotation to cloud** (DP §5.4) - only local rotation
- [ ] **Sensitive data scrubbing** (TS §7.3) - no automatic scrubbing of secrets from logs

### 8.2 Metrics
- [ ] **Application metrics** (DP §5.2) - no collection of latency, error rate, etc.
- [ ] **Health checks** (DP §5.1) - endpoint not implemented
- [ ] **AI usage metrics** (TRD §11.1) - models, tokens, fallback rate not logged
- [ ] **User engagement metrics** (TRD §11.1) - no DAU/WAU, completion rates

### 8.3 Alerts
- [ ] **Error rate alerts** (DP §5.3) - no alerts configured
- [ ] **Performance alerts** (DP §5.3) - no latency monitoring
- [ ] **Cost alerts** (TRD §11.2) - no tracking of approaching free tier limits

---

## 9. Security

### 9.1 Input Validation
- [ ] **Telegram IP validation** (DP §7.2) - webhook does not verify the source
- [ ] **Callback data validation** (TS §7.1) - minimal validation via regex patterns
- [ ] **User input sanitization** (TS §7.1, DS §4.3) - no checks for XSS, SQL injection
- [ ] **Max input length** (TRD §3.5) - no limits on prompt length

### 9.2 Rate Limiting
- [ ] **Per-user rate limit** (TRD §3.1, US §5.2) - 10 req/min mentioned but not implemented
- [ ] **Global rate limit** (SAD §6.3) - no protection against mass requests
- [ ] **Cooldown period** (US §5.2) - not applied when rate limit is exceeded

### 9.3 Data Privacy
- [ ] **PII detection** (TS §7.3) - no log scanning for sensitive data
- [ ] **Encryption at rest** (DDD §8.1, DP §7) - not configured for SQLite/PostgreSQL
- [ ] **Session expiration** (TRD §7.2) - timeout exists but auto-cleanup does not work

---

## 10. Deployment & CI/CD

### 10.1 Infrastructure
- [ ] **Docker configuration** (DP §4.2) - mentioned but no Dockerfile
- [ ] **docker-compose.yml** (DP §4.2) - missing
- [ ] **Nginx config** (DP §10.2) - reverse proxy not configured
- [ ] **SSL/TLS setup** (DP §3.3) - not implemented

### 10.2 CI/CD Pipeline
- [ ] **GitHub Actions workflow** (DP §8, TS §11.2) - no CI/CD configuration
- [ ] **Automated testing on PR** (DP §8.1) - not configured
- [ ] **Lint & type check** (DP §8.1) - no automated checks
- [ ] **Automated deployment** (DP §8.2) - manual process

### 10.3 Deployment Procedures
- [ ] **Zero-downtime deployment** (DP §4.3) - not supported
- [ ] **Rollback mechanism** (DP §4.3) - no automatic rollback
- [ ] **Smoke tests post-deploy** (DP §8.2) - not automated
- [ ] **Database migration automation** (DP §4.4) - manual process

---

## 11. Documentation

### 11.1 Code Documentation
- [ ] **API documentation** (DS §6.1) - docstrings exist but not all functions covered
- [ ] **Architecture diagrams** (DP §12) - no up-to-date diagrams in the repo
- [ ] **Runbooks** (DP §11.2) - incident response not documented
- [ ] **Migration guide** (DP §12) - no SQLite → PostgreSQL instructions

### 11.2 User Documentation
- [ ] **README with setup** (DP §4.2) - basic README but not complete
- [ ] **Contributing guide** - missing
- [ ] **Changelog** - not maintained
- [ ] **API examples** - no usage examples for AI API

---

## 12. Content Management

### 12.1 Lesson Content
- [ ] **Lesson seeding script** (DDD §3.2, DP §4.2) - references private repo but not validated
- [ ] **Content validation** (DDD §3.2) - no JSON structure validation for lessons
- [ ] **Tag-based filtering** (DDD §3.2, TRD §4.1) - tags are stored but not used
- [ ] **Multi-language support** (BRD, DDD §11.2) - mentioned as post-MVP, not implemented

### 12.2 Content Updates
- [ ] **Hot reload lessons** (DDD §6.3) - no lesson updates without restart
- [ ] **Cache invalidation** (US §7.2) - cache not implemented so invalidation also missing
- [ ] **Content versioning** - no versioning for lessons

---

## 13. Advanced Features (Post-MVP)

### 13.1 Community Features
- [ ] **Shared prompts** (BRD, DDD §11.2) - UserPrompt table not created
- [ ] **Leaderboards** (BRD) - not implemented
- [ ] **User ratings** - absent

### 13.2 Analytics
- [ ] **User analytics dashboard** (BRD, US §8.1) - no interface to view stats
- [ ] **Lesson analytics** (US §8.1) - no metrics for completion rate
- [ ] **A/B testing** (UXD §10) - no infrastructure

### 13.3 Advanced Prompting
- [ ] **Chain-of-thought lessons** (BRD, TRD §6.2) - mentioned post-MVP
- [ ] **Meta-prompting** (BRD) - not included in MVP
- [ ] **Prompt chaining** (BRD) - future feature

---

## 14. Error Handling & Resilience

### 14.1 Error Scenarios
- [ ] **Network retry logic** (TRD §3.3, US §5.1) - no retry for Telegram API
- [ ] **Database connection retry** (US §5.1) - no automatic reconnection
- [ ] **Graceful degradation** (TRD §3.3) - partial for AI, not for other components
- [ ] **Circuit breaker** (SAD §7.1) - pattern not implemented

### 14.2 User Experience
- [ ] **Error recovery guidance** (US §5.1) - minimal error messages
- [ ] **Retry buttons** (UXD §7.1) - retry buttons not present everywhere
- [ ] **Error reporting** (US §5.1) - user cannot send error reports
- [ ] **Status pages** - no service status page

---

## Prioritization by category

### 🔴 Critical (blocks production)
- Health check endpoint
- Webhook mode
- Error handling & retry logic
- Rate limiting
- Security validation (XSS, SQL injection)
- Docker configuration

### 🟡 High (important for MVP)
- Message chunking (50-80 words)
- Resume capability (precise resume)
- Lesson seeding validation
- Integration & E2E tests
- CI/CD pipeline
- Structured logging

### 🟢 Medium (improves UX)
- Typing indicators
- Progress bar visualization
- Hint system
- Personalization by learning_goal
- Caching (sessions, lessons)
- Async repositories

### 🔵 Low (nice to have)
- Advanced prompting techniques
- Community features
- Analytics dashboard
- Multi-language support
- A/B testing

---

## Implementation recommendations

1. **Next sprint**: Focus on Critical category to prepare for production deployment
2. **MVP completion**: High category for a full MVP release
3. **Post-MVP**: Medium and Low categories after receiving user feedback

**Overall MVP progress**: ~40% of functionality implemented

- ✅ Core infrastructure (DB, models, basic handlers)
- ✅ Onboarding flow (assessment, goal selection)
- ✅ Basic lesson delivery
- ⚠️ Practice & feedback (implemented but not optimal)
- ❌ Production readiness (security, monitoring, deployment)
- ❌ Test coverage
- ❌ Advanced features
