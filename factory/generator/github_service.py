"""
GitHub and Git Automation Service.
Provides local repository initialization, isolated branch creation, conventional commits,
pull request simulations, conflict-free merging, and release tagging.
"""

from typing import Any, Dict, List, Optional
from factory.core.config import settings
from factory.core.logger import logger
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
        """Create and checkout an isolated branch."""
        if not (self.workspace.workspace_path / ".git").is_dir():
            self.init_repository()

        # Check current branch
        rc_b, current, _ = self.workspace.run_command(["git", "branch", "--show-current"])
        current_branch = current.strip()

        # If branch already exists, switch to it, otherwise create with -b
        rc_chk, _, _ = self.workspace.run_command(["git", "rev-parse", "--verify", branch_name])
        if rc_chk == 0:
            rc, out, err = self.workspace.run_command(["git", "checkout", branch_name])
        else:
            rc, out, err = self.workspace.run_command(["git", "checkout", "-b", branch_name])

        if rc != 0:
            raise RuntimeError(f"Failed to create/checkout branch {branch_name}: {err or out}")
        
        logger.info(f"Workspace [{self.project_id}] switched from {current_branch} to branch {branch_name}")
        return branch_name

    def switch_branch(self, branch_name: str) -> None:
        """Switch to an existing branch."""
        rc, out, err = self.workspace.run_command(["git", "checkout", branch_name])
        if rc != 0:
            raise RuntimeError(f"Failed to checkout branch {branch_name}: {err or out}")

    def commit_changes(self, message: str, stage_all: bool = True) -> Optional[str]:
        """Stage files and create a conventional git commit. Returns commit hash or None if clean."""
        if stage_all:
            self.workspace.run_command(["git", "add", "-A"])

        rc_s, status, _ = self.workspace.run_command(["git", "status", "--porcelain"])
        if not status.strip():
            logger.debug(f"Workspace [{self.project_id}] working tree clean, nothing to commit.")
            rc_h, sha, _ = self.workspace.run_command(["git", "rev-parse", "HEAD"])
            return sha.strip() if rc_h == 0 else None

        rc, out, err = self.workspace.run_command(["git", "commit", "-m", message])
        if rc != 0:
            raise RuntimeError(f"Git commit failed: {err or out}")

        rc_h, sha, _ = self.workspace.run_command(["git", "rev-parse", "HEAD"])
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
        # Switch to target branch
        self.switch_branch(target_branch)

        msg = merge_commit_message or f"merge: Pull request '{branch_name}' into {target_branch}"
        rc, out, err = self.workspace.run_command(
            ["git", "merge", "--no-ff", branch_name, "-m", msg]
        )
        if rc != 0:
            logger.error(f"Merge conflict or error merging {branch_name} into {target_branch}: {err or out}")
            # Abort merge if stuck
            self.workspace.run_command(["git", "merge", "--abort"])
            raise RuntimeError(f"Git merge failed: {err or out}")

        rc_h, sha, _ = self.workspace.run_command(["git", "rev-parse", "HEAD"])
        merge_sha = sha.strip()

        logger.info(f"Merged branch {branch_name} into {target_branch} (commit: {merge_sha[:8]})")
        return {
            "merged": True,
            "merge_commit": merge_sha,
            "target_branch": target_branch,
            "source_branch": branch_name,
        }

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
