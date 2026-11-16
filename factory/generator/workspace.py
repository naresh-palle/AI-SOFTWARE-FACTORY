"""
Isolated Workspace Manager.
Handles path isolation, file access, directory scaffolding, and sandboxed process execution.
"""

import hashlib
import os
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from factory.core.config import settings
from factory.core.logger import logger
from factory.core.security import hash_string


class WorkspaceManager:
    """Manages isolated disk directories and execution sandboxes for software projects."""

    def __init__(self, project_id: str):
        if not project_id or project_id in {".", ".."} or project_id != Path(project_id).name:
            raise ValueError(f"Invalid project_id: {project_id}")
        self.project_id = project_id
        self.root_storage = settings.PROJECTS_STORAGE_DIR.resolve()
        self.workspace_path = (self.root_storage / project_id).resolve()

        if self.workspace_path == self.root_storage or self.root_storage not in self.workspace_path.parents:
            raise ValueError(f"Path traversal detected in project_id: {project_id}")

        self.workspace_path.mkdir(parents=True, exist_ok=True)
        self.active_root = self.workspace_path

    def activate(self, root: Path) -> None:
        """Point file writes at a worktree that stays inside this project."""
        resolved = root.resolve()
        if resolved != self.workspace_path and self.workspace_path not in resolved.parents:
            raise ValueError("Active root escapes the project workspace")
        self.active_root = resolved

    def resolve_path(self, relative_path: str) -> Path:
        """Resolve a relative path securely inside the active worktree."""
        clean_rel = relative_path.lstrip("/\\")
        target = (self.active_root / clean_rel).resolve()
        if target != self.active_root and self.active_root not in target.parents:
            raise ValueError(f"Access denied: path traversal attempt outside workspace: {relative_path}")
        if target != self.workspace_path and self.workspace_path not in target.parents:
            raise ValueError(f"Access denied: path traversal attempt outside workspace: {relative_path}")
        return target

    def write_file(self, relative_path: str, content: str) -> Tuple[Path, str]:
        """Write content to a file inside the workspace and return (Path, sha256)."""
        target = self.resolve_path(relative_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        encoded = content.encode("utf-8")
        target.write_bytes(encoded)
        sha256 = hash_string(content)
        logger.debug(f"Workspace [{self.project_id}]: wrote {relative_path} ({len(encoded)} bytes, sha={sha256[:8]})")
        return target, sha256

    def read_file(self, relative_path: str) -> str:
        """Read text from a file inside the workspace."""
        target = self.resolve_path(relative_path)
        if not target.exists():
            raise FileNotFoundError(f"File not found: {relative_path}")
        return target.read_text(encoding="utf-8")

    def exists(self, relative_path: str) -> bool:
        """Check if file or directory exists."""
        target = self.resolve_path(relative_path)
        return target.exists()

    def list_files(self, sub_dir: str = "", recursive: bool = True) -> List[str]:
        """List files in workspace relative to workspace root."""
        base = self.resolve_path(sub_dir) if sub_dir else self.workspace_path
        if not base.exists():
            return []
        
        skip = {".git", ".worktrees", ".sandbox-deps", "node_modules", ".next", "__pycache__"}
        results: List[str] = []
        if recursive:
            for item in base.rglob("*"):
                if not item.is_file() or any(part in skip or part.startswith(".git") for part in item.parts):
                    continue
                rel = item.relative_to(self.workspace_path)
                results.append(str(rel).replace("\\", "/"))
        else:
            for item in base.iterdir():
                if item.is_file():
                    rel = item.relative_to(self.workspace_path)
                    results.append(str(rel).replace("\\", "/"))
        return sorted(results)

    def run_command(
        self,
        command: List[str],
        cwd_relative: str = "",
        env: Optional[Dict[str, str]] = None,
        timeout_seconds: int = 60,
        use_main: bool = False,
    ) -> Tuple[int, str, str]:
        """
        Execute a command in the isolated workspace with timeout and output capture.
        Returns (returncode, stdout, stderr).
        """
        if cwd_relative:
            cwd = self.resolve_path(cwd_relative)
        elif use_main:
            cwd = self.workspace_path
        else:
            cwd = self.active_root
        safe_keys = ("PATH", "HOME", "USER", "LANG", "LC_ALL", "TMPDIR", "TEMP", "TMP", "SYSTEMROOT", "PATHEXT")
        merged_env = {key: os.environ[key] for key in safe_keys if key in os.environ}
        if env:
            merged_env.update(env)

        # Ensure isolated execution environment
        merged_env["CI"] = "true"
        merged_env["PROJECT_ID"] = self.project_id
        merged_env["WORKSPACE_DIR"] = str(self.workspace_path)

        logger.info(f"Workspace [{self.project_id}] running command: {' '.join(command)} in {cwd}")
        try:
            proc = subprocess.run(
                command,
                cwd=cwd,
                env=merged_env,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                check=False,
            )
            return proc.returncode, proc.stdout, proc.stderr
        except subprocess.TimeoutExpired as exc:
            logger.error(f"Workspace command timed out after {timeout_seconds}s: {' '.join(command)}")
            stdout = exc.stdout or ""
            if isinstance(stdout, bytes):
                stdout = stdout.decode("utf-8", errors="replace")
            stderr = f"Command timed out after {timeout_seconds} seconds"
            return 124, stdout, stderr
        except Exception as exc:
            logger.error(f"Failed to execute command {' '.join(command)}: {exc}")
            return 1, "", str(exc)

    def clean(self) -> None:
        """Remove all files inside workspace while preserving the workspace directory itself."""
        for item in self.workspace_path.iterdir():
            if item.is_dir():
                shutil.rmtree(item, ignore_errors=True)
            else:
                item.unlink(missing_ok=True)
