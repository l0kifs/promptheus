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
└──────┬──────┘         └──────────────┘         └──────┬─────┘
       │ 1                                              │ 1
       │                                                │
       │ 1                                              │ *
       │                                         ┌──────▼──────────┐
┌──────▼──────┐                                 │ LessonVersion   │
│ UserSession │                                 │                 │
│             │                                 └─────────────────┘
└─────────────┘                                        
```

**Relationships**:
- User **1:N** UserProgress (one user has many progress records)
- Lesson **1:N** UserProgress (one lesson tracked by many users)
- User **1:1** UserSession (one active session per user)
- Lesson **1:N** LessonVersion (one lesson has version history)

---

### 3. Schema Definitions

#### 3.1 User
**Purpose**: Store user identity, skill assessment, and learning preferences

| Column              | Type         | Constraints             | Description                            |
| ------------------- | ------------ | ----------------------- | -------------------------------------- |
| `telegram_id`       | BIGINT       | PK, NOT NULL            | Telegram user ID (unique identifier)   |
| `username`          | VARCHAR(255) | NULL                    | Telegram username (optional)           |
| `skill_level`       | ENUM         | NOT NULL, CHECK         | `beginner`, `intermediate`, `advanced` |
| `learning_goal`     | ENUM         | NOT NULL, CHECK         | `academic`, `professional`, `creative` |
| `current_lesson_id` | INTEGER      | FK → Lesson(id), NULL   | Current lesson (for resume capability) |
| `assessment_score`  | INTEGER      | NULL, CHECK (0-100)     | Initial assessment score (0-100)       |
| `created_at`        | TIMESTAMP    | NOT NULL, DEFAULT NOW() | Account creation timestamp             |
| `updated_at`        | TIMESTAMP    | NOT NULL, DEFAULT NOW() | Last update timestamp                  |

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

**Note**: Lesson content is managed via private `promptheus-content` repository and loaded automatically from JSON files on application startup.

| Column           | Type         | Constraints               | Description                                             |
| ---------------- | ------------ | ------------------------- | ------------------------------------------------------- |
| `id`             | SERIAL       | PK, NOT NULL              | Auto-increment lesson ID                                |
| `title`          | VARCHAR(255) | NOT NULL, UNIQUE          | Lesson title (e.g., "Role Definition")                  |
| `slug`           | VARCHAR(100) | NOT NULL                  | URL-safe identifier (e.g., "role-definition")           |
| `skill_level`    | ENUM         | NOT NULL, CHECK           | Target skill level                                      |
| `position`       | INTEGER      | NULL                      | Optional explicit ordering (allows gaps: 10, 20, 30...) |
| `tags`           | JSON         | NOT NULL                  | Array of tags for categorization                        |
| `theory_content` | JSON         | NOT NULL                  | Theory sections (text, examples)                        |
| `examples`       | JSON         | NOT NULL                  | Good/bad prompt comparisons                             |
| `exercises`      | JSON         | NOT NULL                  | Practice scenarios                                      |
| `version`        | VARCHAR(20)  | NOT NULL, DEFAULT '1.0.0' | Current semantic version                                |
| `created_at`     | TIMESTAMP    | NOT NULL, DEFAULT NOW()   | Content creation timestamp                              |
| `updated_at`     | TIMESTAMP    | NOT NULL, DEFAULT NOW()   | Last update timestamp                                   |

**Indexes**:
- PRIMARY KEY: `id`
- UNIQUE INDEX: `skill_level, slug` (slug unique within skill level)
- INDEX: `skill_level, position` (for ordered queries)
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
- `slug` generated automatically from `title` during content loading (lowercase, hyphenated)
- `position` allows explicit ordering with gaps (default: index * 10 from file order)
- If `position` is NULL, lessons ordered alphabetically by slug within skill level
- Tags must match predefined categories (techniques, use_cases, topics)
- Content structured for mobile-optimized delivery (50-80 word chunks)
- **Content Source**: Lessons loaded automatically from JSON files in `promptheus-content` repository
- **Hot Reload**: File changes detected and content updated without application restart
- **Versioning**: Content changes create new version records in LessonVersion table

---

#### 3.2.5 LessonVersion
**Purpose**: Store version history of lesson content changes

| Column               | Type         | Constraints               | Description                      |
| -------------------- | ------------ | ------------------------- | -------------------------------- |
| `id`                 | SERIAL       | PK, NOT NULL              | Auto-increment version ID        |
| `lesson_id`          | INTEGER      | FK → Lesson(id), NOT NULL | Lesson reference                 |
| `version`            | VARCHAR(20)  | NOT NULL                  | Semantic version (e.g., "1.2.3") |
| `content_hash`       | VARCHAR(64)  | NOT NULL                  | SHA-256 hash of content          |
| `theory_content`     | JSON         | NOT NULL                  | Theory content snapshot          |
| `examples`           | JSON         | NOT NULL                  | Examples snapshot                |
| `exercises`          | JSON         | NOT NULL                  | Exercises snapshot               |
| `created_at`         | TIMESTAMP    | NOT NULL, DEFAULT NOW()   | Version creation timestamp       |
| `created_by`         | VARCHAR(100) | NULL                      | Author/system identifier         |
| `change_description` | VARCHAR(500) | NULL                      | Optional change description      |
| `is_active`          | BOOLEAN      | NOT NULL, DEFAULT FALSE   | Active version flag              |

**Indexes**:
- PRIMARY KEY: `id`
- UNIQUE INDEX: `lesson_id, version` (one version per lesson-version pair)
- INDEX: `lesson_id, is_active` (fast active version lookup)
- INDEX: `lesson_id, created_at` (chronological version queries)

**Business Rules**:
- Only one version can be `is_active=TRUE` per lesson
- `content_hash` used to detect actual content changes (ignore formatting)
- Version string follows semver format (MAJOR.MINOR.PATCH)
- All content fields are snapshots (immutable once created)
- Rollback sets target version as active and updates main Lesson table
- Version created automatically on content change detection during hot reload

---

#### 3.3 UserProgress
**Purpose**: Track user advancement through lessons

| Column         | Type      | Constraints                      | Description                               |
| -------------- | --------- | -------------------------------- | ----------------------------------------- |
| `id`           | SERIAL    | PK, NOT NULL                     | Auto-increment progress ID                |
| `user_id`      | BIGINT    | FK → User(telegram_id), NOT NULL | User reference                            |
| `lesson_id`    | INTEGER   | FK → Lesson(id), NOT NULL        | Lesson reference                          |
| `status`       | ENUM      | NOT NULL, DEFAULT 'not_started'  | `not_started`, `in_progress`, `completed` |
| `attempts`     | INTEGER   | NOT NULL, DEFAULT 0              | Number of exercise attempts               |
| `last_score`   | INTEGER   | NULL, CHECK (0-100)              | Most recent exercise score (0-100)        |
| `completed_at` | TIMESTAMP | NULL                             | Completion timestamp                      |

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
- `last_score` is updated whenever user completes a practice exercise, regardless of lesson status
- Average score calculation includes all progress records where `last_score IS NOT NULL`
- Lesson `status` (in_progress vs completed) does not affect score averaging
- Example: User with 3 lessons (scores: 8, 6, 3) shows average of 5.7/10 regardless of completion status

---

#### 3.4 UserSession
**Purpose**: Manage active conversation state and context

| Column         | Type      | Constraints                          | Description                                    |
| -------------- | --------- | ------------------------------------ | ---------------------------------------------- |
| `user_id`      | BIGINT    | PK, FK → User(telegram_id), NOT NULL | User reference (one session per user)          |
| `state`        | ENUM      | NOT NULL                             | `onboarding`, `learning`, `practicing`, `menu` |
| `context_data` | JSON      | NOT NULL, DEFAULT '{}'               | State-specific context                         |
| `updated_at`   | TIMESTAMP | NOT NULL, DEFAULT NOW()              | Last activity timestamp                        |

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
SELECT u.*, l.title, l.slug, l.position
FROM User u 
LEFT JOIN Lesson l ON u.current_lesson_id = l.id 
WHERE u.telegram_id = ?;

-- Get lesson by slug (cache miss fallback)
SELECT * FROM Lesson 
WHERE skill_level = ? AND slug = ?;

-- Get next lesson for user (ordered by position, then slug)
SELECT * FROM Lesson 
WHERE skill_level = ? AND (position > ? OR (position IS NULL AND slug > ?))
ORDER BY position ASC NULLS LAST, slug ASC LIMIT 1;

-- Get all lessons for skill level (for cache population)
SELECT * FROM Lesson
WHERE skill_level = ?
ORDER BY position ASC NULLS LAST, slug ASC;

-- Get user progress summary
SELECT l.title, l.slug, up.status, up.last_score, up.completed_at
FROM UserProgress up
JOIN Lesson l ON up.lesson_id = l.id
WHERE up.user_id = ?
ORDER BY l.position ASC NULLS LAST, l.slug ASC;

-- Get active version for lesson
SELECT * FROM LessonVersion
WHERE lesson_id = ? AND is_active = TRUE;
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

-- Upsert lesson (hot reload)
INSERT INTO Lesson (title, slug, skill_level, position, tags, theory_content, examples, exercises, version)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
ON CONFLICT (title) DO UPDATE
SET slug = EXCLUDED.slug,
    position = EXCLUDED.position,
    theory_content = EXCLUDED.theory_content,
    examples = EXCLUDED.examples,
    exercises = EXCLUDED.exercises,
    version = EXCLUDED.version,
    updated_at = NOW();

-- Create new version
INSERT INTO LessonVersion (lesson_id, version, content_hash, theory_content, examples, exercises, created_by, is_active)
VALUES (?, ?, ?, ?, ?, ?, ?, TRUE);

-- Deactivate other versions
UPDATE LessonVersion
SET is_active = FALSE
WHERE lesson_id = ? AND id != ?;
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
| Feature           | SQLite                  | PostgreSQL               |
| ----------------- | ----------------------- | ------------------------ |
| ENUM types        | TEXT + CHECK constraint | Native ENUM type         |
| JSON indexing     | N/A                     | GIN index support        |
| Concurrent writes | Limited (file lock)     | Full ACID support        |
| Timestamp         | TEXT/INTEGER            | TIMESTAMP WITH TIME ZONE |
| ON CONFLICT       | Limited                 | Full upsert support      |

#### 5.2 Migration Steps
1. Export data from SQLite using SQLAlchemy
2. Create PostgreSQL schema with Alembic migration (includes slug, version table)
3. Transform data (ENUM conversion, timestamp formats, generate slugs)
4. Create initial versions for all existing lessons
5. Import data using bulk insert
6. Rebuild indexes and vacuum analyze
7. Update connection string in configuration

#### 5.3 Schema Evolution (Lesson Management Update)
**Migration from order_index to slug+position:**
1. Add `slug` and `position` columns (nullable initially)
2. Populate slugs from titles (generate_slug function)
3. Populate positions from order_index (order_index * 10 for gaps)
4. Make slug non-nullable, add unique constraint
5. Drop order_index column and associated indexes

**Add LessonVersion table:**
1. Create lesson_version table with all columns
2. Create initial version (1.0.0) for each existing lesson
3. Set is_active=TRUE for initial versions
4. Add foreign key constraints and indexes

---

### 6. Performance Optimization

#### 6.1 Indexing Strategy
- **Primary Keys**: All tables for unique identification
- **Foreign Keys**: Automatic indexing for JOIN operations
- **Composite Indexes**: 
  - `(user_id, status)` for progress filtering
  - `(skill_level, slug)` for lesson lookup (unique)
  - `(skill_level, position)` for ordered lesson queries
  - `(lesson_id, is_active)` for active version lookup
- **JSON Indexes**: GIN indexes on `tags` field (PostgreSQL)

#### 6.2 Query Optimization
- Use `LIMIT` for paginated results
- Avoid `SELECT *` in application code (specify columns)
- Connection pooling (SQLAlchemy pool_size=10, max_overflow=20)
- Prepared statements for repeated queries
- Leverage cache for lesson content (avoid repeated DB queries)

#### 6.3 Caching Strategy
- **Session State**: In-memory cache with 5-minute TTL
- **Lesson Content**: In-memory cache (LessonCache) with hot reload
  - Loaded on startup from database
  - Updated automatically on file changes (file watcher)
  - O(1) lookup by skill_level and slug
  - Cache miss falls back to database
- **User Progress**: Write-through cache (always fresh)
- **Cache Invalidation**: Manual via admin API or automatic on hot reload

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

-- LessonVersion foreign key
lesson_id → Lesson(id) ON DELETE CASCADE
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
- **A/B Testing**: Leverage LessonVersion for serving different versions to different users
- **Version Retention**: Policy for archiving old versions (keep last N versions)
