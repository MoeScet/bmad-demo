# Technical Assumptions

## Repository Structure: Monorepo
Single repository containing Teams bot, API backend, manual processing pipeline, and admin interface. This approach simplifies deployment, dependency management, and development workflow within free-tier constraints while supporting the microservices architecture described in your Project Brief.

## Service Architecture
**Microservices within Monorepo**: Separate services for fast Q&A lookup, semantic search, user context management, and safety classification. Services communicate via REST APIs and share common data layer, enabling independent scaling while maintaining deployment simplicity for free-tier hosting platforms.

## Testing Requirements
**Unit + Integration Testing**: Comprehensive unit tests for core logic (safety classification, context detection, search algorithms) with integration tests for Teams bot interactions and API endpoints. Manual testing convenience methods for troubleshooting response validation given the contextual nature of accuracy assessment.

## Additional Technical Assumptions and Requests

**Backend Technology Stack:**
- **Python with FastAPI**: High-performance API framework with automatic OpenAPI documentation, async support for concurrent users, and excellent free-tier hosting compatibility
- **PostgreSQL**: Free-tier relational database for structured data (user contexts, Q&A pairs, usage metrics) with JSON support for flexible troubleshooting response storage
- **ChromaDB or Weaviate**: Open-source vector database for semantic search embeddings, chosen based on free hosting availability and performance benchmarks

**Frontend and Integration:**
- **Microsoft Teams Bot Framework SDK**: Official SDK for native Teams integration with authentication, conversation state management, and adaptive card support
- **React-based Admin Dashboard**: Web interface for content management, analytics, and system monitoring using Create React App for rapid development

**Infrastructure and Deployment:**
- **Railway or Render**: Free-tier cloud platforms with automatic scaling, Git-based deployment, and PostgreSQL hosting capabilities
- **GitHub Actions**: Free CI/CD pipeline for automated testing, build processes, and deployment workflows
- **Hugging Face Transformers**: Open-source embedding models (sentence-transformers) for semantic search without premium API costs

**Security and Compliance:**
- **Teams SSO Integration**: Leverage Microsoft identity for user authentication, eliminating custom user management complexity
- **Environment-based Configuration**: Secure secrets management using platform environment variables
- **Request Rate Limiting**: Protection against abuse using free middleware solutions
