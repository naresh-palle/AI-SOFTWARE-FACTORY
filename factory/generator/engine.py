"""
Autonomous Code Generation Engine Facade.
Coordinates the isolated workspace, Git operations, specialist workers,
and automated testing loops into a cohesive execution flow.
"""

import json
import os
from typing import Any, Dict, List, Optional

from factory.core.config import settings
from factory.core.database import get_db_session
from factory.core.logger import logger
from factory.generator.github_service import GitHubAutomationService
from factory.generator.security_scan import scan_workspace
from factory.models.schema import SecurityFinding
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

    def initialize_git(self, publish: bool = False) -> Dict[str, Any]:
        """Initialize the project repository. GitHub publication stays off unless requested."""
        info = self.github.init_repository()
        info["remote_created"] = False
        info["repo_url"] = f"local://{self.project_id}"
        info["repo_name"] = f"local-{self.project_id[:8]}"
        if publish and github_publication_enabled():
            published = self.github.publish_repository(info["repo_name"], push=True)
            info["remote_created"] = bool(published.get("remote_created"))
            info["publish_reason"] = published.get("reason", "")
            if str(published.get("repo_url", "")).startswith("https://github.com/"):
                info["repo_url"] = published["repo_url"]
                info["repo_name"] = published.get("repo_name") or info["repo_name"]
        return info

    def write_development_plan(
        self,
        requirement_text: str,
        platform_targets: List[str],
        tech_stack: Dict[str, Any],
        selected_agents: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Record the technologies, agents, and worker order for this requirement."""
        plan = {
            "requirement": requirement_text,
            "platforms": platform_targets,
            "technology": tech_stack,
            "selected_agents": selected_agents or [],
            "workers": [
                "database",
                "backend",
                "frontend",
                "mobile",
                "api_integration",
                "infrastructure",
            ],
            "execution_order": [
                "analysis",
                "architecture",
                "task_generation",
                "github_repository",
                "code_generation",
                "dependency_installation",
                "build",
                "unit_testing",
                "integration_testing",
                "security_scanning",
                "bug_fixing",
                "regression_testing",
                "deployment_preparation",
            ],
        }
        path = self.workspace.workspace_path / "03_development_plan.json"
        path.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
        return plan

    async def run_security_scan(self) -> List[Dict[str, Any]]:
        """Scan generated files and store findings. The scan does not execute the files."""
        findings = scan_workspace(self.workspace, self.workspace.workspace_path)
        report = self.workspace.workspace_path / "security_report.json"
        report.write_text(json.dumps(findings, indent=2) + "\n", encoding="utf-8")
        async with get_db_session() as session:
            for item in findings:
                session.add(
                    SecurityFinding(
                        project_id=self.project_id,
                        severity=str(item["severity"]),
                        title=str(item["title"])[:255],
                        description=f"{item['rule']} at {item['path']}",
                        tool="factory_scanner",
                        remediation_status="open",
                    )
                )
        return findings

    def prepare_deployment(self) -> Dict[str, Any]:
        """Write a deployment plan. This does not apply infrastructure or deploy."""
        plan = {
            "executed": False,
            "status": "prepared",
            "project_id": self.project_id,
            "requires_approval": [
                "paid_service",
                "external_account_change",
                "production_infrastructure",
                "production_deploy",
            ],
            "rejected_without_approval": [
                "terraform apply",
                "kubectl apply",
                "kubectl delete",
                "helm upgrade",
                "helm install",
            ],
        }
        path = self.workspace.workspace_path / "deployment_plan.json"
        path.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
        return plan

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


def github_publication_enabled() -> bool:
    """Publication requires both a token and an explicit operator flag."""
    return bool(settings.GITHUB_TOKEN) and os.getenv("FACTORY_ENABLE_GITHUB_PUSH") == "true"
