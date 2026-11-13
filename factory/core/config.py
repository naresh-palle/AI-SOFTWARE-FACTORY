"""
Factory Configuration and Environment Management.
"""

from enum import Enum
from pathlib import Path
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ExecutionMode(str, Enum):
    ASSISTED = "assisted"
    SEMI_AUTONOMOUS = "semi-autonomous"
    AUTONOMOUS = "autonomous"


class EnvironmentType(str, Enum):
    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Core
    APP_NAME: str = "Autonomous AI Software Development Factory"
    ENVIRONMENT: EnvironmentType = EnvironmentType.DEVELOPMENT
    DEFAULT_EXECUTION_MODE: ExecutionMode = ExecutionMode.AUTONOMOUS
    DEBUG: bool = False

    # Base Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    PROJECTS_STORAGE_DIR: Path = BASE_DIR / "workspace_projects"

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./factory.db"
    POSTGRES_SERVER: Optional[str] = "localhost"
    POSTGRES_USER: Optional[str] = "postgres"
    POSTGRES_PASSWORD: Optional[str] = "postgres"
    POSTGRES_DB: Optional[str] = "ai_factory"

    # Redis Cache & Task Bus
    REDIS_URL: str = "redis://localhost:6379/0"

    # Security & Encryption
    SECRET_KEY: str = "default-factory-super-secret-key-32-bytes-min!!"
    # Fernet key must be 32 url-safe base64-encoded bytes
    ENCRYPTION_KEY: str = "7j8YlQ6xW4K9rL3uP2mE0vN5zC8bA1dF4gH7jK0lM3o="

    # LLM Providers
    DEFAULT_LLM_PROVIDER: str = "mock"  # mock, ollama, openai, gemini, anthropic
    OPENAI_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None
    OLLAMA_BASE_URL: str = "http://172.18.0.2:11434"
    OLLAMA_MODEL: str = "llama3:latest"

    # GitHub Integration
    GITHUB_TOKEN: Optional[str] = None
    GITHUB_USERNAME: Optional[str] = "naresh-palle"
    GITHUB_DEFAULT_ORG: Optional[str] = None

    # Meta Developer Account
    META_APP_ID: Optional[str] = None
    META_APP_SECRET: Optional[str] = None
    META_ACCESS_TOKEN: Optional[str] = None


settings = Settings()
