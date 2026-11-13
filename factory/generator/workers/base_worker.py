"""
Base Code Generation Worker.
Provides unified structure for branch creation, file generation, and commit tracking.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from factory.core.logger import logger
from factory.generator.github_service import GitHubAutomationService
from factory.generator.workspace import WorkspaceManager
from factory.llm.provider import BaseLLMProvider, get_llm_provider


class WorkerResult:
    def __init__(
        self,
        worker_name: str,
        branch_name: str,
        files_created: List[str],
        commit_sha: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.worker_name = worker_name
        self.branch_name = branch_name
        self.files_created = files_created
        self.commit_sha = commit_sha
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "worker_name": self.worker_name,
            "branch_name": self.branch_name,
            "files_created": self.files_created,
            "commit_sha": self.commit_sha,
            "metadata": self.metadata,
        }


class BaseWorker(ABC):
    """Abstract base class for all specialist code generation workers."""

    def __init__(
        self,
        workspace: WorkspaceManager,
        github_service: GitHubAutomationService,
        llm_provider: Optional[BaseLLMProvider] = None,
    ):
        self.workspace = workspace
        self.github = github_service
        self.llm = llm_provider or get_llm_provider()

    @property
    @abstractmethod
    def worker_name(self) -> str:
        """Name of the worker (e.g. frontend, backend, database)."""
        pass

    @property
    @abstractmethod
    def default_branch(self) -> str:
        """Feature branch name."""
        pass

    @abstractmethod
    async def generate_code(
        self,
        requirement_text: str,
        platform_targets: List[str],
        tech_stack: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> WorkerResult:
        """Generate files, commit to feature branch, and return result."""
        pass
