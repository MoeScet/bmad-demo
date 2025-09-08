# Source Tree

```
rag-washing-troubleshoot/
├── .github/
│   ├── workflows/
│   │   ├── ci-backend.yml              # Backend CI/CD pipeline
│   │   ├── ci-frontend.yml             # Frontend CI/CD pipeline
│   │   ├── deploy-staging.yml          # Staging deployment
│   │   └── deploy-production.yml       # Production deployment
│   └── ISSUE_TEMPLATE/
│       ├── bug_report.md
│       └── feature_request.md
│
├── services/
│   ├── teams-bot/                      # Microsoft Teams Bot Service
│   │   ├── src/
│   │   │   ├── main.py                 # FastAPI app entry point
│   │   │   ├── bot/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── teams_bot.py        # Teams bot implementation
│   │   │   │   ├── conversation.py     # Conversation state management
│   │   │   │   └── adapters/
│   │   │   │       ├── teams_adapter.py
│   │   │   │       └── auth_adapter.py
│   │   │   ├── api/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── webhooks.py         # Teams webhook handlers
│   │   │   │   └── health.py           # Health check endpoints
│   │   │   └── config/
│   │   │       ├── __init__.py
│   │   │       └── settings.py         # Service configuration
│   │   ├── tests/
│   │   ├── requirements.txt
│   │   ├── Dockerfile
│   │   └── README.md
│   │
│   ├── query-orchestration/            # Query Orchestration Service
│   ├── fast-qa/                        # Fast Q&A Service
│   ├── semantic-search/                # Semantic Search Service
│   ├── safety-classification/          # Safety Classification Service
│   ├── user-context/                   # User Context Service
│   ├── manual-processing/              # Manual Processing Pipeline
│   └── management-api/                 # Management API Service
│
├── web/                                # Admin Dashboard Frontend
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   └── types/
│   ├── package.json
│   └── vite.config.ts
│
├── shared/                             # Shared Libraries and Utilities
│   ├── python/
│   │   ├── database/
│   │   ├── models/
│   │   ├── auth/
│   │   ├── utils/
│   │   └── types/
│   └── typescript/
│
├── infrastructure/                     # Infrastructure as Code
│   ├── railway/
│   ├── database/
│   └── monitoring/
│
├── scripts/                           # Development and Deployment Scripts
├── docs/                             # Documentation
├── tests/                            # Integration and E2E Tests
├── docker-compose.yml                # Local development environment
├── Makefile                          # Development task automation
└── README.md                         # Project overview and setup
```
