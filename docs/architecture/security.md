# Security

## Input Validation
- **Validation Library:** Pydantic 2.4+ with custom validators for troubleshooting queries
- **Validation Location:** All external inputs validated at API boundary before processing
- **Required Rules:**
  - All user queries MUST be sanitized to remove potential injection attempts
  - Teams user IDs validated against Microsoft Graph API format requirements
  - File uploads limited to PDF format with MIME type verification and size limits (<50MB)
  - Search queries limited to 500 characters with content filtering for malicious patterns

## Authentication & Authorization
- **Auth Method:** Microsoft Teams SSO with OAuth 2.0 and JWT token validation
- **Session Management:** Bot Framework conversation state with encrypted storage, 24-hour expiry
- **Required Patterns:**
  - All API endpoints MUST validate Teams JWT tokens using Microsoft public keys
  - Admin endpoints require additional API key authentication with role-based access control
  - User context access restricted to authenticated Teams user's own data only
  - Service-to-service communication uses mutual TLS with certificate validation

## Secrets Management
- **Development:** `.env` files with `.env.example` template, never committed to version control
- **Production:** Railway environment variables with encryption at rest
- **Code Requirements:**
  - NEVER hardcode API keys, connection strings, or authentication tokens
  - Access secrets via environment variables with fallback to secure defaults
  - No secrets in logs, error messages, or client-side code
  - Rotate all API keys and tokens every 90 days with automated alerts

## API Security
- **Rate Limiting:** 60 requests per minute per user, 10 requests per minute for expensive operations
- **CORS Policy:** Restricted to Teams client domains and approved admin dashboard origins
- **Security Headers:** Strict-Transport-Security, X-Content-Type-Options, X-Frame-Options, Content-Security-Policy
- **HTTPS Enforcement:** All API endpoints require HTTPS, automatic HTTP to HTTPS redirect

## Data Protection
- **Encryption at Rest:** PostgreSQL with TDE enabled, ChromaDB with encryption plugins
- **Encryption in Transit:** TLS 1.3 for all external communications, mutual TLS for service-to-service
- **PII Handling:** Teams user IDs hashed for analytics, no conversation content stored beyond session duration
- **Logging Restrictions:** No user queries, personal identifiers, or troubleshooting content in persistent logs

## Dependency Security
- **Scanning Tool:** GitHub Dependabot with automatic security updates for critical vulnerabilities
- **Update Policy:** Security patches applied within 48 hours, dependency updates monthly
- **Approval Process:** New dependencies require security review and documentation of usage justification

## Security Testing
- **SAST Tool:** bandit for Python static analysis with custom rules for troubleshooting context
- **DAST Tool:** OWASP ZAP integration in CI pipeline for API endpoint scanning
- **Penetration Testing:** Annual third-party security assessment for enterprise compliance
