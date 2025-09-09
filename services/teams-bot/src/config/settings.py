"""
Microsoft Teams Bot Service Configuration
Environment configuration for Teams bot with Bot Framework integration.
"""
from __future__ import annotations

import os
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class TeamsConfig(BaseSettings):
    """Teams Bot Service Configuration with Bot Framework and Microsoft Graph settings."""
    
    # Service Information
    SERVICE_NAME: str = "teams-bot"
    SERVICE_VERSION: str = "1.2.0"
    ENVIRONMENT: str = Field(default="development", description="Deployment environment")
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    LOG_FORMAT: str = Field(default="json", description="Logging format")
    
    # Server Configuration
    HOST: str = Field(default="0.0.0.0", description="Server host")
    PORT: int = Field(default=8000, description="Server port")
    
    # CORS Configuration
    CORS_ORIGINS: Optional[list[str]] = Field(default=None, description="CORS allowed origins")
    
    # Database Configuration
    DATABASE_URL: str = Field(description="PostgreSQL database connection URL")
    
    # Microsoft Teams Bot Framework Configuration
    TEAMS_BOT_APP_ID: str = Field(description="Microsoft Teams application ID for bot registration")
    TEAMS_BOT_APP_PASSWORD: str = Field(description="Bot Framework application password for authentication")
    TEAMS_BOT_WEBHOOK_URL: str = Field(description="Public webhook URL for Teams message delivery")
    
    # Microsoft Graph API Configuration
    MICROSOFT_GRAPH_BASE_URL: str = Field(default="https://graph.microsoft.com/v1.0", description="Microsoft Graph API base URL")
    MICROSOFT_GRAPH_SCOPE: str = Field(default="https://graph.microsoft.com/.default", description="Graph API scope")
    
    # Service Timeouts (in seconds)
    USER_CONTEXT_TIMEOUT: float = Field(default=0.5, description="User Context Service timeout")
    TEAMS_API_TIMEOUT: float = Field(default=30.0, description="Teams API call timeout")
    
    # External Service URLs
    QUERY_ORCHESTRATION_URL: str = Field(description="Query Orchestration Service URL")
    USER_CONTEXT_URL: str = Field(description="User Context Service URL")
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "forbid"
    
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.ENVIRONMENT.lower() == "production"
    
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.ENVIRONMENT.lower() == "development"


# Global configuration instance
teams_config = TeamsConfig()