# Infrastructure and Deployment

## Infrastructure as Code
- **Tool:** Railway CLI and configuration files with Render YAML backup
- **Location:** `infrastructure/` directory in monorepo
- **Approach:** Platform-native configuration with Docker containers for consistency

## Deployment Strategy
- **Strategy:** Blue-Green deployment simulation using Railway's preview deployments
- **CI/CD Platform:** GitHub Actions (free tier) with automated testing and deployment
- **Pipeline Configuration:** `.github/workflows/` with separate pipelines for each service

## Environments
- **Development:** Local Docker Compose environment with shared PostgreSQL and ChromaDB
- **Staging:** Railway preview deployments triggered by pull requests to main branch
- **Production:** Railway main deployment with automatic promotion after staging validation
- **Testing:** Temporary Railway deployments for load testing and integration validation

## Environment Promotion Flow
```
Feature Branch → Development (Local)
       ↓
Pull Request → Staging (Railway Preview)  
       ↓
Code Review → Merge to Main
       ↓
Automated Tests → Production (Railway Main)
       ↓
Health Checks → Live Traffic
```

## Rollback Strategy
- **Primary Method:** Railway's built-in deployment rollback with Git SHA-based versioning
- **Trigger Conditions:** Health check failures, response time degradation >15 seconds, error rate >5%
- **Recovery Time Objective:** <5 minutes to previous stable deployment
