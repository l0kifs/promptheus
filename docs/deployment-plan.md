# Deployment Plan (DP)
## Promptheus - Telegram Bot for Prompt Engineering Education

### 1. Deployment Overview

**Goal**: Ensure reliable, secure, and scalable bot deployment with minimal downtime.

**Strategy**: Direct deployment from local development to production with CI/CD automation and comprehensive testing.

### 2. Environments

#### 2.1 Development (Local Development)
**Purpose**: Feature development, debugging, and testing before production deployment

**Configuration**:
- Python 3.11+ (local installation or venv)
- SQLite (file `data/dev.db`)
- Telegram Bot API: Polling mode
- OpenRouter: Free tier models
- Logging: DEBUG level, console output

**Requirements**:
- `.env` file with environment variables
- Test Telegram bot (separate from production)
- Comprehensive test suite for validation
- Docker for local containerized testing
- Private `promptheus-content` repository (for lesson data)

#### 2.2 Production
**Purpose**: Serving real users

**Configuration**:
- Managed service or VPS (2 CPU, 2GB RAM minimum)
- PostgreSQL (managed database)
- Telegram Bot API: Webhook mode
- OpenRouter: Free tier models with limit monitoring
- Logging: WARNING level, structured JSON logs
- Monitoring: metrics, alerts, health checks

**Infrastructure (MVP)**:
```
Single VPS
├── Docker Container (app)
│   └── Python app + dependencies
├── Nginx (SSL termination, reverse proxy)
├── PostgreSQL (managed RDS/Cloud SQL)
└── Monitoring agent
```

**Инфраструктура (Scale)**:
```
Load Balancer
├── App Container 1 (stateless)
├── App Container 2 (stateless)
└── App Container N (stateless)
    ↓
PostgreSQL (primary + replica)
    ↓
Monitoring & Logging Stack
```

### 3. Environment Requirements

#### 3.1 System Dependencies
- **OS**: Ubuntu 22.04 LTS or higher
- **Runtime**: Python 3.11+
- **Containerization**: Docker 24.0+, Docker Compose 2.20+
- **Web Server**: Nginx 1.24+ (for webhook)
- **Database**: PostgreSQL 15+ (production)

#### 3.2 Network Requirements
- **Inbound Traffic**: HTTPS (443) for Telegram webhook
- **Outbound Traffic**: 
  - api.telegram.org (443)
  - openrouter.ai (443)
  - Database endpoint (5432 for PostgreSQL)
  - github.com (443, for private content repo access)
- **Firewall**: Only necessary ports

#### 3.3 SSL/TLS
- **Production**: Valid SSL certificate (Let's Encrypt)
- **Development**: Not required (polling mode)

### 4. Deployment Procedure

#### 4.1 Pre-deployment Preparation

**Secrets and environment variables**:
```bash
# Required variables
TELEGRAM_BOT_TOKEN=<bot_token>
OPENROUTER_API_KEY=<api_key>
DATABASE_URL=<connection_string>

# Optional settings
LOG_LEVEL=INFO  # DEBUG/INFO/WARNING/ERROR
ENVIRONMENT=production  # development/production
WEBHOOK_URL=https://your-domain.com/webhook  # for webhook mode
```

**Secrets Management**:
- Development: `.env` file (do not commit to Git)
- Production: Cloud secrets manager or env variables in deployment
- Content Repository: SSH deploy keys or personal access tokens for CI/CD

#### 4.2 Initial Deployment

**Step 1: Infrastructure Preparation**
```bash
# Clone repositories
git clone https://github.com/l0kifs/promptheus.git
git clone https://github.com/l0kifs/promptheus-content.git  # Private repo
cd promptheus

# Check Python version
python --version  # Should be >= 3.11
```

**Step 2: Environment Configuration**
```bash
# Create .env file
cp .env.example .env
# Edit .env with actual values

# For Docker deployment
cp docker-compose.example.yml docker-compose.yml
# Configure docker-compose.yml for environment
```

**Step 3: Install Dependencies**
```bash
# Option 1: Local installation
python -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt

# Option 2: Docker
docker compose build
```

**Step 4: Database Initialization**
```bash
# Apply migrations
alembic upgrade head

# Seed initial data (lessons) - requires private content repo
# Clone private repo: git clone https://github.com/l0kifs/promptheus-content.git
python ../promptheus-content/scripts/seed_lessons.py
```

**Step 5: Application Start**
```bash
# Locally
python -m src.main

# Docker
docker compose up -d

# Check status
docker compose ps
docker compose logs -f app
```

**Step 6: Webhook Configuration (Production)**
```bash
# Set webhook URL
curl -X POST "https://api.telegram.org/bot<TOKEN>/setWebhook" \
  -d "url=https://your-domain.com/webhook" \
  -d "max_connections=100"

# Verify webhook
curl "https://api.telegram.org/bot<TOKEN>/getWebhookInfo"
```

**Step 7: Pre-production Validation (Local)**
```bash
# Run full test suite locally
pytest tests/ -v --cov

# Integration tests with test bot
pytest tests/integration/ -v

# Load testing (optional)
# locust -f tests/load/locustfile.py
```

#### 4.3 Update Deployment

**Zero-downtime strategy for Production**:

1. **Pre-deployment checks**:
```bash
# Run tests
pytest tests/

# Check migrations
alembic check
alembic upgrade head --sql  # Dry-run
```

2. **Deployment process**:
```bash
# Pull latest code
git pull origin main

# Rebuild containers (if dependency changes)
docker compose build

# Apply migrations
docker compose run --rm app alembic upgrade head

# Rolling update
docker compose up -d --no-deps --build app

# Check health
curl https://your-domain.com/health
```

3. **Post-deployment validation**:
```bash
# Check logs
docker compose logs -f --tail=100 app

# Test core functions
# Send /start to bot
# Check onboarding flow
# Check lesson delivery
```

4. **Rollback procedure** (if issues occur):
```bash
# Rollback to previous version
git checkout <previous_commit>
docker compose up -d --no-deps --build app

# Rollback migrations (if needed)
alembic downgrade -1
```

#### 4.4 Database Migrations

**Creating a migration**:
```bash
# Generate migration
alembic revision --autogenerate -m "description"

# Check SQL
alembic upgrade head --sql

# Apply
alembic upgrade head
```

**Rolling back a migration**:
```bash
# Rollback last migration
alembic downgrade -1

# Rollback to specific version
alembic downgrade <revision>
```

**Best practices**:
- Test migrations locally with production-like data before deployment
- Backup database before migrations
- Reversible migrations (downgrade support)
- Don't drop columns in same migration as creation (two-phase)
- Validate migrations with `--sql` flag before applying

### 5. Monitoring and System Health

#### 5.1 Health Checks

**Application health endpoint**:
```python
# GET /health
{
  "status": "healthy",
  "database": "connected",
  "telegram_api": "reachable",
  "openrouter_api": "reachable",
  "version": "0.1.0"
}
```

**Availability check**:
```bash
# HTTP health check every 30 seconds
curl -f https://your-domain.com/health || exit 1
```

#### 5.2 Monitoring Metrics

**System metrics**:
- CPU utilization (< 70%)
- Memory usage (< 80%)
- Disk space (< 80%)
- Network latency

**Application**:
- Request rate (req/minute)
- Response time (p50, p95, p99)
- Error rate (< 1%)
- Active users (concurrent sessions)

**Database**:
- Connection pool utilization
- Query performance (slow queries > 100ms)
- Database size

**AI API (OpenRouter)**:
- Requests per model
- Fallback frequency (primary → fallback → alternative)
- Response time per model
- Free tier limit proximity
- Token consumption per user session

#### 5.3 Alerts

**Critical** (immediate action):
- Application down (health check failed)
- Database connection lost
- Error rate > 5%
- Disk space > 90%

**Warnings** (monitoring):
- Response time > 5s (p95)
- Error rate > 1%
- Memory usage > 80%
- OpenRouter API fallback frequency > 20%
- Free tier limit approaching (> 80% usage)

#### 5.4 Logging

**Log structure**:
```json
{
  "timestamp": "2025-11-01T12:00:00Z",
  "level": "INFO",
  "user_id": "123456789",
  "action": "lesson_completed",
  "lesson_id": "intro-to-prompting",
  "duration_ms": 245,
  "context": {}
}
```

**Log levels by environment**:
- Development: DEBUG (all logs)
- Production: WARNING (warnings and errors)

**Rotation and retention**:
- Rotation: Daily or 100MB size limit
- Retention: 30 days (local), 90 days (cloud storage)
- Format: JSON for structured logging

### 6. Backup and Recovery

#### 6.1 Backup Strategy

**Database**:
- **Frequency**: Daily full backup at 02:00 UTC
- **Retention**: 7 daily, 4 weekly, 3 monthly
- **Storage**: Cloud storage (S3/GCS) with encryption
- **Testing**: Monthly recovery verification

**Backup commands**:
```bash
# PostgreSQL backup
pg_dump -h <host> -U <user> -d promptheus -F c -f backup_$(date +%Y%m%d).dump

# Restore
pg_restore -h <host> -U <user> -d promptheus backup_20251101.dump
```

**Application state**:
- Configuration files: In Git
- Secrets: In secrets manager with backup
- Logs: Archive to cloud storage

#### 6.2 Disaster Recovery

**Recovery Time Objective (RTO)**: < 1 hour
**Recovery Point Objective (RPO)**: < 24 hours

**Recovery procedure**:
1. Provision new infrastructure (or use backup VM)
2. Restore database from latest backup
3. Deploy latest stable application version
4. Update Telegram webhook URL (if domain changed)
5. Validation via health checks and smoke tests
6. Monitor metrics for 1 hour

**Runbook must contain**:
- Step-by-step recovery commands
- Contact information for responsible parties
- Credentials access procedure
- Successful recovery criteria

### 7. Security

#### 7.1 Secrets management
- **Development**: `.env` file in `.gitignore`
- **Production**: Cloud secrets manager (AWS Secrets Manager, GCP Secret Manager)
- **Rotation**: API keys rotated every 90 days
- **Access**: Principle of least privilege
- **Pre-production Testing**: Use separate test bot token, never production secrets locally

#### 7.2 Network security
- **Firewall**: Only necessary ports (443, 22)
- **SSH**: Key-based authentication, disable password auth
- **SSL/TLS**: TLS 1.2+ only, strong cipher suites
- **Webhook validation**: Verify Telegram IP ranges

#### 7.3 Application security
- **Input validation**: All user inputs are validated
- **Rate limiting**: 10 requests/minute per user
- **Logging**: No sensitive data in logs (tokens, API keys)
- **Dependencies**: Regular security updates (Dependabot)

### 8. CI/CD Pipeline

#### 8.1 Continuous Integration

**On every Pull Request**:
```yaml
1. Linting and formatting (ruff, mypy)
2. Unit tests (pytest)
3. Integration tests
4. Security scan (dependencies)
5. Build Docker image (test)
```

**Requirements for merge**:
- All tests passed
- Code coverage > 80%
- No critical security issues
- Code review approved

#### 8.2 Continuous Deployment

**On merge to `develop` branch**:
```yaml
1. Run full test suite (unit + integration)
2. Build Docker image
3. Push to container registry (tag: develop-<commit-sha>)
4. Notify team in Slack/Telegram
```

**On merge to `main` branch** (Production deployment):
```yaml
1. Run full test suite (unit + integration)
2. Build Docker image
3. Push to container registry (tag: <version>, production-latest)
4. Create GitHub Release
5. Deploy to Production (manual approval required)
6. Run post-deployment smoke tests
7. Monitor metrics for 15 minutes
8. Notify team in Slack/Telegram
```

**Rollback trigger**:
- Manual trigger via CI/CD interface
- Automatic rollback if health checks fail > 5 minutes

### 9. Scaling

#### 9.1 Vertical Scaling (MVP → Growth)
- Start: 1 CPU, 1GB RAM
- Growth: 2 CPU, 2GB RAM
- Scale: 4 CPU, 4GB RAM

**Triggers for scale up**:
- CPU usage > 70% sustained for 5 minutes
- Memory usage > 80%
- Response time degradation (p95 > 5s)

#### 9.2 Horizontal Scaling (Growth → Scale)

**Migration to multi-instance**:
- Load balancer (Nginx/HAProxy/Cloud LB)
- Stateless application (session in database)
- PostgreSQL connection pooling
- Shared cache layer (Redis)

**Auto-scaling rules**:
- Scale up: CPU > 70% for 5 minutes
- Scale down: CPU < 30% for 15 minutes
- Min instances: 2 (high availability)
- Max instances: 10 (cost control)

#### 9.3 Database Scaling
- **Read replicas**: For read-heavy workloads
- **Connection pooling**: PgBouncer
- **Vertical scaling**: Managed database tier upgrades
- **Sharding**: Only if > 100K active users

### 10. Deployment Checklist

#### 10.1 Pre-deployment (Local Validation)
- [ ] All tests passed locally (unit + integration)
- [ ] Code review completed and approved
- [ ] Database migrations tested locally with production-like data
- [ ] Manual testing completed with test bot
- [ ] Environment variables configured in production secrets manager
- [ ] Secrets rotated (if needed)
- [ ] Database backup created
- [ ] Monitoring alerts configured
- [ ] Rollback plan documented

#### 10.2 Deployment
- [ ] Deploy to production (with manual approval)
- [ ] Database migrations applied successfully
- [ ] Health checks passed
- [ ] Webhook configured (if needed)
- [ ] Logs checked (no critical errors)
- [ ] Application responding to requests

#### 10.3 Post-deployment (Production Validation)
- [ ] Smoke tests completed (core user flows)
- [ ] Metrics normal (error rate < 1%, latency acceptable)
- [ ] No rollback triggered
- [ ] Monitor for 15-30 minutes
- [ ] Team notified of successful deployment
- [ ] Documentation updated (if configuration changes)

### 11. Troubleshooting

#### 11.1 Common Issues

**Bot not responding**:
1. Check health check endpoint
2. Check Docker container status: `docker compose ps`
3. Check logs: `docker compose logs -f app`
4. Check webhook: `getWebhookInfo` API call
5. Check firewall rules

**Database connection errors**:
1. Check DATABASE_URL
2. Check network connectivity to database
3. Check credentials
4. Check connection pool limits
5. Check database disk space

**OpenRouter API errors**:
1. Check API key validity
2. Check free tier limits
3. Try fallback models manually
4. Check network connectivity
5. Check logs for specific error messages

**High response time**:
1. Check database query performance
2. Check OpenRouter API latency
3. Check CPU/Memory utilization
4. Check network latency
5. Consider caching for frequently accessed data

#### 11.2 Contacts and Escalation

**Level 1** (On-call engineer):
- Bot outages
- High error rates
- Performance degradation

**Level 2** (Lead developer):
- Database issues
- Security incidents
- Architecture decisions

**Level 3** (DevOps/Infrastructure):
- Infrastructure failures
- Scaling issues
- Network problems

### 12. Documentation and Runbooks

**Required documentation**:
- [ ] Deployment runbook (this document)
- [ ] Incident response playbook
- [ ] Database migration guide
- [ ] Secrets rotation procedure
- [ ] Disaster recovery plan

**Storage**:
- Technical docs: `docs/` in Git repository
- Runbooks: Confluence/Notion with access control
- Credentials: Secrets manager
- Architecture diagrams: `docs/architecture/`

### 13. Success Milestones

**MVP deployment**:
- [ ] Bot running in production
- [ ] 50+ users onboarded in first week
- [ ] Uptime > 99%
- [ ] Zero critical security issues
- [ ] Backup and restore tested

**Growth phase**:
- [ ] Auto-scaling configured
- [ ] Monitoring and alerting fully configured
- [ ] CI/CD pipeline fully automated
- [ ] Disaster recovery tested
- [ ] Documentation complete
