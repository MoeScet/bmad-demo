# Tech Stack

This is the **DEFINITIVE** technology selection section that serves as the single source of truth for all development decisions.

## Cloud Infrastructure
- **Provider:** Railway (Primary) with Render as backup option
- **Key Services:** PostgreSQL hosting, container deployment, environment management  
- **Deployment Regions:** US-East (closest to Microsoft Teams data centers)

## Technology Stack Table

| Category | Technology | Version | Purpose | Rationale |
|----------|------------|---------|---------|-----------|
| **Language** | Python | 3.11 | Primary development language | Modern async features, FastAPI optimization, strong typing |
| **Runtime** | Python | 3.11.5 | Application runtime | LTS stability, performance improvements |
| **Backend Framework** | FastAPI | 0.104.1 | REST API and async services | High performance, automatic OpenAPI, async support |
| **Database** | PostgreSQL | 15.4 | Primary data storage | JSON support, reliability, free-tier availability |
| **Vector Database** | ChromaDB | 0.4.15 | Semantic search storage | Python-native, simple deployment, open-source |
| **ORM** | SQLAlchemy | 2.0.23 | Database abstraction | Async support, migration tools, FastAPI compatibility |
| **Teams Integration** | Bot Framework SDK | 4.15.0 | Microsoft Teams interface | Official SDK, conversation state, adaptive cards |
| **Frontend Framework** | React | 18.2.0 | Admin dashboard UI | Component ecosystem, team expertise |
| **Build Tool** | Vite | 4.5.0 | Frontend build system | Fast HMR, modern tooling, optimized builds |
| **Embeddings** | sentence-transformers | 2.2.2 | Text embeddings for search | Open-source, no API costs, proven performance |
| **HTTP Client** | httpx | 0.25.0 | Async HTTP requests | FastAPI compatibility, async support |
| **Authentication** | Microsoft Graph SDK | 1.2.0 | Teams SSO integration | Official SDK, secure token handling |
| **Testing Framework** | pytest | 7.4.3 | Unit and integration testing | Async support, fixtures, extensive plugins |
| **Code Quality** | ruff | 0.1.5 | Linting and formatting | Fast, comprehensive, replaces multiple tools |
| **Deployment** | Railway | Latest | Cloud platform | Git-based deployment, PostgreSQL, free tier |
| **CI/CD** | GitHub Actions | Latest | Automated pipeline | Free for public repos, Docker support |
| **Monitoring** | Better Stack | Free Tier | Uptime and error tracking | Free tier, simple setup, good alerting |
