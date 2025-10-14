"""
Core configuration for the Lead Management System.
Uses Pydantic settings for validation and environment variable support.
"""

import secrets
from typing import List, Optional, Union

from pydantic import field_validator, ValidationInfo
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings with environment variable support.
    """

    # Project Info
    PROJECT_NAME: str = "Lead Management AI System"
    PROJECT_DESCRIPTION: str = "A comprehensive AI-powered lead management system with multi-agent architecture"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # Security
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days

    # Server
    SERVER_NAME: str = "Lead Management API"
    SERVER_HOST: str = "http://localhost"
    DEBUG: bool = True

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",  # React dev server
        "http://localhost:8501",  # Streamlit dashboard
        "http://localhost:8080",  # Alternative frontend
    ]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(
        cls, v: Union[str, List[str]]
    ) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # Trusted Hosts
    ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1"]

    # Database
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "lead_user"
    POSTGRES_PASSWORD: str = "lead_password"
    POSTGRES_DB: str = "lead_management"
    POSTGRES_PORT: str = "5432"
    DATABASE_URL: Optional[str] = None

    @property
    def sql_database_url(self) -> str:
        """Generate SQLAlchemy database URL."""
        if self.DATABASE_URL:
            return self.DATABASE_URL

        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = None
    REDIS_DB: int = 0

    @property
    def redis_url(self) -> str:
        """Generate Redis URL."""
        auth = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        return f"redis://{auth}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # AI/LLM Configuration
    XAI_API_KEY: str = ""
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None

    # External APIs
    CRM_API_KEY: Optional[str] = None
    CRM_BASE_URL: str = "https://api.crmplatform.com"

    # Email Configuration
    SMTP_TLS: bool = True
    SMTP_PORT: Optional[int] = None
    SMTP_HOST: Optional[str] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAILS_FROM_EMAIL: Optional[str] = None
    EMAILS_FROM_NAME: Optional[str] = None

    # File Upload
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB

    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 60  # seconds

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    # Testing
    TESTING: bool = False

    class Config:
        env_file = ".env"
        case_sensitive = True


# Create global settings instance
settings = Settings()