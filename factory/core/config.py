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

    # Soft-launch registration: invite_only | open
    # invite_only creates pending tenants until an administrator approves.
    REGISTRATION_MODE: str = "invite_only"

    # Comma-separated browser origins allowed to call the API.
    # Empty means local defaults in non-production; production requires an explicit list.
    CORS_ALLOWED_ORIGINS: str = (
        "http://127.0.0.1:3000,http://localhost:3000,"
        "https://palramai.in,https://www.palramai.in,https://app.palramai.in"
    )

    # Public URLs (documentation / Studio redirects). Hosting may be pending.
    PUBLIC_WEBSITE_URL: str = "https://palramai.in"
    PUBLIC_APP_URL: str = "https://app.palramai.in"
    PUBLIC_API_URL: str = "https://api.palramai.in"

    # Allow X-Tenant-Id auth bypass only for local/testing automation.
    ALLOW_TENANT_HEADER_AUTH: bool = False

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
    META_VERIFY_TOKEN: str = "factory_meta_verify_token_secure"
    META_GRAPH_VERSION: str = "v20.0"

    # Google & YouTube Developer Account
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    YOUTUBE_API_KEY: Optional[str] = None

    # X (Twitter) Developer Account
    X_CLIENT_ID: Optional[str] = None
    X_CLIENT_SECRET: Optional[str] = None
    X_API_KEY: Optional[str] = None
    X_API_SECRET: Optional[str] = None

    # LinkedIn Developer Account
    LINKEDIN_CLIENT_ID: Optional[str] = None
    LINKEDIN_CLIENT_SECRET: Optional[str] = None

    # TikTok Developer Account
    TIKTOK_CLIENT_KEY: Optional[str] = None
    TIKTOK_CLIENT_SECRET: Optional[str] = None

    # Cloud Worker & Autonomous Execution Engine
    WORKER_AUTH_TOKEN: str = "factory_cloud_worker_internal_secret_token"
    WORKER_HEARTBEAT_TIMEOUT_SECONDS: int = 60
    WORKER_LEASE_DURATION_SECONDS: int = 180
    WORKER_MAX_CONCURRENCY: int = 10
    WORKER_DEFAULT_CPU_CORES: int = 2
    WORKER_DEFAULT_MEMORY_MB: int = 4096

    # AWS Cloud Infrastructure
    AWS_REGION: str = "us-east-1"
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_S3_ARTIFACTS_BUCKET: str = "ai-software-factory-artifacts"
    AWS_ECS_CLUSTER: str = "ai-software-factory-cluster"
    AWS_ECS_TASK_FAMILY: str = "ai-factory-cloud-worker"
    AWS_SECRETS_PREFIX: str = "ai-software-factory/"

    # Execution Budget & Cost Governance
    PROJECT_DEFAULT_BUDGET_USD: float = 50.0
    WORKER_COST_PER_VCPU_HOUR_USD: float = 0.04048
    WORKER_COST_PER_GB_HOUR_USD: float = 0.004445


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


def cors_allow_origins(settings_obj: "Settings") -> list[str]:
    """Parse CORS origins. Production never falls back to wildcard."""
    raw = (settings_obj.CORS_ALLOWED_ORIGINS or "").strip()
    origins = [part.strip() for part in raw.split(",") if part.strip()]
    if origins:
        return origins
    if settings_obj.ENVIRONMENT == EnvironmentType.PRODUCTION:
        raise RuntimeError("CORS_ALLOWED_ORIGINS must be set in production")
    return [
        "http://127.0.0.1:3000",
        "http://localhost:3000",
        "http://127.0.0.1:4173",
        "http://localhost:4173",
    ]


def registration_requires_approval(settings_obj: "Settings") -> bool:
    mode = (settings_obj.REGISTRATION_MODE or "invite_only").strip().lower()
    if mode == "open":
        return False
    return True


settings = Settings()
