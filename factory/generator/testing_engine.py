"""
Automated Testing and Bug-Fixing Engine.
Runs real pytest/build validations in isolated project workspaces, captures failures,
and executes an autonomous bug-fixing loop (max 3 retries) with defect logging.
"""

import json
import re
import time
from typing import Any, Dict, List, Optional, Tuple

from factory.core.database import get_db_session
from factory.core.logger import logger
from factory.generator.github_service import GitHubAutomationService
from factory.generator.repairs import apply_repair
from factory.generator.sandbox import DockerExecutionSandbox, SandboxResult
from factory.generator.workspace import WorkspaceManager
from factory.llm.provider import BaseLLMProvider, get_llm_provider
from factory.models.schema import TestingResult


class TestRunOutcome:
    def __init__(
        self,
        total: int,
        passed: int,
        failed: int,
        status: str,  # "passed", "failed", "fixed"
        output: str,
        retries: int = 0,
        defects_fixed: Optional[List[str]] = None,
    ):
        self.total = total
        self.passed = passed
        self.failed = failed
        self.status = status
        self.output = output
        self.retries = retries
        self.defects_fixed = defects_fixed or []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total": self.total,
            "passed": self.passed,
            "failed": self.failed,
            "status": self.status,
            "retries": self.retries,
            "defects_fixed": self.defects_fixed,
            "output_summary": self.output[-1000:] if len(self.output) > 1000 else self.output,
        }


class AutomatedTestingEngine:
    """Executes test suites and manages automated bug-fixing cycles."""

    def __init__(
        self,
        workspace: WorkspaceManager,
        github_service: GitHubAutomationService,
        llm_provider: Optional[BaseLLMProvider] = None,
    ):
        self.workspace = workspace
        self.github = github_service
        self.llm = llm_provider or get_llm_provider()
        self.sandbox = DockerExecutionSandbox()

    def _execute_pytest(self) -> Tuple[int, str, str]:
        """Run pytest in the Docker sandbox. Generated code is not started on the host."""
        result: SandboxResult = self.sandbox.run_backend_tests(self.workspace)
        return result.returncode, result.output, result.status

    def _parse_pytest_output(self, output: str) -> Tuple[int, int, int]:
        """Extract total, passed, and failed test counts from pytest stdout."""
        passed = 0
        failed = 0

        # Look for summary lines like: '=== 3 passed in 0.25s ===' or '=== 1 failed, 2 passed in 0.5s ==='
        pass_match = re.search(r"(\d+)\s+passed", output)
        if pass_match:
            passed = int(pass_match.group(1))

        fail_match = re.search(r"(\d+)\s+failed", output)
        if fail_match:
            failed = int(fail_match.group(1))

        total = passed + failed
        return total, passed, failed

    async def _attempt_bug_fix(self, failure_trace: str, attempt: int) -> Optional[str]:
        """Apply one known repair on an isolated branch. Return None when no edit is safe."""
        logger.warning(f"TestingEngine: repair attempt {attempt} for project {self.workspace.project_id}")
        bugfix_branch = f"bugfix/test-failures-attempt-{attempt}"
        self.github.create_branch(bugfix_branch)
        repair = apply_repair(self.workspace, failure_trace)
        if repair is None:
            self.workspace.activate(self.workspace.workspace_path)
            self.github._remove_worktree(bugfix_branch)
            return None
        self.github.commit_changes(f"fix: {repair}")
        self.github.merge_pull_request(bugfix_branch)
        return repair

    async def run_testing_and_fixing_loop(
        self,
        max_retries: int = 3,
    ) -> TestRunOutcome:
        """
        Execute backend and integration tests. If tests fail, run bug-fixing loop up to max_retries.
        """
        logger.info(f"TestingEngine: Initiating test suite for project {self.workspace.project_id}")
        attempt = 0
        defects_fixed: List[str] = []

        while attempt <= max_retries:
            rc, output, sandbox_status = self._execute_pytest()
            total, passed, failed = self._parse_pytest_output(output)

            if sandbox_status in {"unavailable", "timed_out", "rejected"}:
                return TestRunOutcome(
                    total=0,
                    passed=0,
                    failed=0,
                    status=sandbox_status,
                    output=output,
                    retries=attempt,
                    defects_fixed=defects_fixed,
                )

            if total == 0 and rc == 0:
                logger.info("TestingEngine: No formal tests found in workspace; status=not_run.")
                return TestRunOutcome(total=0, passed=0, failed=0, status="not_run", output=output)

            if failed == 0 and rc == 0:
                status = "fixed" if attempt > 0 else "passed"
                logger.info(f"TestingEngine: Tests succeeded on attempt {attempt}: {passed}/{total} passed.")
                return TestRunOutcome(
                    total=total,
                    passed=passed,
                    failed=failed,
                    status=status,
                    output=output,
                    retries=attempt,
                    defects_fixed=defects_fixed,
                )

            logger.warning(f"TestingEngine: Tests failed on attempt {attempt}: {failed}/{total} failed (exit {rc}).")
            if attempt >= max_retries:
                return TestRunOutcome(
                    total=total,
                    passed=passed,
                    failed=failed,
                    status="failed",
                    output=output,
                    retries=attempt,
                    defects_fixed=defects_fixed,
                )

            attempt += 1
            repair = await self._attempt_bug_fix(output, attempt)
            if repair is None:
                return TestRunOutcome(
                    total=total,
                    passed=passed,
                    failed=failed,
                    status="failed",
                    output=output,
                    retries=attempt,
                    defects_fixed=defects_fixed,
                )
            defects_fixed.append(repair)

        return TestRunOutcome(
            total=total,
            passed=passed,
            failed=failed,
            status="failed",
            output=output,
            retries=attempt,
            defects_fixed=defects_fixed,
        )

    async def record_test_results(self, outcome: TestRunOutcome) -> str:
        """Save test_report.json to workspace and record entry in DB testing_results."""
        report_data = {
            "project_id": self.workspace.project_id,
            "suite": "pytest_and_integration",
            "total": outcome.total,
            "passed": outcome.passed,
            "failed": outcome.failed,
            "total_tests": outcome.total,
            "passed_tests": outcome.passed,
            "failed_tests": outcome.failed,
            "status": outcome.status,
            "evidence": outcome.output or "Automated test suite report.",
            "retries": outcome.retries,
            "defects_remediated": outcome.defects_fixed,
            "timestamp": time.time(),
        }
        report_file, sha = self.workspace.write_file("test_report.json", json.dumps(report_data, indent=2) + "\n")

        # Record in database
        async with get_db_session() as session:
            tr = TestingResult(
                project_id=self.workspace.project_id,
                test_suite="automated_qa",
                total_tests=outcome.total,
                passed_tests=outcome.passed,
                failed_tests=outcome.failed,
                evidence_path=str(report_file),
                details=report_data,
            )
            session.add(tr)

        logger.info(f"Recorded test report in DB and workspace: {report_file.name}")
        return str(report_file)
