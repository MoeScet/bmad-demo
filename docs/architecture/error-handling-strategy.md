# Error Handling Strategy

## General Approach
- **Error Model:** Structured exception hierarchy with HTTP status codes and user-friendly messages
- **Exception Hierarchy:** Base `TroubleshootingError` with specific subclasses for different failure modes
- **Error Propagation:** Fail-fast approach with graceful degradation and safety fallbacks

## Logging Standards
- **Library:** Python `structlog` 23.1.0 with JSON formatting for structured logging
- **Format:** Structured JSON logs with consistent field naming and timestamp formats
- **Levels:** DEBUG (development), INFO (user actions), WARN (recoverable errors), ERROR (failures), CRITICAL (safety issues)
- **Required Context:**
  - **Correlation ID:** UUID v4 format tracked across service boundaries (`correlation_id`)
  - **Service Context:** Service name, version, and deployment environment (`service`, `version`, `environment`)
  - **User Context:** Anonymized user identifier and session context when available (`user_id`, `session_id`)

## Error Handling Patterns

### External API Errors
- **Retry Policy:** Exponential backoff with max 3 retries (100ms, 200ms, 400ms intervals)
- **Circuit Breaker:** Open circuit after 5 consecutive failures, half-open retry after 60 seconds
- **Timeout Configuration:** 5 seconds for Microsoft Graph API, 3 seconds for Bot Framework API
- **Error Translation:** External API errors mapped to user-friendly messages with fallback guidance

### Business Logic Errors
- **Custom Exceptions:** Specific exception types for domain errors (`SafetyViolationError`, `UnsupportedModelError`, `InsufficientDataError`)
- **User-Facing Errors:** Clear, actionable messages that guide users to alternative solutions
- **Error Codes:** Structured error codes for programmatic handling (`SAFETY_001`, `MODEL_404`, `SEARCH_TIMEOUT`)

### Data Consistency
- **Transaction Strategy:** Database transactions with automatic rollback on failures, no distributed transactions
- **Compensation Logic:** Async compensation for failed operations (e.g., cleanup incomplete manual processing)
- **Idempotency:** All mutation operations designed for safe retry with UUID-based deduplication
