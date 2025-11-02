# System Architecture Document (SAD)
## Promptheus - Telegram Bot for Prompt Engineering Education

### 1. Architecture Overview

**Architecture Style**: Layered architecture with async event-driven communication

```
┌─────────────────────────────────────────────────────────────┐
│                     Telegram Bot API                        │
└───────────────────────────┬─────────────────────────────────┘
                            │ HTTPS/Webhook or Polling
┌───────────────────────────▼─────────────────────────────────┐
│                    Bot Interface Layer                      │
│  • Message Handler  • Callback Handler  • State Manager     │
└───────────────────────────┬─────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────┐
│                   Application Core Layer                    │
│  • Learning Flow Orchestrator  • Content Delivery Manager   │
│  • Assessment Engine           • Progress Tracker           │
└─────────────┬──────────────────────────────┬────────────────┘
              │                              │
    ┌─────────▼──────────┐         ┌─────────▼──────────┐
    │   AI Integration   │         │   Data Access      │
    │       Layer        │         │      Layer         │
    │  • OpenRouter      │         │  • User Repository │
    │    Client          │         │  • Lesson Repo     │
    │  • Prompt Manager  │         │  • Progress Repo   │
    │  • Response Parser │         │  • Session Repo    │
    └─────────┬──────────┘         └─────────┬──────────┘
              │                              │
    ┌─────────▼──────────┐         ┌─────────▼──────────┐
    │   OpenRouter API   │         │   SQLite/Postgres  │
    │   (Free models)    │         │     Database       │
    └────────────────────┘         └────────────────────┘
```

### 2. System Components

#### 2.1 Bot Interface Layer
**Responsibility**: Handle all Telegram-specific communication

**Components**:
- **Message Handler**: Processes incoming text messages, routes to appropriate handlers
- **Callback Query Handler**: Manages inline keyboard button clicks
- **State Manager**: Tracks user conversation state (onboarding/learning/practicing/menu)
- **Message Formatter**: Formats outgoing messages with markdown, emojis, keyboards

**Key Interactions**:
- Receives events from Telegram Bot API
- Delegates business logic to Application Core
- Returns formatted responses to Telegram

#### 2.2 Application Core Layer
**Responsibility**: Orchestrate business logic and learning flows

**Components**:
- **Learning Flow Orchestrator**: Manages lesson progression, navigation, resume capability
- **Content Delivery Manager**: Chunks content into mobile-optimized messages (50-80 words)
- **Assessment Engine**: Evaluates user skill level, generates personalized paths
- **Progress Tracker**: Records completion, calculates scores, manages checkpoints

**Key Interactions**:
- Receives commands from Bot Interface Layer
- Queries/updates data via Data Access Layer
- Requests AI operations from AI Integration Layer
- Returns structured responses to Bot Interface

#### 2.3 AI Integration Layer
**Responsibility**: Manage all AI model interactions

**Components**:
- **OpenRouter Client**: HTTP client with retry logic, fallback chain, rate limiting
- **Prompt Template Manager**: Stores and renders prompt templates for different scenarios
- **Response Parser**: Extracts structured data from AI responses, validates format
- **Model Selector**: Implements fallback chain (Llama-4-Scout → Gemini-2.5-Pro → Mistral-Small)

**Key Interactions**:
- Receives AI operation requests from Application Core
- Calls OpenRouter API with configured models
- Returns parsed, validated responses
- Handles errors with automatic fallback

#### 2.4 Data Access Layer
**Responsibility**: Abstract database operations

**Components**:
- **User Repository**: CRUD operations for user data, skill level, goals
- **Lesson Repository**: Retrieve lessons by skill level, tags, order (seeded from private content repo)
- **Progress Repository**: Track lesson status, attempts, scores
- **Session Repository**: Manage active session state, context data

**Key Interactions**:
- Receives data queries from Application Core
- Executes SQLAlchemy queries against database
- Returns domain models
- Handles transactions and error recovery

### 3. Component Interactions

#### 3.1 User Onboarding Flow
```
User → Telegram → Bot Handler → Flow Orchestrator
                                      ↓
                              Assessment Engine ← AI Integration
                                      ↓
                              User Repository → Database
                                      ↓
                          ← Personalized Path Response
```

#### 3.2 Lesson Delivery Flow
```
User Action → Bot Handler → Flow Orchestrator
                                  ↓
                          Lesson Repository → Database
                                  ↓
                          Content Delivery Manager
                                  ↓
                          Message Formatter → Bot Handler → Telegram
```

#### 3.3 Practice Exercise Flow
```
User Prompt → Bot Handler → Assessment Engine
                                  ↓
                          AI Integration → OpenRouter API
                                  ↓
                          Response Parser
                                  ↓
                          Progress Tracker → Database
                                  ↓
                          Feedback Message → User
```

### 4. Data Flow

#### 4.1 State Management
- **Session State**: In-memory cache with database persistence
- **User Progress**: Write-through cache to database
- **Lesson Content**: Read-through cache with 1-hour TTL

#### 4.2 Message Flow
1. Incoming: Telegram → Handler → State Manager → Core Logic
2. Processing: Core → AI (if needed) → Data Access (if needed)
3. Outgoing: Core → Formatter → Handler → Telegram

### 5. Technology Mapping

| Layer | Technologies |
|-------|--------------|
| Bot Interface | python-telegram-bot, asyncio |
| Application Core | Python 3.11+, Pydantic |
| AI Integration | httpx, OpenAI SDK (OpenRouter-compatible) |
| Data Access | SQLAlchemy, Alembic |
| Database | SQLite (MVP) / PostgreSQL (production) |
| Configuration | python-dotenv, Pydantic Settings |
| Logging | loguru |

### 6. Scalability Considerations

#### 6.1 Horizontal Scaling
- Stateless application design (session state externalized to database)
- Connection pooling for database
- Async/await for I/O-bound operations

#### 6.2 Vertical Optimization
- Message batching to reduce API calls
- Database query optimization with indexes
- AI response caching for common queries

#### 6.3 Rate Limiting
- Per-user: 10 requests/minute (Bot Interface Layer)
- Per-system: OpenRouter free tier limits (AI Integration Layer)

### 7. Error Handling Strategy

#### 7.1 Layer-Specific Handling
- **Bot Interface**: Catch all exceptions, send user-friendly error messages
- **Application Core**: Validate input, throw domain exceptions
- **AI Integration**: Retry with exponential backoff, fallback to alternative models
- **Data Access**: Handle connection errors, transaction rollback

#### 7.2 Fallback Chain
```
Primary Model (Llama-4-Scout) → Fallback (Gemini-2.5-Pro) → Alternative (Mistral-Small) → Error Message
```

### 8. Security Architecture

#### 8.1 Security Layers
- **Transport**: HTTPS-only for all external communications
- **Authentication**: Telegram user ID validation, API key management
- **Data**: Encryption at rest for sensitive data, minimal PII storage
- **Input**: Validation and sanitization at Bot Interface Layer

#### 8.2 Secrets Management
- Environment variables for API keys
- No hardcoded credentials
- Separate configurations per environment (dev/prod)

### 9. Monitoring Points

#### 9.1 Application Metrics
- Request latency per layer
- Error rate per component
- AI model usage and fallback frequency
- Database connection pool utilization

#### 9.2 Business Metrics
- User engagement per component (onboarding/learning/practice)
- Lesson completion rates
- AI feedback quality scores

### 10. Deployment Architecture

#### 10.1 MVP Deployment
```
Single VPS/VM
├── Application Container (Python app)
├── SQLite Database (file-based)
└── Nginx (optional, for webhook)
```

#### 10.2 Production Deployment
```
Load Balancer
├── App Container 1 (stateless)
├── App Container 2 (stateless)
└── App Container N (stateless)
    ↓
Managed Database (PostgreSQL)
    ↓
Monitoring Stack (metrics, logs, traces)
```

### 11. Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| Layered Architecture | Clear separation of concerns, easier testing and maintenance |
| Async/Await Pattern | Handle multiple users concurrently without threading complexity |
| Repository Pattern | Abstract database implementation, enable easy migration (SQLite → PostgreSQL) |
| Free Tier AI Models | Zero AI costs for MVP, validate demand before paid tier investment |
| Polling (MVP) | Simpler deployment, webhook for production with proper infrastructure |
| SQLite → PostgreSQL | Start simple, migrate when scaling requires concurrent write support |
