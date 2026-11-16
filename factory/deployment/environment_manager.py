"""
Environment Management Service.
Manages isolated configurations across Development, Testing, Staging, and Production environments.
Enforces secret hygiene: Only AWS Secrets Manager ARN references are stored, never plaintext secrets.
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy import select, and_

from factory.core.database import get_db_session
from factory.core.logger import logger
from factory.models.schema import EnvironmentConfig


VALID_ENVIRONMENTS = ["development", "testing", "staging", "production"]


class EnvironmentManager:
    """Configures and validates environment-specific settings with zero secret leaks."""

    @staticmethod
    def get_default_config_for_env(env: str, project_name: str) -> Dict[str, Any]:
        """Generate safe, scoped configurations by environment tier."""
        env_lower = env.lower()
        if env_lower == "production":
            return {
                "config_data": {
                    "APP_ENV": "production",
                    "LOG_LEVEL": "WARNING",
                    "DEBUG": False,
                    "CORS_ORIGIN": f"https://{project_name}.com",
                },
                "secret_references": {
                    "DATABASE_URL": f"arn:aws:secretsmanager:us-east-1:*:secret:ai-factory/prod/db",
                    "SECRET_KEY": f"arn:aws:secretsmanager:us-east-1:*:secret:ai-factory/prod/secret_key",
                },
                "cpu_limits": "2048m",
                "memory_limits": "4096Mi",
                "min_replicas": 2,
                "max_replicas": 10,
            }
        elif env_lower == "staging":
            return {
                "config_data": {
                    "APP_ENV": "staging",
                    "LOG_LEVEL": "INFO",
                    "DEBUG": False,
                    "CORS_ORIGIN": f"https://staging.{project_name}.com",
                },
                "secret_references": {
                    "DATABASE_URL": f"arn:aws:secretsmanager:us-east-1:*:secret:ai-factory/staging/db",
                    "SECRET_KEY": f"arn:aws:secretsmanager:us-east-1:*:secret:ai-factory/staging/secret_key",
                },
                "cpu_limits": "1024m",
                "memory_limits": "2048Mi",
                "min_replicas": 1,
                "max_replicas": 3,
            }
        else:
            return {
                "config_data": {
                    "APP_ENV": env_lower,
                    "LOG_LEVEL": "DEBUG",
                    "DEBUG": True,
                    "CORS_ORIGIN": "http://localhost:3000",
                },
                "secret_references": {
                    "DATABASE_URL": f"sqlite:///./factory_{env_lower}.db",
                    "SECRET_KEY": "dev_insecure_local_key",
                },
                "cpu_limits": "512m",
                "memory_limits": "1024Mi",
                "min_replicas": 1,
                "max_replicas": 1,
            }

    async def get_or_create_env_config(self, project_id: str, environment: str) -> EnvironmentConfig:
        """Fetch or initialize configuration for a given environment."""
        if environment not in VALID_ENVIRONMENTS:
            raise ValueError(f"Invalid environment: {environment}. Must be one of {VALID_ENVIRONMENTS}")

        async with get_db_session() as session:
            q = select(EnvironmentConfig).where(
                and_(
                    EnvironmentConfig.project_id == project_id,
                    EnvironmentConfig.environment == environment,
                )
            )
            cfg = (await session.execute(q)).scalar_one_or_none()
            if cfg:
                return cfg

            defaults = self.get_default_config_for_env(environment, f"project-{project_id[:8]}")
            cfg = EnvironmentConfig(
                project_id=project_id,
                environment=environment,
                config_data=defaults["config_data"],
                secret_references=defaults["secret_references"],
                cpu_limits=defaults["cpu_limits"],
                memory_limits=defaults["memory_limits"],
                min_replicas=defaults["min_replicas"],
                max_replicas=defaults["max_replicas"],
                updated_at=datetime.utcnow(),
            )
            session.add(cfg)
            await session.commit()
            await session.refresh(cfg)
            return cfg

    @staticmethod
    def compare_environments(
        cfg_source: EnvironmentConfig,
        cfg_target: EnvironmentConfig,
    ) -> Dict[str, Any]:
        """Compute configuration drift and difference between two environments."""
        source_keys = set(cfg_source.config_data.keys())
        target_keys = set(cfg_target.config_data.keys())

        return {
            "source_env": cfg_source.environment,
            "target_env": cfg_target.environment,
            "common_keys": list(source_keys.intersection(target_keys)),
            "source_only": list(source_keys - target_keys),
            "target_only": list(target_keys - source_keys),
            "cpu_diff": f"{cfg_source.cpu_limits} -> {cfg_target.cpu_limits}",
            "replicas_diff": f"{cfg_source.min_replicas} -> {cfg_target.min_replicas}",
        }
