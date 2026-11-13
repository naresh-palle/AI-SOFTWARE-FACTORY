"""Isolate tests from the developer database, workspace, and provider settings."""

import os
import tempfile
from pathlib import Path

_root = Path(tempfile.mkdtemp(prefix="ai-factory-tests-"))
(_root / "projects").mkdir()
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{(_root / 'test.db').as_posix()}"
os.environ["PROJECTS_STORAGE_DIR"] = str(_root / "projects")
os.environ["ENVIRONMENT"] = "testing"
os.environ["FACTORY_API_TOKEN"] = ""
os.environ["DEFAULT_LLM_PROVIDER"] = "mock"
os.environ["DEBUG"] = "false"
