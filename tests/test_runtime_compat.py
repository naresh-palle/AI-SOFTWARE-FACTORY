"""Runtime packaging checks for Docker, dependencies, and the LLM gateway."""

from pathlib import Path

import pytest

from factory.llm.provider import get_llm_provider

ROOT = Path(__file__).resolve().parents[1]


def test_dockerignore_keeps_secrets_and_local_data_out_of_the_image():
    text = (ROOT / ".dockerignore").read_text(encoding="utf-8")
    for entry in (".env", "*.db", "workspace_projects", ".venv"):
        assert entry in text.splitlines()


def test_compose_uses_the_postgres_driver_and_host_env():
    text = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")
    assert "postgresql+asyncpg://${POSTGRES_USER:-postgres}:${POSTGRES_PASSWORD:-postgres}@" in text
    assert "postgresql+asyncpg://postgres:postgres@" not in text
    assert "host.docker.internal" in text
    requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8")
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert "asyncpg" in requirements
    assert "asyncpg" in pyproject


def test_default_ollama_url_is_not_a_docker_bridge_address():
    source = (ROOT / "factory" / "core" / "config.py").read_text(encoding="utf-8")
    example = (ROOT / ".env.example").read_text(encoding="utf-8")
    assert "172.18.0.2" not in source
    assert "172.18.0.2" not in example
    assert "127.0.0.1:11434" in source
    assert "127.0.0.1:11434" in example


def test_unconfigured_llm_provider_is_rejected():
    with pytest.raises(ValueError):
        get_llm_provider("gemini")
