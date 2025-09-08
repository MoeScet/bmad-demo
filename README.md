# BMAD - Business Management Application Development

A Microsoft Teams-integrated troubleshooting assistant for washing machine repairs with RAG-based knowledge retrieval and safety classification.

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+ (for web dashboard)
- PostgreSQL 15+ (local or Railway)
- Git

### Development Setup

1. **Clone and setup environment:**
   ```bash
   git clone <repository-url>
   cd BMAD
   
   # Run automated setup (creates venvs and installs dependencies)
   python scripts/setup-dev-env.py
   # OR for Unix/Linux/MacOS:
   ./scripts/setup-dev-env.sh
   ```

2. **Configure environment variables:**
   ```bash
   # Copy environment templates for each service
   cp services/teams-bot/.env.example services/teams-bot/.env
   cp services/semantic-search/.env.example services/semantic-search/.env
   # ... repeat for other services
   
   # Edit .env files with your actual configuration
   ```

3. **Set up database:**
   ```bash
   # Create local PostgreSQL database or use Railway
   createdb bmad_dev
   
   # Run migrations
   psql bmad_dev -f infrastructure/database/migrations/001_initial_schema.sql
   ```

4. **Start development services:**
   ```bash
   # Start individual services
   cd services/teams-bot
   source venv/bin/activate  # Windows: venv\Scripts\activate
   uvicorn src.main:app --reload --port 8001
   
   # Or use Docker Compose for full stack
   docker-compose up -d
   ```

### Project Structure

```
BMAD/
├── services/                    # Microservices
│   ├── teams-bot/              # Microsoft Teams Bot
│   ├── query-orchestration/     # Query routing and orchestration
│   ├── fast-qa/                # Fast Q&A lookup service
│   ├── semantic-search/        # Vector-based semantic search
│   ├── safety-classification/  # Repair safety assessment
│   ├── user-context/           # User profile and history
│   ├── manual-processing/      # Document processing pipeline
│   └── management-api/         # Admin and management API
├── web/                        # React admin dashboard
├── shared/                     # Shared libraries and utilities
│   ├── python/                # Shared Python packages
│   └── typescript/            # Shared TypeScript types
├── infrastructure/            # Infrastructure as Code
│   ├── railway/              # Railway deployment config
│   ├── database/            # DB schema and migrations
│   └── monitoring/          # Monitoring and observability
├── scripts/                  # Development and deployment scripts
├── tests/                   # Integration and E2E tests
└── docs/                   # Project documentation
```

## 🛠 Technology Stack

| Component | Technology | Version | Purpose |
|-----------|------------|---------|---------|
| **Backend** | Python + FastAPI | 3.11 / 0.104.1 | High-performance async API services |
| **Database** | PostgreSQL | 15.4 | Primary data storage with JSON support |
| **Vector DB** | ChromaDB | 0.4.15 | Semantic search and embeddings |
| **Frontend** | React + TypeScript | 18.2.0 / 5.0+ | Admin dashboard interface |
| **Cloud Platform** | Railway | Latest | Container deployment and PostgreSQL |
| **CI/CD** | GitHub Actions | Latest | Automated testing and deployment |
| **Teams Integration** | Bot Framework SDK | 4.15.0 | Microsoft Teams interface |

## 🏗 Development Workflow

### Code Standards

- **Python:** Follow PEP 8, use `ruff` for linting, async/await for all I/O
- **TypeScript:** Strict mode, no `any` types, functional React components
- **Database:** Snake_case naming, explicit transactions for multi-table ops
- **API:** REST conventions, correlation ID propagation, standardized error responses

### Testing Strategy

```bash
# Run unit tests for specific service
cd services/teams-bot
pytest tests/ -v --cov=src

# Run integration tests
pytest tests/integration/ -v

# Run linting and type checking
ruff check src/
mypy src/ --ignore-missing-imports
```

### Environment Configuration

Each service uses environment-specific configuration:

- **Development:** Local PostgreSQL, debug logging, mock Teams integration
- **Staging:** Railway preview deployments, integration testing
- **Production:** Railway main branch, structured logging, full monitoring

### Git Workflow

1. Create feature branch: `git checkout -b feature/your-feature`
2. Make changes following coding standards
3. Run tests: `make test` (or service-specific test commands)
4. Create PR with clear description and acceptance criteria
5. Automated CI runs tests and security scans
6. Deploy to staging for integration testing
7. Deploy to production on main branch merge

## 🚀 Deployment

### Staging Deployment

```bash
# Automatic on push to develop branch
git push origin develop

# Manual trigger
gh workflow run deploy-staging.yml
```

### Production Deployment

```bash
# Automatic on push to main branch  
git push origin main

# Manual deployment with specific version
gh workflow run deploy-production.yml -f version=v1.2.0
```

### Railway Configuration

Services are deployed as separate Railway services:
- `bmad-teams-bot-prod`
- `bmad-query-orchestration-prod`
- `bmad-semantic-search-prod`
- etc.

PostgreSQL database shared across services with proper connection pooling.

## 📊 Monitoring and Observability

### Logging

- **Structured JSON logging** with correlation ID tracking
- **Log levels:** DEBUG (dev), INFO (user actions), WARN (recoverable), ERROR (failures), CRITICAL (safety)
- **Service context:** Automatic service name, version, environment tagging

### Metrics

- **Health checks:** `/health` endpoint for each service
- **Performance metrics:** Response times, database query performance
- **Business metrics:** Query success rates, safety classification accuracy

### Alerting

- **Better Stack** for uptime monitoring
- **Teams webhook** notifications for deployment status
- **Error thresholds** for automatic alerting

## 🔒 Security Considerations

- **No sensitive data in logs** above INFO level
- **Secrets management** via Railway environment variables
- **Safety classification** required for all repair responses
- **Correlation ID** tracking for audit trails
- **Input validation** with Pydantic models
- **Rate limiting** and timeout enforcement

## 📚 API Documentation

Once services are running, API documentation is available at:
- Teams Bot: `http://localhost:8001/docs`
- Query Orchestration: `http://localhost:8002/docs`
- Fast Q&A: `http://localhost:8003/docs`

## 🤝 Contributing

1. Read the [coding standards](docs/architecture/coding-standards.md)
2. Check the [development guidelines](docs/architecture/tech-stack.md)
3. Follow the testing requirements in [test strategy](docs/architecture/test-strategy-and-standards.md)
4. Ensure all changes pass CI/CD pipeline
5. Update documentation for new features

## 📞 Support

- **Issues:** Create GitHub issue with bug report or feature request template
- **Questions:** Check existing documentation or create discussion
- **Security:** Report security issues privately via email

## 📈 Project Status

- ✅ Infrastructure setup and configuration
- 🔄 Teams bot implementation
- 🔄 Query orchestration service
- 📋 Semantic search integration
- 📋 Safety classification system
- 📋 Admin dashboard development

---

**Built with BMAD™ Core Framework**