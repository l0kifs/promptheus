# Promptheus - Telegram Bot for Prompt Engineering Education

An AI-powered Telegram bot that teaches users effective prompt engineering techniques through interactive lessons and hands-on practice.

## Features

- 🎯 **Adaptive Learning**: Personalized curriculum based on skill assessment
- 📚 **Interactive Lessons**: 5 foundational lessons covering core prompt engineering concepts
- 🤖 **AI-Powered Feedback**: Instant evaluation of your prompts using OpenRouter API
- 📱 **Mobile-First**: Optimized for Telegram mobile clients
- 🔄 **Resume Capability**: Continue learning from where you left off

## Prerequisites

- Python 3.11 or higher
- Telegram Bot Token (get from [@BotFather](https://t.me/botfather))
- OpenRouter API Key (get from [openrouter.ai](https://openrouter.ai/))

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/l0kifs/promptheus.git
cd promptheus
```

### 2. Create Virtual Environment

Using uv (recommended):
```bash
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

Or using standard Python:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 3. Install Dependencies

Using uv:
```bash
uv pip install -e ".[dev]"
```

Or using pip:
```bash
pip install -e ".[dev]"
```

### 4. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` and add your credentials:
- `TELEGRAM_BOT_TOKEN`: Your Telegram bot token from BotFather
- `OPENROUTER_API_KEY`: Your OpenRouter API key

### 5. Clone Content Repository

```bash
# Clone the private content repository (must have access)
cd ..
git clone https://github.com/l0kifs/promptheus-content.git
cd promptheus
```

### 6. Initialize Database

```bash
# Create data directory
mkdir -p data

# Run migrations (creates tables including lesson management)
alembic upgrade head

# Note: Lesson content is loaded automatically from JSON files
# No separate seeding step required after initial migration
```

### 7. Run the Bot

```bash
uv run python -m promptheus.main
```

The bot will start and log: `Bot is running. Press Ctrl+C to stop.`

### Docker Setup (Alternative)

For containerized deployment:

#### Prerequisites
- Docker and Docker Compose installed
- Same environment variables as above

#### Quick Start with Docker

```bash
# Clone repositories
git clone https://github.com/l0kifs/promptheus.git
cd promptheus
git clone https://github.com/l0kifs/promptheus-content.git ../promptheus-content

# Create environment file
cp .env.example .env
# Edit .env with your credentials

# Start with Docker Compose (development)
docker compose up --build

# Or for production
docker compose -f docker-compose.prod.yml up --build -d
```

#### Docker Commands

```bash
# Development setup
docker compose up --build          # Start all services
docker compose up -d --build       # Start in background
docker compose logs -f             # Follow logs
docker compose down                # Stop and remove containers

# Production setup
docker compose -f docker-compose.prod.yml up --build -d
docker compose -f docker-compose.prod.yml logs -f
docker compose -f docker-compose.prod.yml down

# Health check
curl http://localhost:8080/health

# Database operations
docker compose exec promptheus uv run alembic upgrade head
```

#### Docker Environment Variables

Additional variables for Docker:

| Variable             | Description                    | Default   |
| -------------------- | ------------------------------ | --------- |
| `API_SERVER_ENABLED` | Enable health check API server | `true`    |
| `API_SERVER_HOST`    | API server host                | `0.0.0.0` |
| `API_SERVER_PORT`    | API server port                | `8080`    |

### 8. VS Code Workspace (Optional)

For convenient multi-repo development:

```bash
# Open the workspace file in VS Code
code promptheus.code-workspace
```

This opens both repositories (public + private content) in one window with:
- ✅ Shared settings and extensions
- ✅ Integrated terminal in main project directory
- ✅ Easy navigation between code and content

### 9. Test the Bot

1. Open Telegram and find your bot by username
2. Send `/start` to begin
3. Complete the assessment
4. Start learning!

## Development

### Multi-Repository Setup

This project uses **two repositories** to separate open-source code from proprietary content:

**📦 promptheus (public)** - Application framework
- [https://github.com/l0kifs/promptheus](https://github.com/l0kifs/promptheus)
- Contains: application code, database schema, bot logic, documentation

**🔒 promptheus-content (private)** - Educational content
- [https://github.com/l0kifs/promptheus-content](https://github.com/l0kifs/promptheus-content)
- Contains: lessons, assessments, exercises, proprietary materials

### Content Management System

Promptheus uses an **organic lesson management system** that automatically loads content from JSON files:

**Key Features:**
- 📁 **File-based content**: Lessons stored as JSON files in the content repository
- 🔄 **Hot reload**: Content changes detected automatically (development mode)
- 📝 **Version control**: Automatic versioning of all content changes
- ✅ **Validation**: JSON schema validation on load
- 🚀 **Zero-downtime updates**: Content updates without application restart

**Content Structure:**
```
lessons/
├── beginner/
│   ├── introduction-to-prompting.json
│   └── defining-ai-roles.json
├── intermediate/
│   └── chain-of-thought-prompting.json
└── advanced/
    └── meta-prompting.json
```

**Workflow:**
1. Edit JSON files in `promptheus-content/lessons/`
2. System detects changes automatically
3. Content reloaded with validation
4. New versions created for change tracking

See [Content Creation Guide](docs/content-creation-guide.md) for detailed instructions.

### VS Code Workspace

For the best development experience, use the provided workspace file:

```bash
# Open the workspace in VS Code
code promptheus.code-workspace
```

This workspace configuration:
- ✅ Shows both repos side-by-side in one window
- ✅ Proper Python path resolution
- ✅ Recommended extensions
- ✅ Filters out cache directories

### Project Structure

```
promptheus/                  # PUBLIC REPO
├── src/promptheus/          # Main application code
│   ├── ai/                  # AI integration (OpenRouter)
│   ├── bot/                 # Telegram bot handlers
│   ├── core/                # Business logic
│   ├── config/              # Configuration
│   └── data/                # Data management & repositories
│       ├── models.py        # SQLAlchemy models
│       ├── async_repositories.py  # Database access layer
│       ├── lesson_loader.py # JSON lesson loading
│       ├── lesson_cache.py  # In-memory caching
│       ├── file_watcher.py  # Hot reload system
│       └── version_manager.py # Content versioning
├── alembic/                 # Database migrations
├── scripts/                 # Utility scripts
│   ├── migrate_from_old_system.py  # One-time migration
│   └── validate_content.py  # Content validation
├── tests/                   # Test suite
└── docs/                    # Documentation

promptheus-content/          # PRIVATE REPO (separate)
├── lessons/                 # JSON lesson files
│   ├── beginner/*.json
│   ├── intermediate/*.json
│   └── advanced/*.json
├── docs/                    # Content documentation
│   ├── lesson-catalog.md
│   └── content-workflow.md
└── README.md
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/promptheus --cov-report=html

# Run specific test file
pytest tests/test_core.py
```

### Code Quality

```bash
# Format code
ruff format src/

# Lint code
ruff check src/

# Type checking
mypy src/
```

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

## Configuration

All configuration is done via environment variables in `.env`:

| Variable             | Description                             | Default                          |
| -------------------- | --------------------------------------- | -------------------------------- |
| `TELEGRAM_BOT_TOKEN` | Telegram bot token                      | Required                         |
| `OPENROUTER_API_KEY` | OpenRouter API key                      | Required                         |
| `DATABASE_URL`       | Database connection URL                 | `sqlite:///./data/promptheus.db` |
| `ENVIRONMENT`        | Environment (development/production)    | `development`                    |
| `LOG_LEVEL`          | Logging level                           | `INFO`                           |
| `BOT_MODE`           | Bot operating mode (polling/webhook)    | `polling`                        |
| `WEBHOOK_URL`        | Webhook URL (required for webhook mode) | None                             |
| `WEBHOOK_SECRET`     | Webhook secret token                    | None                             |
| `WEBHOOK_PORT`       | Webhook server port                     | 8443                             |
| `WEBHOOK_PATH`       | Webhook endpoint path                   | `/webhook`                       |
| `API_SERVER_ENABLED` | Enable health check API server          | `true`                           |
| `API_SERVER_HOST`    | API server host                         | `0.0.0.0`                        |
| `API_SERVER_PORT`    | API server port                         | `8080`                           |

See `.env.example` for all available options.

### Bot Modes

Promptheus supports two operating modes:

#### Polling Mode (Development)
- **Use case**: Local development, testing, CI/CD
- **How it works**: Bot actively polls Telegram API for updates
- **Configuration**: `BOT_MODE=polling` (default)
- **Pros**: Easy setup, works behind firewalls/NAT
- **Cons**: Higher latency, consumes more API calls

#### Webhook Mode (Production)
- **Use case**: Production deployment, scalable environments
- **How it works**: Telegram sends updates directly to your server
- **Configuration**: `BOT_MODE=webhook` with `WEBHOOK_URL=https://yourdomain.com/webhook`
- **Requirements**:
  - Public HTTPS URL (Let's Encrypt recommended)
  - Port must be 80, 88, 443, or 8443
  - SSL certificate required
- **Pros**: Lower latency, more efficient, real-time updates
- **Cons**: Requires public server with SSL

#### Setting up Webhook Mode

1. **Get a domain with SSL**:
   ```bash
   # Using Let's Encrypt with certbot
   sudo certbot certonly --standalone -d yourdomain.com
   ```

2. **Configure reverse proxy** (nginx example):
   ```nginx
   server {
       listen 443 ssl http2;
       server_name yourdomain.com;
       
       ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
       ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
       
       location /webhook {
           proxy_pass http://127.0.0.1:8443/webhook;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

3. **Update `.env`**:
   ```bash
   BOT_MODE=webhook
   WEBHOOK_URL=https://yourdomain.com/webhook
   WEBHOOK_SECRET=your_secure_random_secret_here
   WEBHOOK_PORT=8443
   ```

4. **For local testing with ngrok**:
   ```bash
   # Install ngrok
   npm install -g ngrok
   
   # Start tunnel
   ngrok http 8443
   
   # Use the HTTPS URL in .env
   WEBHOOK_URL=https://abc123.ngrok.io/webhook
   ```

#### Mode Selection Guidelines

- **Development**: Always use `polling`
- **Staging/Testing**: Use `polling` or `webhook` with ngrok
- **Production**: Always use `webhook` with proper SSL
- **CI/CD**: Use `polling` for automated tests

## Architecture

Promptheus follows a layered architecture:

- **Bot Interface Layer**: Telegram handlers and message formatting
- **Application Core**: Business logic and orchestration
- **AI Integration Layer**: OpenRouter client with fallback chain
- **Data Access Layer**: Repository pattern for database operations

See [docs/SAD.md](docs/SAD.md) for detailed architecture documentation.

## MVP Scope

The current MVP includes:

- User onboarding and skill assessment (5 questions)
- 5 foundational lessons:
  1. Introduction to Prompt Engineering
  2. Defining AI Roles
  3. Providing Context
  4. Setting Clear Objectives
  5. Specifying Output Format
- Practice exercises with AI feedback
- Progress tracking
- Resume capability

## Technology Stack

- **Language**: Python 3.11+
- **Bot Framework**: python-telegram-bot v21+
- **AI API**: OpenRouter (free tier models)
- **Database**: SQLite (dev) / PostgreSQL (production)
- **ORM**: SQLAlchemy
- **Migrations**: Alembic
- **Testing**: pytest

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

Please read [docs/DS.md](docs/DS.md) for coding standards.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Documentation

- [Business Requirements](docs/BRD.md)
- [Technical Requirements](docs/TRD.md)
- [System Architecture](docs/SAD.md)
- [Database Design](docs/DDD.md)
- [Development Standards](docs/DS.md)
- [Testing Strategy](docs/TS.md)
- [Deployment Plan](docs/DP.md)
- [User Stories](docs/US.md)
- [UX Design](docs/UXD.md)

## Support

For issues, questions, or contributions:
- Open an issue on GitHub
- Contact: [@l0kifs](https://github.com/l0kifs)

## Acknowledgments

- Telegram Bot API
- OpenRouter for free tier AI models
- The prompt engineering community
