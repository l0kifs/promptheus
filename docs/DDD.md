# Database Design Document (DDD)
## Promptheus - Telegram Bot for Prompt Engineering Education

### 1. Database Overview

**Purpose**: Persistent storage for user data, learning content, progress tracking, and session management

**Technology**: 
- **MVP**: SQLite (file-based, single-writer)
- **Production**: PostgreSQL (concurrent access, advanced features)

**Migration Strategy**: SQLAlchemy ORM + Alembic for version-controlled schema changes

---

### 2. Entity-Relationship Diagram

```
┌─────────────┐         ┌──────────────┐         ┌────────────┐
│    User     │────────<│ UserProgress │>────────│   Lesson   │
│             │ 1     * │              │ *     1 │            │
└──────┬──────┘         └──────────────┘         └────────────┘
       │ 1                                              
       │                                                
       │ 1                                              
       │                                                
┌──────▼──────┐                                        
│ UserSession │                                        
│             │                                        
└─────────────┘                                        
```

**Relationships**:
- User **1:N** UserProgress (one user has many progress records)
- Lesson **1:N** UserProgress (one lesson tracked by many users)
- User **1:1** UserSession (one active session per user)

---

### 3. Schema Definitions

#### 3.1 User
**Purpose**: Store user identity, skill assessment, and learning preferences

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `telegram_id` | BIGINT | PK, NOT NULL | Telegram user ID (unique identifier) |
| `username` | VARCHAR(255) | NULL | Telegram username (optional) |
| `skill_level` | ENUM | NOT NULL, CHECK | `beginner`, `intermediate`, `advanced` |
| `learning_goal` | ENUM | NOT NULL, CHECK | `academic`, `professional`, `creative` |
| `current_lesson_id` | INTEGER | FK → Lesson(id), NULL | Current lesson (for resume capability) |
| `assessment_score` | INTEGER | NULL, CHECK (0-100) | Initial assessment score (0-100) |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT NOW() | Account creation timestamp |
| `updated_at` | TIMESTAMP | NOT NULL, DEFAULT NOW() | Last update timestamp |

**Indexes**:
- PRIMARY KEY: `telegram_id`
- INDEX: `skill_level` (for lesson filtering)
- INDEX: `created_at` (for analytics)

**Business Rules**:
- `telegram_id` must match authenticated Telegram user
- `skill_level` and `learning_goal` set during onboarding
- `current_lesson_id` updated on lesson start, nullified on completion

---

#### 3.2 Lesson
**Purpose**: Store learning content metadata and structure

**Note**: Lesson content is managed via private `promptheus-content` repository and seeded into database.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | SERIAL | PK, NOT NULL | Auto-increment lesson ID |
| `title` | VARCHAR(255) | NOT NULL, UNIQUE | Lesson title (e.g., "Role Definition") |
| `skill_level` | ENUM | NOT NULL, CHECK | Target skill level |
| `order_index` | INTEGER | NOT NULL | Display order within skill level |
| `tags` | JSON | NOT NULL | Array of tags for categorization |
| `theory_content` | JSON | NOT NULL | Theory sections (text, examples) |
| `examples` | JSON | NOT NULL | Good/bad prompt comparisons |
| `exercises` | JSON | NOT NULL | Practice scenarios |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT NOW() | Content creation timestamp |

**Indexes**:
- PRIMARY KEY: `id`
- UNIQUE INDEX: `skill_level, order_index` (ensure ordered progression)
- GIN INDEX: `tags` (PostgreSQL only, for tag-based queries)

**JSON Structures**:
```json
// tags
["role-based", "professional", "role-definition"]

// theory_content
{
  "sections": [
    {"text": "Theory text chunk 1 (50-80 words)", "order": 1},
    {"text": "Theory text chunk 2 (50-80 words)", "order": 2}
  ]
}

// examples
{
  "comparisons": [
    {
      "bad": "Write about dogs",
      "good": "As a veterinarian, explain...",
      "annotation": "Good example shows role definition"
    }
  ]
}

// exercises
{
  "scenarios": [
    {
      "description": "Scenario description (max 100 words)",
      "task": "Your task",
      "evaluation_criteria": ["criterion1", "criterion2"]
    }
  ]
}
```

**Business Rules**:
- Each skill level has distinct `order_index` sequence (1, 2, 3...)
- Tags must match predefined categories (techniques, use_cases, topics)
- Content structured for mobile-optimized delivery (50-80 word chunks)
- **Content Source**: Lessons seeded from private `promptheus-content` repository

---

#### 3.3 UserProgress
**Purpose**: Track user advancement through lessons

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | SERIAL | PK, NOT NULL | Auto-increment progress ID |
| `user_id` | BIGINT | FK → User(telegram_id), NOT NULL | User reference |
| `lesson_id` | INTEGER | FK → Lesson(id), NOT NULL | Lesson reference |
| `status` | ENUM | NOT NULL, DEFAULT 'not_started' | `not_started`, `in_progress`, `completed` |
| `attempts` | INTEGER | NOT NULL, DEFAULT 0 | Number of exercise attempts |
| `last_score` | INTEGER | NULL, CHECK (0-100) | Most recent exercise score (0-100) |
| `completed_at` | TIMESTAMP | NULL | Completion timestamp |

**Indexes**:
- PRIMARY KEY: `id`
- UNIQUE INDEX: `user_id, lesson_id` (one progress record per user-lesson pair)
- INDEX: `user_id, status` (for progress queries)
- INDEX: `lesson_id` (for analytics)

**Business Rules**:
- Status transition: `not_started` → `in_progress` → `completed`
- `completed_at` set when status changes to `completed`
- `attempts` incremented on each exercise submission
- `last_score` updated with AI evaluation result

---

#### 3.4 UserSession
**Purpose**: Manage active conversation state and context

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `user_id` | BIGINT | PK, FK → User(telegram_id), NOT NULL | User reference (one session per user) |
| `state` | ENUM | NOT NULL | `onboarding`, `learning`, `practicing`, `menu` |
| `context_data` | JSON | NOT NULL, DEFAULT '{}' | State-specific context |
| `updated_at` | TIMESTAMP | NOT NULL, DEFAULT NOW() | Last activity timestamp |

**Indexes**:
- PRIMARY KEY: `user_id`
- INDEX: `updated_at` (for session cleanup)

**JSON Structure (context_data)**:
```json
{
  "current_step": "assessment_question_3",
  "temp_data": {
    "assessment_answers": [true, false, true],
    "lesson_section": 2
  },
  "last_message_id": 12345
}
```

**Business Rules**:
- One active session per user (PK constraint)
- Session expires after 15 minutes inactivity (cleanup job)
- `context_data` stores state-specific temporary data
- `updated_at` refreshed on every user interaction

---

### 4. Data Access Patterns

#### 4.1 Read Queries (High Frequency)
```sql
-- Get user with current lesson (onboarding/resume)
SELECT u.*, l.title, l.order_index 
FROM User u 
LEFT JOIN Lesson l ON u.current_lesson_id = l.id 
WHERE u.telegram_id = ?;

-- Get next lesson for user
SELECT * FROM Lesson 
WHERE skill_level = ? AND order_index > ? 
ORDER BY order_index ASC LIMIT 1;

-- Get user progress summary
SELECT l.title, up.status, up.last_score, up.completed_at
FROM UserProgress up
JOIN Lesson l ON up.lesson_id = l.id
WHERE up.user_id = ?
ORDER BY l.order_index;
```

#### 4.2 Write Queries (Medium Frequency)
```sql
-- Update lesson progress
UPDATE UserProgress 
SET status = 'completed', last_score = ?, completed_at = NOW()
WHERE user_id = ? AND lesson_id = ?;

-- Update session state
UPDATE UserSession 
SET state = ?, context_data = ?, updated_at = NOW()
WHERE user_id = ?;

-- Create progress record (on lesson start)
INSERT INTO UserProgress (user_id, lesson_id, status)
VALUES (?, ?, 'in_progress')
ON CONFLICT (user_id, lesson_id) DO UPDATE
SET status = 'in_progress';
```

#### 4.3 Analytics Queries (Low Frequency)
```sql
-- Lesson completion rates
SELECT l.title, 
       COUNT(CASE WHEN up.status = 'completed' THEN 1 END) * 100.0 / COUNT(*) as completion_rate
FROM Lesson l
LEFT JOIN UserProgress up ON l.id = up.lesson_id
GROUP BY l.id, l.title;

-- User retention (7-day)
SELECT COUNT(DISTINCT user_id) as active_users
FROM UserSession
WHERE updated_at > NOW() - INTERVAL '7 days';
```

---

### 5. Migration Strategy

#### 5.1 SQLite → PostgreSQL Differences
| Feature | SQLite | PostgreSQL |
|---------|--------|------------|
| ENUM types | TEXT + CHECK constraint | Native ENUM type |
| JSON indexing | N/A | GIN index support |
| Concurrent writes | Limited (file lock) | Full ACID support |
| Timestamp | TEXT/INTEGER | TIMESTAMP WITH TIME ZONE |

#### 5.2 Migration Steps
1. Export data from SQLite using SQLAlchemy
2. Create PostgreSQL schema with Alembic migration
3. Transform data (ENUM conversion, timestamp formats)
4. Import data using bulk insert
5. Rebuild indexes and vacuum analyze
6. Update connection string in configuration

---

### 6. Performance Optimization

#### 6.1 Indexing Strategy
- **Primary Keys**: All tables for unique identification
- **Foreign Keys**: Automatic indexing for JOIN operations
- **Composite Indexes**: `(user_id, status)` for progress filtering
- **JSON Indexes**: GIN indexes on `tags` field (PostgreSQL)

#### 6.2 Query Optimization
- Use `LIMIT` for paginated results
- Avoid `SELECT *` in application code (specify columns)
- Connection pooling (SQLAlchemy pool_size=10, max_overflow=20)
- Prepared statements for repeated queries

#### 6.3 Caching Strategy
- **Session State**: In-memory cache with 5-minute TTL
- **Lesson Content**: Read-through cache with 1-hour TTL
- **User Progress**: Write-through cache (always fresh)

---

### 7. Data Integrity

#### 7.1 Constraints
- **NOT NULL**: All critical fields (user_id, lesson_id, state)
- **UNIQUE**: Prevent duplicate records (user-lesson pairs, telegram_id)
- **CHECK**: Validate enum values and score ranges (0-100)
- **FOREIGN KEY**: Referential integrity with CASCADE delete

#### 7.2 Referential Actions
```sql
-- UserProgress foreign keys
user_id → User(telegram_id) ON DELETE CASCADE
lesson_id → Lesson(id) ON DELETE RESTRICT

-- UserSession foreign key
user_id → User(telegram_id) ON DELETE CASCADE

-- User current lesson
current_lesson_id → Lesson(id) ON DELETE SET NULL
```

---

### 8. Security Considerations

#### 8.1 Data Protection
- **No PII Storage**: Only Telegram user ID (encrypted in transit)
- **Encryption at Rest**: Database-level encryption (production)
- **Parameterized Queries**: Prevent SQL injection via SQLAlchemy ORM
- **Access Control**: Application-level authentication (no direct DB access)

#### 8.2 Data Retention
- **Active Users**: Retain indefinitely while active
- **Inactive Sessions**: Purge after 30 days of inactivity
- **Audit Logs**: 90-day retention for security events (future enhancement)

---

### 9. Backup and Recovery

#### 9.1 Backup Strategy
- **Frequency**: Daily automated backups (production)
- **Retention**: 30-day rolling backups
- **Storage**: Off-site backup location (cloud storage)
- **Testing**: Monthly restore drills

#### 9.2 Recovery Procedures
- **Point-in-Time Recovery**: WAL archiving (PostgreSQL)
- **Disaster Recovery**: RTO < 4 hours, RPO < 1 hour
- **Rollback**: Alembic migration downgrade for schema issues

---

### 10. Monitoring and Maintenance

#### 10.1 Health Checks
- Connection pool utilization (alert if >80%)
- Query performance (slow query log, threshold >500ms)
- Table size growth (alert on unexpected spikes)
- Index usage statistics (identify unused indexes)

#### 10.2 Routine Maintenance
- **Daily**: Automated backups, session cleanup
- **Weekly**: Vacuum analyze (PostgreSQL), index rebuild if needed
- **Monthly**: Capacity planning review, query optimization audit

---

### 11. Schema Evolution

#### 11.1 Alembic Migrations
```bash
# Create new migration
alembic revision --autogenerate -m "Add user preferences table"

# Apply migration
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

#### 11.2 Future Enhancements
- **Community Features**: `UserPrompt` table for shared prompts
- **Certification**: `Certificate` table for achievements
- **Analytics**: `EventLog` table for detailed user actions
- **Multi-Language**: `Content` table with language variants
