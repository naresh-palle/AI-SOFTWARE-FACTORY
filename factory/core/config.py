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


# Public defaults shipped for local development. Production startup refuses these.
INSECURE_DEFAULT_SECRET_KEY = "default-factory-super-secret-key-32-bytes-min!!"
INSECURE_DEFAULT_ENCRYPTION_KEY = "7j8YlQ6xW4K9rL3uP2mE0vN5zC8bA1dF4gH7jK0lM3o="


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
    SECRET_KEY: str = INSECURE_DEFAULT_SECRET_KEY
    # Fernet key must be 32 url-safe base64-encoded bytes
    ENCRYPTION_KEY: str = INSECURE_DEFAULT_ENCRYPTION_KEY
    # When set, /api/v1 requires Authorization: Bearer <token>.
    # Production refuses to serve the API when this is empty.
    FACTORY_API_TOKEN: Optional[str] = None

    # LLM Providers
    DEFAULT_LLM_PROVIDER: str = "mock"  # mock, ollama, openai, gemini, anthropic
    OPENAI_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None
    # 127.0.0.1 reaches Ollama on the Windows host and inside WSL2.
    # Compose overrides this with host.docker.internal for the backend container.
    OLLAMA_BASE_URL: str = "http://127.0.0.1:11434"
    OLLAMA_MODEL: str = "llama3:latest"

    # GitHub Integration
    GITHUB_TOKEN: Optional[str] = None
    GITHUB_USERNAME: Optional[str] = "naresh-palle"
    GITHUB_DEFAULT_ORG: Optional[str] = None

    # Meta Developer Account
    META_APP_ID: Optional[str] = None
    META_APP_SECRET: Optional[str] = None
    META_ACCESS_TOKEN: Optional[str] = None


def enforce_production_secrets(
    environment: EnvironmentType,
    secret_key: str,
    encryption_key: str,
) -> None:
    """Refuse to boot production with the secrets published in the repository."""
    if environment != EnvironmentType.PRODUCTION:
        return
    unsafe = []
    if not secret_key or secret_key == INSECURE_DEFAULT_SECRET_KEY:
        unsafe.append("SECRET_KEY")
    if not encryption_key or encryption_key == INSECURE_DEFAULT_ENCRYPTION_KEY:
        unsafe.append("ENCRYPTION_KEY")
    if unsafe:
        names = ", ".join(unsafe)
        raise RuntimeError(f"Refusing to start in production with default or empty secrets: {names}")


settings = Settings()
