# REST API Spec

```yaml
openapi: 3.0.0
info:
  title: RAG-Powered Washing Machine Troubleshooting API
  version: 1.0.0
  description: |
    Comprehensive API specification for the RAG-powered washing machine troubleshooting system.
    Supports tiered search architecture, user context management, safety classification, and analytics.
    
    ## Authentication
    - Teams Bot endpoints use Bot Framework JWT tokens
    - Admin endpoints require API key authentication
    - User context endpoints use Teams SSO integration
    
    ## Rate Limiting
    - Query processing: 60 requests per minute per user
    - Admin operations: 100 requests per minute
    - Analytics endpoints: 30 requests per minute
servers:
  - url: https://api.washing-troubleshoot.app/v1
    description: Production API Server

paths:
  /query/process:
    post:
      summary: Process troubleshooting query
      description: |
        Main endpoint for processing user troubleshooting queries through tiered search architecture.
        Orchestrates fast Q&A lookup, semantic search fallback, safety classification, and context adaptation.
      operationId: processQuery
      tags: [Query Processing]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [query_text, user_id, session_id]
              properties:
                query_text:
                  type: string
                  description: User's natural language troubleshooting question
                  example: "My washing machine won't drain"
                user_id:
                  type: string
                  format: uuid
                  description: Teams user identifier
                session_id:
                  type: string
                  format: uuid
                  description: Conversation session identifier
      responses:
        '200':
          description: Successful query processing
          content:
            application/json:
              schema:
                type: object
                required: [response_text, source_type, confidence_score, response_time_ms]
                properties:
                  response_text:
                    type: string
                    description: Formatted troubleshooting response for user
                  source_type:
                    type: string
                    enum: [fast_qa, semantic_search, safety_override, knowledge_gap]
                  confidence_score:
                    type: number
                    minimum: 0.0
                    maximum: 1.0
                  response_time_ms:
                    type: integer

components:
  securitySchemes:
    BotFrameworkAuth:
      type: http
      scheme: bearer
      description: Microsoft Bot Framework JWT token
    TeamsSSO:
      type: oauth2
      flows:
        authorizationCode:
          authorizationUrl: https://login.microsoftonline.com/common/oauth2/v2.0/authorize
          tokenUrl: https://login.microsoftonline.com/common/oauth2/v2.0/token
          scopes:
            User.Read: Read user profile

security:
  - BotFrameworkAuth: []
  - TeamsSSO: []
```
