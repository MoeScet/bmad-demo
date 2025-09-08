# Test Strategy and Standards

## Testing Philosophy
- **Approach:** Test-Driven Development for safety-critical components, test-after for UI and integration features
- **Coverage Goals:** 90% line coverage for core business logic, 100% for safety classification, 70% overall project coverage
- **Test Pyramid:** 40% unit tests, 40% integration tests, 20% end-to-end tests (inverted for microservices architecture)

## Test Types and Organization

### Unit Tests
- **Framework:** pytest 7.4.3 with asyncio support and fixtures
- **File Convention:** `test_*.py` files in `tests/` directory adjacent to `src/`
- **Location:** Each service has `tests/` directory mirroring `src/` structure
- **Mocking Library:** pytest-mock with unittest.mock for external dependencies
- **Coverage Requirement:** 90% for business logic modules, 100% for safety classification

**AI Agent Requirements:**
- Generate tests for all public methods with safety implications
- Cover edge cases: empty results, timeout scenarios, invalid inputs
- Follow AAA pattern (Arrange, Act, Assert) with descriptive test names
- Mock all external dependencies (database, APIs, vector stores)
- Include performance assertions for response time budgets

### Integration Tests
- **Scope:** Service-to-service communication, database operations, external API integration
- **Location:** `tests/integration/` in project root
- **Test Infrastructure:**
  - **PostgreSQL:** Testcontainers with PostgreSQL 15 for realistic database testing
  - **ChromaDB:** In-memory ChromaDB instance for vector operations
  - **Microsoft Teams API:** WireMock for stubbing Teams Bot Framework calls
  - **HTTP Services:** httpx test client for FastAPI service testing

### End-to-End Tests
- **Framework:** pytest with async support for full workflow testing
- **Scope:** Complete user journeys from Teams message to response delivery
- **Environment:** Dedicated testing environment on Railway with production-like data
- **Test Data:** Curated dataset of realistic troubleshooting queries with expected outcomes

## Test Data Management
- **Strategy:** Factory pattern for test data generation with realistic troubleshooting scenarios
- **Fixtures:** SQL fixtures in `tests/fixtures/test_data.sql` with common Q&A pairs and manual content
- **Factories:** Python factories using `factory_boy` for generating realistic user contexts and queries
- **Cleanup:** Automatic database cleanup after each test using pytest fixtures

## Continuous Testing
- **CI Integration:** GitHub Actions with parallel test execution for each service
- **Performance Tests:** Automated performance testing with response time validation in CI pipeline
- **Security Tests:** SAST scanning with bandit for Python security issues, npm audit for frontend
