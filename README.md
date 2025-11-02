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

# Run migrations (creates tables)
alembic upgrade head

# Seed lessons from private repo
uv run python ../promptheus-content/scripts/seed_lessons.py
```

### 7. Run the Bot

```bash
uv run python -m promptheus.main
```

The bot will start and log: `Bot is running. Press Ctrl+C to stop.`

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
│   └── data/                # Data models & repositories
├── alembic/                 # Database migrations
├── scripts/                 # Utility scripts (no content)
├── tests/                   # Test suite
└── docs/                    # Documentation

promptheus-content/          # PRIVATE REPO (separate)
├── scripts/
│   └── seed_lessons.py      # Lesson seeding script
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

| Variable | Description | Default |
|----------|-------------|---------|
| `TELEGRAM_BOT_TOKEN` | Telegram bot token | Required |
| `OPENROUTER_API_KEY` | OpenRouter API key | Required |
| `DATABASE_URL` | Database connection URL | `sqlite:///./data/promptheus.db` |
| `ENVIRONMENT` | Environment (development/production) | `development` |
| `LOG_LEVEL` | Logging level | `INFO` |

See `.env.example` for all available options.

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
