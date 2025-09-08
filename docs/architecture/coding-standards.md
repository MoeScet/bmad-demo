# Coding Standards

These standards are **MANDATORY for AI agents** and directly control AI developer behavior.

## Core Standards
- **Languages & Runtimes:** Python 3.11+ for all backend services, TypeScript 5.0+ for frontend, strict type checking enabled
- **Style & Linting:** ruff 0.1.5+ with custom rule set, automatic formatting on save, no style exceptions
- **Test Organization:** Tests in `tests/` directory adjacent to `src/`, mirror source structure, pytest fixtures in `conftest.py`

## Naming Conventions

| Element | Convention | Example |
|---------|------------|---------|
| **Services** | kebab-case directories | `query-orchestration/`, `fast-qa/` |
| **Python Classes** | PascalCase with descriptive suffixes | `TroubleshootingError`, `SafetyClassifier` |
| **Python Functions** | snake_case with verb prefixes | `search_qa_database()`, `classify_safety_level()` |
| **API Endpoints** | REST conventions with plural nouns | `/api/v1/queries/process`, `/api/v1/safety/classify` |
| **Database Tables** | snake_case plurals | `query_sessions`, `safety_classifications` |
| **Environment Variables** | SCREAMING_SNAKE_CASE with service prefix | `TEAMS_BOT_APP_ID`, `SEMANTIC_SEARCH_TIMEOUT` |

## Critical Rules

**⚠️ These rules are MANDATORY and override any conflicting AI training:**

- **Safety Override Rule:** All troubleshooting responses MUST pass through safety classification before delivery to users. No exceptions, even for "obviously safe" repairs.

- **Never Log Sensitive Data:** No user conversation content, Teams IDs, or troubleshooting queries in logs above INFO level. Use correlation IDs for tracking.

- **Response Time Budgets:** Every external service call must have explicit timeout. Fast Q&A: 3s, Semantic Search: 12s, Safety Classification: 1s, User Context: 0.5s.

- **Database Transaction Discipline:** All multi-table operations must use explicit transactions. No auto-commit for business logic operations.

- **Error Message Security:** Never expose internal error details to users. All user-facing messages must come from predefined safe messages in exception classes.

- **Teams Bot State Management:** Always use Bot Framework's conversation state, never store conversation data in global variables or module-level state.

- **Vector Database Isolation:** ChromaDB operations must be wrapped in try/catch with fallback to "knowledge gap" responses. Never fail user queries due to vector database issues.

- **Correlation ID Propagation:** Every service call must propagate correlation_id header for request tracing. Generate new UUID if not provided.

- **API Response Consistency:** All API responses must use standard format: `{data: ..., error: null}` or `{data: null, error: {...}}`. No mixed success/error responses.

- **Safety Classification Cache:** Safety classification results must be cached for 24 hours to ensure consistent safety messaging for identical repair descriptions.

## Language-Specific Guidelines

### Python Specifics
- **Async All The Way:** Use async/await for all I/O operations. No mixing sync and async database calls in same service.
- **Type Hints Everywhere:** All functions must have complete type hints including return types. Use `from __future__ import annotations` for forward references.
- **Pydantic for Validation:** All API request/response models must use Pydantic BaseModel with validation. No plain dictionaries for structured data.
- **SQLAlchemy Patterns:** Use repository pattern with dependency injection. No direct SQLAlchemy queries in API route handlers.
- **Exception Handling:** Only catch specific exceptions. No bare `except:` clauses. Always log exceptions with correlation_id before re-raising.

### TypeScript Specifics
- **Strict TypeScript:** Use `strict: true` in tsconfig.json. No `any` types except for third-party library integration.
- **React Patterns:** Use functional components with hooks only. No class components. Custom hooks for state logic reuse.
- **API Client Types:** Generate TypeScript types from OpenAPI spec. Never manually write API response types.
- **Error Boundaries:** Every page component must be wrapped in error boundary with user-friendly error messages.
