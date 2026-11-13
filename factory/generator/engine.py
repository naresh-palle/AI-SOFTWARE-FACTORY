"""
Autonomous Code Generation Engine Facade.
Coordinates the isolated workspace, Git operations, specialist workers,
and automated testing loops into a cohesive execution flow.
"""

from typing import Any, Dict, List, Optional
from factory.core.logger import logger
from factory.generator.github_service import GitHubAutomationService
from factory.generator.testing_engine import AutomatedTestingEngine, TestRunOutcome
from factory.generator.workers.api_worker import APIWorker
from factory.generator.workers.backend_worker import BackendWorker
from factory.generator.workers.database_worker import DatabaseWorker
from factory.generator.workers.frontend_worker import FrontendWorker
from factory.generator.workers.infra_worker import InfraWorker
from factory.generator.workers.mobile_worker import MobileWorker
from factory.generator.workspace import WorkspaceManager
from factory.llm.provider import BaseLLMProvider, get_llm_provider


class CodeGenerationEngine:
    """Master engine orchestrating specialist code generation workers."""

    def __init__(self, project_id: str, llm_provider: Optional[BaseLLMProvider] = None):
        self.project_id = project_id
        self.llm = llm_provider or get_llm_provider()
        self.workspace = WorkspaceManager(project_id)
        self.github = GitHubAutomationService(self.workspace)
        self.testing_engine = AutomatedTestingEngine(self.workspace, self.github, self.llm)

        # Specialist Workers
        self.frontend_worker = FrontendWorker(self.workspace, self.github, self.llm)
        self.backend_worker = BackendWorker(self.workspace, self.github, self.llm)
        self.mobile_worker = MobileWorker(self.workspace, self.github, self.llm)
        self.database_worker = DatabaseWorker(self.workspace, self.github, self.llm)
        self.api_worker = APIWorker(self.workspace, self.github, self.llm)
        self.infra_worker = InfraWorker(self.workspace, self.github, self.llm)

    def initialize_git(self) -> Dict[str, Any]:
        """Initialize local repository on main branch."""
        return self.github.init_repository()

    async def generate_database(
        self, requirement_text: str, platform_targets: List[str], tech_stack: Dict[str, Any]
    ) -> Dict[str, Any]:
        result = await self.database_worker.generate_code(requirement_text, platform_targets, tech_stack)
        # Merge feature branch into main
        self.github.merge_pull_request(result.branch_name, target_branch="main")
        return result.to_dict()

    async def generate_backend(
        self, requirement_text: str, platform_targets: List[str], tech_stack: Dict[str, Any]
    ) -> Dict[str, Any]:
        result = await self.backend_worker.generate_code(requirement_text, platform_targets, tech_stack)
        self.github.merge_pull_request(result.branch_name, target_branch="main")
        return result.to_dict()

    async def generate_frontend(
        self, requirement_text: str, platform_targets: List[str], tech_stack: Dict[str, Any]
    ) -> Dict[str, Any]:
        result = await self.frontend_worker.generate_code(requirement_text, platform_targets, tech_stack)
        self.github.merge_pull_request(result.branch_name, target_branch="main")
        return result.to_dict()

    async def generate_mobile(
        self, requirement_text: str, platform_targets: List[str], tech_stack: Dict[str, Any]
    ) -> Dict[str, Any]:
        result = await self.mobile_worker.generate_code(requirement_text, platform_targets, tech_stack)
        if result.files_created:
            self.github.merge_pull_request(result.branch_name, target_branch="main")
        return result.to_dict()

    async def generate_api_integrations(
        self, requirement_text: str, platform_targets: List[str], tech_stack: Dict[str, Any]
    ) -> Dict[str, Any]:
        result = await self.api_worker.generate_code(requirement_text, platform_targets, tech_stack)
        self.github.merge_pull_request(result.branch_name, target_branch="main")
        return result.to_dict()

    async def generate_infrastructure(
        self, requirement_text: str, platform_targets: List[str], tech_stack: Dict[str, Any]
    ) -> Dict[str, Any]:
        result = await self.infra_worker.generate_code(requirement_text, platform_targets, tech_stack)
        self.github.merge_pull_request(result.branch_name, target_branch="main")
        return result.to_dict()

    async def run_testing_and_fixing(self, max_retries: int = 3) -> TestRunOutcome:
        """Run pytest test suite in isolated workspace and fix any defects."""
        outcome = await self.testing_engine.run_testing_and_fixing_loop(max_retries=max_retries)
        await self.testing_engine.record_test_results(outcome)
        return outcome
