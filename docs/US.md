# User Stories (US)
## Promptheus - Telegram Bot for Prompt Engineering Education

### Document Purpose
Detailed user stories with acceptance criteria for MVP development and subsequent product versions.

---

## 1. Onboarding and Skill Assessment

### US-1.1: First Interaction
**As** a new user  
**I want** to receive a clear welcome message on first launch  
**So that** I understand the bot's purpose and can start learning

**Acceptance Criteria:**
- Welcome message is sent on `/start` command
- Message contains brief bot description (≤80 words)
- "Start Learning" button is present
- User record is created in DB with `telegram_id`
- Response time <500ms

### US-1.2: Current Knowledge Assessment
**As** a new user  
**I want** to take a quick knowledge level assessment  
**So that** I receive a personalized learning path

**Acceptance Criteria:**
- Test consists of 5 multiple-choice questions
- Each question displays progress (1/5, 2/5...)
- Answers are saved in session `context_data`
- Upon completion, `skill_level` is calculated (beginner/intermediate/advanced)
- Result is saved in `User` table
- Total completion time 2-3 minutes

### US-1.3: Learning Goal Definition
**As** a user who completed assessment  
**I want** to specify my learning goal  
**So that** I receive relevant examples and exercises

**Acceptance Criteria:**
- Three options: Study (academic), Work (professional), Creativity (creative)
- Choice is saved in `learning_goal` field of `User` table
- After selection, personalized learning path is displayed
- Path contains 3-5 recommended lessons with tags matching the goal

---

## 2. Lesson Learning

### US-2.1: View Lesson List
**As** a user  
**I want** to see all available lessons  
**So that** I can choose a topic of interest

**Acceptance Criteria:**
- Lessons are grouped by `skill_level`
- Status displayed for each lesson: ✅ completed, ⏳ in progress, 🔒 locked
- Lessons above user's current level are unavailable
- "Go to Lesson N" buttons for available lessons
- Ability to return to main menu

### US-2.2: Start Lesson
**As** a user  
**I want** to start a new lesson  
**So that** I can learn a specific prompt engineering technique

**Acceptance Criteria:**
- Lesson title, brief description, and study time (~5 minutes) are displayed
- Record created in `UserProgress` with status `in_progress`
- User's `current_lesson_id` is updated
- "Start" button leads to theory section
- "Back to Lesson List" button available for return

### US-2.3: Study Theory
**As** a user  
**I want** to read theory in small chunks  
**So that** I can easily absorb information on a mobile device

**Acceptance Criteria:**
- Theory split into 50-80 word messages
- Each message contains "Next ➡️" button
- "⬅️ Back" button available for review
- Content extracted from lesson's `theory_content` JSON field
- Use of 💡 emoji to highlight key points

### US-2.4: Compare Examples
**As** a user  
**I want** to see good and bad prompt examples  
**So that** I understand the difference in formulation quality

**Acceptance Criteria:**
- Bad example shown first with ❌ marker
- Problem explained (2-3 sentences)
- "Show Good ➡️" button displays improved version with ✅
- Brief annotation of changes (2-3 sentences)
- Data taken from lesson's `examples` JSON field

---

## 3. Practice and Feedback

### US-3.1: Complete Practice Exercise
**As** a user  
**I want** to practice the acquired knowledge  
**So that** I can reinforce my understanding of the technique

**Acceptance Criteria:**
- Exercise scenario displayed (≤100 words)
- Task clearly formulated
- Instruction to send prompt in next message
- "💡 Show Hint" and "⏭️ Skip" buttons available
- `attempts` counter in `UserProgress` is incremented

### US-3.2: AI Evaluation of User Prompt
**As** a user  
**I want** to receive instant feedback on my prompt  
**So that** I understand what was done well and what needs improvement

**Acceptance Criteria:**
- "⏳ Analyzing..." indicator shown after prompt submission
- Request sent to OpenRouter API (model `llama-4-scout:free`)
- Response structured: score 0-10, what's missing, what's good
- On API error, fallback to `gemini-2.5-pro-exp:free`
- `last_score` in `UserProgress` is updated
- Response time ≤10 seconds, otherwise timeout message

### US-3.3: Receive Improved Version
**As** a user  
**I want** to see the correct prompt variant  
**So that** I can compare with mine and understand improvement direction

**Acceptance Criteria:**
- Improved prompt version displayed
- Key additions listed (role, context, format)
- "🔄 Try Again" (new attempt) and "✅ Lesson Completed" buttons available
- On completion, lesson status changes to `completed`
- `completed_at` timestamp is set

---

## 4. Progress and Navigation

### US-4.1: View Progress
**As** a user  
**I want** to see my learning progress  
**So that** I can track achievements and stay motivated

**Acceptance Criteria:**
- Current level (`skill_level`) displayed
- Number of completed lessons shown
- Average score calculated from `last_score` of all completed lessons
- Last studied lesson indicated with date
- "▶️ Continue" and "📋 All Lessons" buttons

### US-4.2: Resume After Break
**As** a returning user  
**I want** to continue from where I left off  
**So that** I don't waste time on navigation

**Acceptance Criteria:**
- On `/start` command, `current_lesson_id` is checked
- If lesson is incomplete, "Welcome back!" message shown
- Lesson and section from session `context_data` indicated
- "▶️ Continue" button returns to stopping point
- Alternative "📚 Main Menu" button

### US-4.3: Main Menu
**As** a user  
**I want** to have a central navigation point  
**So that** I can quickly access needed sections

**Acceptance Criteria:**
- Available via `/menu` command or "📚 Menu" button
- Four main sections: Continue, All Lessons, Progress, Settings
- Each button on separate line with emoji icon
- Maximum 2 taps to any feature

---

## 5. System and Reliability

### US-5.1: Network Error Handling
**As** a user  
**I want** to receive clear messages during technical issues  
**So that** I understand what to do next

**Acceptance Criteria:**
- On Telegram API unavailability, "⚠️ Temporary Issues" message shown
- Indication that progress is saved
- On OpenRouter timeout (>10s), suggestion to simplify prompt or retry
- "🔄 Try Again" and "⏭️ Skip" buttons available
- All errors logged with timestamp and user_id

### US-5.2: Request Rate Limiting
**As** a system  
**I must** limit request frequency from users  
**So that** abuse is prevented and quality maintained for all

**Acceptance Criteria:**
- Limit: 10 requests per minute per user
- On exceeding, "⏸️ Too Many Requests" message shown
- Wait time indicated (1 minute)
- Counter resets every minute
- Limit applied at Bot Interface Layer level

### US-5.3: Inactive Session Cleanup
**As** a system  
**I must** clean up stale sessions  
**So that** resource usage is optimized

**Acceptance Criteria:**
- Session considered inactive after 15 minutes without actions
- Daily task removes sessions with `updated_at` > 30 days
- `UserProgress` and core user data preserved
- Only `UserSession` records deleted
- Process is logged

---

## 6. AI Integration

### US-6.1: Model Fallback Chain
**As** a system  
**I must** automatically switch between AI models on failures  
**So that** uninterrupted operation is ensured

**Acceptance Criteria:**
- Primary model: `meta-llama/llama-4-scout:free`
- Fallback 1: `google/gemini-2.5-pro-exp:free`
- Fallback 2: `mistralai/mistral-small-3.1-24b-instruct:free`
- Switching occurs on 5xx error or timeout
- Exponential backoff used (1s, 2s, 4s)
- Usage frequency of each model logged

### US-6.2: Prompt Templates for Different Tasks
**As** a system  
**I must** use optimized prompts for each request type  
**So that** quality and consistent responses are obtained

**Acceptance Criteria:**
- Separate templates for: level assessment, feedback generation, example creation
- Templates stored in Prompt Template Manager
- Variables used for personalization (skill_level, learning_goal)
- AI temperature: 0.3 for assessment, 0.5 for feedback, 0.7 for content generation
- Max tokens: 256 for assessment, 512 for feedback, 1024 for content

---

## 7. Data and Performance

### US-7.1: Migration from SQLite to PostgreSQL
**As** an administrator  
**I want** to migrate data from SQLite to PostgreSQL  
**So that** a larger number of users can be supported

**Acceptance Criteria:**
- Export all data via SQLAlchemy
- Create PostgreSQL schema via Alembic migration
- Convert ENUM and timestamp formats
- Bulk data import
- Integrity check: record counts match
- Update connection string in configuration
- Downtime ≤1 hour

### US-7.2: Lesson Content Caching
**As** a system  
**I must** cache lesson content  
**So that** DB load is reduced and delivery accelerated

**Acceptance Criteria:**
- Read-through cache for `Lesson` table
- TTL = 1 hour
- Cache key: `lesson_{id}`
- Invalidation on lesson content update
- DB request reduction by 80%+
- Lesson load time <100ms

---

## 8. Analytics and Monitoring

### US-8.1: Lesson Completion Metrics
**As** an administrator  
**I want** to see lesson completion statistics  
**So that** problem areas in content can be identified

**Acceptance Criteria:**
- Dashboard shows completion rate for each lesson
- % of users who completed lesson out of those who started is calculated
- Average `last_score` per lesson
- Average number of `attempts`
- Data updated daily

### US-8.2: AI Usage Tracking
**As** an administrator  
**I want** to monitor OpenRouter API costs  
**So that** migration to paid models can be planned

**Acceptance Criteria:**
- Each request logged: model, token count, latency
- Cost per user calculated (currently $0 on free tier)
- Warning when approaching free tier limits
- Fallback model usage frequency
- Weekly reports via email

---

## MVP Prioritization

### Must Have (MVP v1.0)
- US-1.1, US-1.2, US-1.3: Onboarding
- US-2.1, US-2.2, US-2.3, US-2.4: Lesson Learning
- US-3.1, US-3.2, US-3.3: Practice
- US-4.1, US-4.2, US-4.3: Navigation
- US-5.1, US-5.2: Basic error handling
- US-6.1, US-6.2: AI integration

### Should Have (v1.1)
- US-5.3: Session cleanup
- US-7.2: Caching
- US-8.1: Basic analytics

### Could Have (v1.2+)
- US-7.1: PostgreSQL migration
- US-8.2: Detailed AI analytics

---

## Success Metrics

**User Metrics:**
- 50+ users complete onboarding (1 month)
- 30% lesson completion rate
- Average session >5 minutes
- 7-day retention >40%

**Technical Metrics:**
- Uptime >99%
- Average response time <3s
- AI response time 3-10s
- Test coverage >80%

**Business Metrics:**
- $0 AI costs (MVP on free tier)
- Ready to scale to 1000 users
- Positive feedback >80%
