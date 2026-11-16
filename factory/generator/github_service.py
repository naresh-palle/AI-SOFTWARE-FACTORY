"""
GitHub and Git Automation Service.
Provides local repository initialization, isolated branch creation, conventional commits,
pull request simulations, conflict-free merging, and release tagging.
"""

import json
import re
from typing import Any, Callable, Dict, List, Optional

from factory.core.config import settings
from factory.core.logger import logger
from factory.generator.security_scan import find_blocking_secrets
from factory.generator.workspace import WorkspaceManager


class GitHubAutomationService:
    """Manages Git lifecycle and optional GitHub remote integration."""

    def __init__(self, workspace: WorkspaceManager):
        self.workspace = workspace
        self.project_id = workspace.project_id
        self.github_token = getattr(settings, "GITHUB_TOKEN", None)

    def init_repository(self) -> Dict[str, Any]:
        """Initialize a local git repository on branch main and make initial commit."""
        if (self.workspace.workspace_path / ".git").is_dir():
            rc_h, sha, _ = self.workspace.run_command(["git", "rev-parse", "HEAD"])
            rc_b, br, _ = self.workspace.run_command(["git", "branch", "--show-current"])
            return {
                "initialized": True,
                "branch": br.strip() or "main",
                "commit": sha.strip() or "unknown",
                "message": "Repository already initialized",
            }

        # 1. git init -b main
        rc, out, err = self.workspace.run_command(["git", "init", "-b", "main"])
        if rc != 0:
            raise RuntimeError(f"Failed to initialize git repository: {err or out}")

        # Configure local git author identity
        self.workspace.run_command(["git", "config", "user.name", "AI Software Factory"])
        self.workspace.run_command(["git", "config", "user.email", "agent@software-factory.ai"])

        # Write standard .gitignore if none exists
        if not self.workspace.exists(".gitignore"):
            gitignore_content = (
                "node_modules/\n"
                ".next/\n"
                "out/\n"
                "build/\n"
                "dist/\n"
                "__pycache__/\n"
                "*.pyc\n"
                ".venv/\n"
                "venv/\n"
                ".env\n"
                ".env.local\n"
                ".DS_Store\n"
                "coverage/\n"
                ".pytest_cache/\n"
                ".worktrees/\n"
                ".sandbox-deps/\n"
            )
            self.workspace.write_file(".gitignore", gitignore_content)

        # Write standard README.md if none exists
        if not self.workspace.exists("README.md"):
            readme_content = (
                f"# Project {self.project_id}\n\n"
                "Autonomous AI Software Factory Delivery Repository.\n"
            )
            self.workspace.write_file("README.md", readme_content)

        # Stage and commit
        self.workspace.run_command(["git", "add", "-A"])
        rc_c, out_c, err_c = self.workspace.run_command(
            ["git", "commit", "-m", "chore: initial repository scaffold by Master Orchestrator"]
        )
        
        # Get HEAD hash
        rc_h, sha, _ = self.workspace.run_command(["git", "rev-parse", "HEAD"])
        commit_hash = sha.strip() if rc_h == 0 else "unknown"

        logger.info(f"Initialized Git repo for {self.project_id} (commit: {commit_hash[:8]})")
        return {
            "initialized": True,
            "branch": "main",
            "commit": commit_hash,
            "message": "chore: initial repository scaffold",
        }

    def create_branch(self, branch_name: str) -> str:
        """Create an isolated git worktree so this agent cannot overwrite another branch."""
        if not (self.workspace.workspace_path / ".git").is_dir():
            self.init_repository()

        worktree = self._worktree_path(branch_name)
        worktree.parent.mkdir(parents=True, exist_ok=True)
        if not worktree.exists():
            rc_exists, _, _ = self._git(["rev-parse", "--verify", branch_name])
            if rc_exists == 0:
                rc, out, err = self._git(["worktree", "add", str(worktree), branch_name])
            else:
                rc, out, err = self._git(["worktree", "add", "-b", branch_name, str(worktree), "main"])
            if rc != 0:
                raise RuntimeError(f"Failed to create worktree for {branch_name}: {err or out}")
        self.workspace.activate(worktree)
        logger.info(f"Workspace [{self.project_id}] opened worktree {worktree.name} on {branch_name}")
        return branch_name

    def switch_branch(self, branch_name: str) -> None:
        """Return file operations to the main worktree and check out a branch there."""
        self.workspace.activate(self.workspace.workspace_path)
        rc, out, err = self._git(["checkout", branch_name])
        if rc != 0:
            raise RuntimeError(f"Failed to checkout branch {branch_name}: {err or out}")

    def commit_changes(self, message: str, stage_all: bool = True) -> Optional[str]:
        """Stage files and create a conventional git commit. Returns commit hash or None if clean."""
        blocked = find_blocking_secrets(self.workspace)
        if blocked:
            names = ", ".join(item["path"] for item in blocked)
            raise RuntimeError(f"Refusing to commit blocked files: {names}")

        if stage_all:
            self._git_here(["add", "-A"])

        rc_s, status, _ = self._git_here(["status", "--porcelain"])
        if not status.strip():
            logger.debug(f"Workspace [{self.project_id}] working tree clean, nothing to commit.")
            rc_h, sha, _ = self._git_here(["rev-parse", "HEAD"])
            return sha.strip() if rc_h == 0 else None

        rc, out, err = self._git_here(["commit", "-m", message])
        if rc != 0:
            raise RuntimeError(f"Git commit failed: {err or out}")

        rc_h, sha, _ = self._git_here(["rev-parse", "HEAD"])
        commit_sha = sha.strip()
        logger.info(f"Workspace [{self.project_id}] committed: '{message}' ({commit_sha[:8]})")
        return commit_sha

    def create_pull_request(
        self,
        branch_name: str,
        target_branch: str = "main",
        title: str = "",
        description: str = "",
    ) -> Dict[str, Any]:
        """
        Create a Pull Request object. In local mode, compares the diff against target branch.
        """
        # Inspect diff against target
        rc, diff_stat, _ = self.workspace.run_command(
            ["git", "diff", "--stat", f"{target_branch}...{branch_name}"]
        )
        
        pr_title = title or f"PR: Merge {branch_name} into {target_branch}"
        pr_id = f"pr-{branch_name}-{target_branch}"
        
        return {
            "pr_id": pr_id,
            "title": pr_title,
            "source_branch": branch_name,
            "target_branch": target_branch,
            "diff_summary": diff_stat.strip(),
            "status": "open",
            "created_at": "now",
        }

    def merge_pull_request(
        self,
        branch_name: str,
        target_branch: str = "main",
        merge_commit_message: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Safely checkout target branch and merge the feature branch with --no-ff.
        """
        self.switch_branch(target_branch)

        msg = merge_commit_message or f"merge: Pull request '{branch_name}' into {target_branch}"
        rc, out, err = self._git(["merge", "--no-ff", branch_name, "-m", msg])
        if rc != 0:
            logger.error(f"Merge conflict merging {branch_name} into {target_branch}")
            self._git(["merge", "--abort"])
            raise RuntimeError(f"Git merge failed for {branch_name}")

        self._remove_worktree(branch_name)
        rc_h, sha, _ = self._git(["rev-parse", "HEAD"])
        merge_sha = sha.strip()
        self._record_pull_request(
            {
                "pr_id": f"pr-{branch_name}-{target_branch}",
                "title": f"Merge {branch_name} into {target_branch}",
                "source_branch": branch_name,
                "target_branch": target_branch,
                "status": "merged",
                "merge_commit": merge_sha,
            }
        )

        logger.info(f"Merged branch {branch_name} into {target_branch} (commit: {merge_sha[:8]})")
        return {
            "merged": True,
            "merge_commit": merge_sha,
            "target_branch": target_branch,
            "source_branch": branch_name,
        }

    def publish_repository(
        self,
        repo_name: str,
        poster: Optional[Callable[..., Dict[str, Any]]] = None,
        push: bool = True,
    ) -> Dict[str, Any]:
        """Create a GitHub repository when publication is explicitly enabled."""
        token = settings.GITHUB_TOKEN or ""
        if not token:
            return {"remote_created": False, "reason": "GITHUB_TOKEN is not configured", "repo_url": ""}
        blocked = find_blocking_secrets(self.workspace)
        if blocked:
            return {
                "remote_created": False,
                "reason": "secret scan blocked publication",
                "repo_url": "",
                "blocked_files": [item["path"] for item in blocked],
            }
        safe_name = re.sub(r"[^A-Za-z0-9_.-]", "-", repo_name)[:80]
        payload = {"name": safe_name, "private": True, "auto_init": False}
        headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
        try:
            if poster is not None:
                body = poster("https://api.github.com/user/repos", headers=headers, json=payload)
            else:
                import httpx
                response = httpx.post("https://api.github.com/user/repos", headers=headers, json=payload, timeout=30.0)
                if response.status_code >= 300:
                    return {"remote_created": False, "reason": f"GitHub returned HTTP {response.status_code}", "repo_url": ""}
                body = response.json()
        except Exception:
            logger.warning("GitHub repository creation failed")
            return {"remote_created": False, "reason": "GitHub request failed", "repo_url": ""}

        repo_url = str(body.get("html_url") or "")
        if not repo_url.startswith("https://github.com/"):
            return {"remote_created": False, "reason": "GitHub response did not include a repository URL", "repo_url": ""}
        if push:
            self._git(["remote", "remove", "origin"])
            rc, _, _ = self._git(["remote", "add", "origin", f"{repo_url}.git"])
            if rc != 0:
                return {"remote_created": False, "reason": "Could not add the git remote", "repo_url": repo_url, "pushed": False}
            pushed = self._push_with_askpass(token)
            if not pushed:
                return {"remote_created": True, "reason": "Repository created but push failed", "repo_url": repo_url, "repo_name": safe_name, "pushed": False}
        return {"remote_created": True, "reason": "GitHub repository created", "repo_url": repo_url, "repo_name": safe_name, "pushed": push}

    def _push_with_askpass(self, token: str) -> bool:
        """Push main without placing the token on the logged command line."""
        askpass = self.workspace.workspace_path / ".git" / "factory-askpass.sh"
        askpass.write_text("#!/bin/sh\nprintf '%s\\n' \"$FACTORY_GIT_TOKEN\"\n", encoding="utf-8")
        askpass.chmod(0o700)
        try:
            rc, _, _ = self.workspace.run_command(
                ["git", "push", "-u", "origin", "main"],
                use_main=True,
                timeout_seconds=60,
                env={
                    "GIT_ASKPASS": str(askpass),
                    "GIT_TERMINAL_PROMPT": "0",
                    "FACTORY_GIT_TOKEN": token,
                },
            )
        finally:
            askpass.unlink(missing_ok=True)
        return rc == 0

    def _git(self, args: List[str]):
        return self.workspace.run_command(["git", *args], use_main=True)

    def _git_here(self, args: List[str]):
        return self.workspace.run_command(["git", *args])

    def _worktree_path(self, branch_name: str):
        safe = re.sub(r"[^A-Za-z0-9_.-]", "-", branch_name)
        return self.workspace.workspace_path / ".worktrees" / safe

    def _remove_worktree(self, branch_name: str) -> None:
        worktree = self._worktree_path(branch_name)
        if worktree.exists():
            self._git(["worktree", "remove", "--force", str(worktree)])

    def _record_pull_request(self, record: Dict[str, Any]) -> None:
        path = self.workspace.workspace_path / "pull_requests.json"
        current: List[Dict[str, Any]] = []
        if path.exists():
            current = json.loads(path.read_text(encoding="utf-8"))
        current.append(record)
        path.write_text(json.dumps(current, indent=2) + "\n", encoding="utf-8")

    def tag_release(self, tag_name: str, message: str) -> str:
        """Create an annotated git release tag."""
        rc, out, err = self.workspace.run_command(["git", "tag", "-a", tag_name, "-m", message])
        if rc != 0:
            raise RuntimeError(f"Failed to create tag {tag_name}: {err or out}")
        return tag_name

    def get_commit_history(self, limit: int = 15) -> List[Dict[str, str]]:
        """Return git log entries."""
        rc, out, _ = self.workspace.run_command(
            ["git", "log", f"-n{limit}", "--pretty=format:%H|%an|%s|%cI"]
        )
        if rc != 0 or not out.strip():
            return []

        commits = []
        for line in out.strip().split("\n"):
            parts = line.split("|")
            if len(parts) >= 4:
                commits.append({
                    "hash": parts[0],
                    "author": parts[1],
                    "subject": parts[2],
                    "date": parts[3],
                })
        return commits
