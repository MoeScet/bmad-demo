# External APIs

## Microsoft Graph API
**Purpose:** User authentication, profile information, and Teams organization context

- **Documentation:** https://docs.microsoft.com/en-us/graph/api/overview
- **Base URL(s):** https://graph.microsoft.com/v1.0
- **Authentication:** OAuth 2.0 with Teams SSO integration
- **Rate Limits:** 10,000 requests per 10 minutes per application

**Key Endpoints Used:**
- `GET /me` - Retrieve authenticated user profile
- `GET /me/memberOf` - Get user's team/organization memberships
- `GET /users/{id}` - Lookup user information for context

**Integration Notes:** Used primarily during initial user authentication and context setup. Minimal ongoing API calls to stay within rate limits. Cached user information in local database to reduce external dependencies.

## Microsoft Bot Framework API
**Purpose:** Teams bot conversation management, message delivery, and adaptive card rendering

- **Documentation:** https://docs.microsoft.com/en-us/azure/bot-service/
- **Base URL(s):** https://api.botframework.com/v3, https://smba.trafficmanager.net/apis
- **Authentication:** Bot Framework JWT tokens with app credentials
- **Rate Limits:** 600 calls per minute per bot, 1800 calls per minute per app

**Key Endpoints Used:**
- `POST /v3/conversations/{conversationId}/activities` - Send messages to Teams
- `POST /v3/conversations/{conversationId}/activities/{activityId}` - Update existing messages
- `GET /v3/conversations/{conversationId}/members` - Get conversation participants

**Integration Notes:** Core integration for Teams functionality. SDK handles token management and retry logic. Implements circuit breaker pattern for resilience against Teams service outages.

## Hugging Face Model Hub (Self-Hosted)
**Purpose:** Download and local deployment of sentence-transformer models for embeddings

- **Documentation:** https://huggingface.co/sentence-transformers
- **Base URL(s):** https://huggingface.co (model download only)
- **Authentication:** None required for public models
- **Rate Limits:** Download throttling only, no runtime API limits

**Key Models Used:**
- `sentence-transformers/all-MiniLM-L6-v2` - General purpose semantic embeddings
- `sentence-transformers/all-mpnet-base-v2` - Higher quality embeddings for manual content

**Integration Notes:** Models downloaded once during deployment and run locally. No ongoing API dependencies or costs. Fallback model available if primary model unavailable during initial setup.
