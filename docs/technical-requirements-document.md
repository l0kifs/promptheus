# Technical Requirements Document (TRD)
## Promptheus - Telegram Bot for Prompt Engineering Education

### 1. System Architecture

#### 1.1 High-Level Components
- **Telegram Bot Layer**: User interface and interaction handler
- **Application Core**: Business logic and learning flow orchestration
- **AI Integration Layer**: OpenRouter API client and prompt management
- **Data Storage**: User progress, lessons, and assessment data
- **Configuration Management**: Environment-specific settings

#### 1.2 Technology Stack
- **Language**: Python 3.11+
- **Bot Framework**: python-telegram-bot (v20+)
- **AI API**: OpenRouter API
- **Database**: SQLite (MVP) / PostgreSQL (production)
- **ORM**: SQLAlchemy
- **Async Runtime**: asyncio
- **Configuration**: python-dotenv, Pydantic Settings

### 2. Functional Requirements

#### 2.1 User Management
- User registration on first interaction
- Skill level assessment (beginner/intermediate/advanced)
- Goal identification (academic/professional/creative)
- Session state management
- Progress persistence

#### 2.2 Learning Flow
- **Onboarding**: Welcome → Assessment → Goal Setting → Personalized Path
- **Lesson Structure**: Theory → Examples → Practice → Feedback → Next Steps
- **Navigation**: Forward/Back navigation, lesson menu, progress overview
- **Resume Capability**: Continue from last checkpoint

#### 2.3 Content Delivery
- **Theory Modules**: Bite-sized explanations (50-80 words per message, split into multiple messages if needed)
- **Examples**: Good vs. Bad prompt comparisons with brief annotations (2-3 sentences each)
- **Exercises**: Scenario-based tasks with clear objectives (max 100 words)
- **Feedback**: AI-generated evaluation with improvement suggestions (structured in 2-3 short messages)

#### 2.4 AI Integration
- **Model Selection**: Free models for MVP phase via OpenRouter
  - Primary: `meta-llama/llama-4-scout:free` (109B MoE, 512K context)
  - Fallback: `google/gemini-2.5-pro-exp:free` (1M context, advanced reasoning)
  - Alternative: `mistralai/mistral-small-3.1-24b-instruct:free` (96K context, function calling)
  - Lightweight: `qwen/qwen2.5-vl-3b-instruct:free` (3B, multimodal for examples)
- **Model Strategy**: Start with free tier, migrate to paid models based on usage metrics and revenue
- **Prompt Templates**: Structured templates for assessment, feedback, content generation
- **Response Parsing**: Extract structured data from AI responses
- **Error Handling**: Multi-model fallback chain (primary → fallback → alternative)

### 3. Non-Functional Requirements

#### 3.1 Performance
- Bot response time: < 3 seconds for standard operations
- AI response time: < 10 seconds (with loading indicators)
- Concurrent users: Support 100+ simultaneous sessions
- Database query optimization: < 100ms per query

#### 3.2 Scalability
- Stateless application design for horizontal scaling
- Database connection pooling
- Async/await pattern for I/O operations
- Rate limiting per user (10 requests/minute)

#### 3.3 Reliability
- 99% uptime target
- Graceful degradation on AI API failures
- Error logging and monitoring
- Automatic retry logic with exponential backoff

#### 3.4 Security
- Secure API key storage (environment variables)
- Input validation and sanitization
- User data encryption at rest
- HTTPS-only API communication
- No PII storage beyond Telegram user ID

#### 3.5 Usability
- Mobile-first message formatting:
  - Theory: 50-80 words (300-500 chars) per message
  - Examples: 2-3 sentences (150-200 chars) per comparison
  - Exercises: max 100 words (500-600 chars)
  - Total lesson time: 3-5 minutes reading
- Inline keyboards for all navigation
- Clear visual hierarchy with emojis and formatting
- Maximum 2 taps to reach any feature
- Message chunking: Split complex topics into 2-4 sequential messages

### 4. Data Models

#### 4.1 User
```
- telegram_id (PK)
- username
- skill_level (enum: beginner/intermediate/advanced)
- learning_goal (enum: academic/professional/creative)
- current_lesson_id (FK)
- assessment_score
- created_at, updated_at
```

#### 4.2 Lesson
```
- id (PK)
- title
- skill_level (enum: beginner/intermediate/advanced)
- order_index
- tags (JSON array: ["technique", "use_case", "topic"])
- theory_content (JSON)
- examples (JSON)
- exercises (JSON)
- created_at
```

**Tag Categories:**
- **Techniques**: `zero-shot`, `few-shot`, `role-based`, `chain-of-thought`, `context-heavy`, `formatting`
- **Use Cases**: `academic`, `professional`, `creative`, `general`
- **Topics**: `role-definition`, `context-provision`, `clear-objectives`, `output-formatting`, `iterative-refinement`, `error-detection`

#### 4.3 UserProgress
```
- id (PK)
- user_id (FK)
- lesson_id (FK)
- status (enum: not_started/in_progress/completed)
- attempts
- last_score
- completed_at
```

#### 4.4 UserSession
```
- user_id (PK)
- state (enum: onboarding/learning/practicing/menu)
- context_data (JSON)
- updated_at
```

### 5. API Integrations

#### 5.1 Telegram Bot API
- **Methods**: sendMessage, editMessageText, answerCallbackQuery
- **Webhook vs Polling**: Polling for MVP, webhook for production
- **Message Types**: Text, inline keyboards, markdown formatting

#### 5.2 OpenRouter API
- **Endpoints**: `/api/v1/chat/completions`
- **Authentication**: Bearer token
- **Rate Limits**: Free tier limits vary by model, implement request throttling
- **Models**: Free tier models with automatic fallback chain
  - Llama-4-Scout: 512K context, optimized deployment
  - Gemini-2.5-Pro-Exp: 1M context, advanced reasoning
  - Mistral-Small-3.1: Function calling support
- **Cost Strategy**: 
  - MVP: 100% free tier models ($0 cost)
  - Post-MVP: Monitor usage, migrate high-value users to paid models
  - Target: <$0.05 per user per month initially

### 6. MVP Scope

#### 5.1 MVP Scope
- 5 foundational lessons (managed in private promptheus-content repository):
  1. Introduction to Prompt Engineering
  2. Defining AI Roles
  3. Providing Context
  4. Setting Clear Objectives
  5. Specifying Output Format
- Practice exercises (1 per lesson)
- AI-powered feedback on user prompts
- Progress tracking and resume capability

#### 6.2 Excluded from MVP
- Advanced techniques (chain-of-thought, meta-prompting)
- Community features
- Multi-language support
- Analytics dashboard
- Certification system

### 7. Configuration

#### 7.1 Environment Variables
```
TELEGRAM_BOT_TOKEN
OPENROUTER_API_KEY
DATABASE_URL
LOG_LEVEL

# AI Model Configuration (Free Tier)
AI_MODEL_PRIMARY=meta-llama/llama-4-scout:free
AI_MODEL_FALLBACK=google/gemini-2.5-pro-exp:free
AI_MODEL_ALTERNATIVE=mistralai/mistral-small-3.1-24b-instruct:free
AI_MODEL_LIGHTWEIGHT=qwen/qwen2.5-vl-3b-instruct:free

# Model Parameters
MAX_TOKENS_DEFAULT=1024
MAX_TOKENS_FEEDBACK=512
MAX_TOKENS_ASSESSMENT=256
TEMPERATURE_DEFAULT=0.7
TEMPERATURE_ASSESSMENT=0.3
TEMPERATURE_FEEDBACK=0.5
```

#### 7.2 Application Settings
- Message length limits:
  - Theory content: 50-80 words/message
  - Example annotations: 2-3 sentences/comparison
  - Exercise descriptions: max 100 words
  - Feedback: structured 2-3 messages
- Rate limiting thresholds
- Retry attempts and timeouts
- Session timeout duration (15 minutes inactivity)
- Cache TTL values
- Message typing delay: 0.5-1s between sequential messages

### 8. Error Handling Strategy

#### 8.1 Error Categories
- **User Errors**: Invalid input, rate limit exceeded → User-friendly message
- **API Errors**: Timeout, rate limit, invalid response → Retry with fallback
- **System Errors**: Database connection, critical failures → Log + notify admin
- **Data Errors**: Invalid state, missing data → Reset to safe state

#### 8.2 Logging Requirements
- Structured logging with loguru
- Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Include: timestamp, user_id, action, error details
- Rotation: Daily, max 30 days retention
- JSON serialization for structured data
- Colored output for development environment
- Context binding for request tracing

### 9. Testing Requirements

#### 9.1 Unit Tests
- Business logic coverage: >80%
- AI integration layer (mocked APIs)
- Data models and validation

#### 9.2 Integration Tests
- Telegram bot handlers
- Database operations
- API client functionality

#### 9.3 End-to-End Tests
- Complete user flows (onboarding → lesson → practice)
- Error scenarios
- Session persistence

### 10. Deployment

#### 10.1 Infrastructure
- **MVP**: Single VPS or cloud VM
- **Production**: Container-based (Docker)
- **Database**: Managed service (RDS/Cloud SQL)
- **Monitoring**: Application and infrastructure metrics

#### 10.2 CI/CD Pipeline
- Automated testing on PR
- Lint and type checking (ruff, mypy)
- Automated build and test on merge to develop
- Manual deployment to production with approval

### 11. Monitoring and Observability

#### 11.1 Metrics
- User engagement (daily/weekly active users)
- Lesson completion rates
- Average session duration
- API response times and error rates
- API usage metrics:
  - Requests per model (primary/fallback/alternative)
  - Fallback frequency (indicates primary model reliability)
  - Token consumption per user session
  - Cost per user (track for migration to paid models)
  - Free tier limit proximity warnings

#### 11.2 Alerts
- Bot downtime
- API error rate > 5%
- Database connection failures
- Unusual cost spikes

### 12. Dependencies

#### 12.1 Core Libraries
```
python-telegram-bot>=20.0
openai>=1.0  # For OpenRouter compatibility
sqlalchemy>=2.0
alembic>=1.12  # Database migrations
pydantic>=2.0
pydantic-settings>=2.0
python-dotenv>=1.0
httpx>=0.27  # Modern async HTTP client
loguru>=0.7  # Simplified logging with better defaults
```

#### 12.2 Development Dependencies
```
pytest>=7.4
pytest-asyncio>=0.21
pytest-cov>=4.1
ruff>=0.1
mypy>=1.7
```

### 13. Success Criteria

#### 13.1 Technical Metrics
- Bot uptime: >99%
- Average response time: <3s
- Test coverage: >80%
- Zero critical security vulnerabilities

#### 13.2 User Metrics
- 50+ users complete onboarding (first month)
- 30% lesson completion rate
- Average session duration: >5 minutes
- User retention (7-day): >40%
