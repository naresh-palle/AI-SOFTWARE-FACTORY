"""
Tests for Phase 8: Autonomous Maintenance & Continuous Improvement Platform.
Verifies maintenance scheduling, code quality analysis, dependency management,
autonomous security remediation, bug detection & auto-fixing, regression testing,
database maintenance, performance benchmarking, technical debt tracking,
documentation synchronization, continuous improvement proposals, and FastAPI endpoints.
"""

import pytest
from datetime import datetime, timedelta
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from factory.core.database import get_db_session, init_db
from factory.models.schema import (
    Project,
    IncidentRecord,
    MaintenancePolicy,
    MaintenanceTask,
    CodeQualityReport,
    DependencyVulnerabilityRecord,
    BugReport,
    TechnicalDebtItem,
    ContinuousImprovementProposal,
    ApprovalRecord,
)
from factory.maintenance.scheduler import MaintenanceScheduler
from factory.maintenance.code_quality import CodeQualityAgent
from factory.maintenance.dependency_manager import DependencyManagementAgent
from factory.maintenance.security_remediation import SecurityRemediationAgent
from factory.maintenance.bug_fixing import BugDetectionAndFixAgent
from factory.maintenance.regression_engine import RegressionEngine
from factory.maintenance.database_maintenance import DatabaseMaintenanceAgent
from factory.maintenance.performance_optimizer import PerformanceOptimizer
from factory.maintenance.technical_debt import TechnicalDebtAgent
from factory.maintenance.documentation_manager import DocumentationMaintenanceAgent
from factory.maintenance.improvement_engine import ContinuousImprovementAgent
from factory.api.main import app


@pytest.fixture(autouse=True)
async def setup_db():
    await init_db()


async def get_or_create_test_project(session, name="Maintenance Test Project") -> Project:
    q = select(Project).where(Project.name == name)
    res = await session.execute(q)
    proj = res.scalar_one_or_none()
    if not proj:
        proj = Project(
            name=name,
            requirement_text="Automated maintenance and continuous improvement harness",
            platform_target="website",
            status="active",
        )
        session.add(proj)
        await session.commit()
        await session.refresh(proj)
    return proj


@pytest.mark.asyncio
async def test_maintenance_policy_and_scheduler():
    """Verify maintenance policy configuration and task queue management."""
    async with get_db_session() as session:
        proj = await get_or_create_test_project(session, "Scheduler Project")
        scheduler = MaintenanceScheduler()

        # 1. Configure Policy
        policy = await scheduler.configure_policy(
            db=session,
            project_id=proj.id,
            schedule="weekly",
            is_enabled=True,
            auto_remediate_level1=True,
            require_approval_level2=True,
            maintenance_window="03:00-05:00 UTC",
        )
        assert policy.schedule == "weekly"
        assert policy.is_enabled is True
        assert policy.maintenance_window == "03:00-05:00 UTC"

        # 2. Schedule Task
        task = await scheduler.schedule_task(
            db=session,
            project_id=proj.id,
            maintenance_type="code_quality",
            trigger_type="scheduled",
            priority="high",
        )
        assert task.id is not None
        assert task.status == "scheduled"
        assert task.priority == "high"
        assert 97 in task.assigned_agents  # Application Maintenance Agent

        # 3. List and get task
        tasks = await scheduler.list_tasks(session, project_id=proj.id)
        assert len(tasks) >= 1
        fetched = await scheduler.get_task(session, task.id)
        assert fetched.id == task.id


@pytest.mark.asyncio
async def test_code_quality_agent():
    """Verify code complexity, duplication, and maintainability reporting."""
    async with get_db_session() as session:
        proj = await get_or_create_test_project(session, "Quality Project")
        agent = CodeQualityAgent()

        report = await agent.analyze_project_quality(
            db=session,
            project_id=proj.id,
        )
        assert report.id is not None
        assert report.quality_score >= 80.0
        assert report.maintainability_rating == "A"
        assert report.complexity_score > 0
        assert report.test_coverage_percent > 85.0
        assert len(report.recommendations) >= 1

        latest = await agent.get_latest_report(session, proj.id)
        assert latest is not None
        assert latest.quality_score == report.quality_score


@pytest.mark.asyncio
async def test_dependency_manager_and_upgrade_branch():
    """Verify dependency auditing, CVE detection, and safe upgrade PR proposal."""
    async with get_db_session() as session:
        proj = await get_or_create_test_project(session, "Dependency Project")
        agent = DependencyManagementAgent()

        # 1. Scan dependencies
        vulns = await agent.scan_dependencies(session, proj.id)
        assert len(vulns) >= 3
        packages = [v.package_name for v in vulns]
        assert "aiohttp" in packages
        assert "urllib3" in packages

        # 2. Create upgrade branch & PR proposal (Level 2 operation)
        upgrade_res = await agent.create_upgrade_branch_and_pr(
            db=session,
            project_id=proj.id,
            package_name="aiohttp",
            target_version="3.9.4",
        )
        assert upgrade_res["status"] == "pending_approval"
        assert "maintenance/deps-aiohttp" in upgrade_res["branch_name"]
        assert upgrade_res["approval_id"] is not None

        # Verify ApprovalRecord created
        q_app = select(ApprovalRecord).where(ApprovalRecord.id == upgrade_res["approval_id"])
        approval = (await session.execute(q_app)).scalar_one_or_none()
        assert approval is not None
        assert approval.status == "pending"


@pytest.mark.asyncio
async def test_autonomous_security_remediation():
    """Verify vulnerability scanning and patch generation with Level 2 approval."""
    async with get_db_session() as session:
        proj = await get_or_create_test_project(session, "Security Project")
        agent = SecurityRemediationAgent()

        # 1. Scan findings
        findings = await agent.scan_security_findings(session, proj.id)
        assert len(findings) >= 2
        categories = [f["category"] for f in findings]
        assert "exposed_secret" in categories

        # 2. Remediate finding
        remediation_res = await agent.remediate_vulnerability(
            db=session,
            project_id=proj.id,
            finding_id="SEC-FIND-01",
            category="exposed_secret",
            file_path=".env.example",
            proposed_patch="Replace mock credentials",
        )
        assert remediation_res["status"] == "pending_approval"
        assert "maintenance/sec-sec-find-01" in remediation_res["branch_name"]
        assert remediation_res["security_tests_passed"] is True
        assert remediation_res["approval_id"] is not None


@pytest.mark.asyncio
async def test_autonomous_bug_detection_and_auto_fix():
    """Verify bug creation from incident, reproduction, patch generation, and PR creation."""
    async with get_db_session() as session:
        proj = await get_or_create_test_project(session, "BugFix Project")

        # Create parent incident
        incident = IncidentRecord(
            project_id=proj.id,
            title="Payment Service Timeout Exception",
            affected_service="payment-processor",
            severity="high",
            status="detected",
            impact_summary="Connection timeout during transaction verification",
        )
        session.add(incident)
        await session.commit()
        await session.refresh(incident)

        # 1. Create bug from incident
        bug_agent = BugDetectionAndFixAgent()
        bug = await bug_agent.detect_and_create_bug_from_incident(session, incident)
        assert bug.id is not None
        assert bug.status == "detected"
        assert len(bug.reproduction_steps) >= 2

        # 2. Auto-generate fix, execute tests, prepare PR
        fix_res = await bug_agent.auto_generate_bug_fix(session, bug.id)
        assert fix_res["status"] == "pr_created"
        assert "maintenance/bugfix" in fix_res["branch_name"]
        assert fix_res["test_evidence"]["full_regression_passed"] == 84
        assert fix_res["approval_id"] is not None


@pytest.mark.asyncio
async def test_regression_engine_impact_analysis():
    """Verify impact-based test suite mapping and flaky test isolation."""
    engine = RegressionEngine()

    # 1. Targeted regression for API file change
    api_res = await engine.execute_targeted_regression(
        changed_files=["factory/api/maintenance_routes.py"],
        project_id="reg-proj",
        run_full_suite=False,
    )
    assert api_res["is_passed"] is True
    assert "api_tests" in api_res["suites_executed"]

    # 2. Full regression suite
    full_res = await engine.execute_targeted_regression(
        changed_files=["factory/core/config.py"],
        project_id="reg-proj",
        run_full_suite=True,
    )
    assert full_res["is_passed"] is True
    assert len(full_res["suites_executed"]) >= 5
    assert full_res["total_tests"] > 80


@pytest.mark.asyncio
async def test_database_and_performance_optimization():
    """Verify database index proposals and benchmark-validated performance optimizations."""
    async with get_db_session() as session:
        proj = await get_or_create_test_project(session, "Optimization Project")

        # 1. Database maintenance
        db_agent = DatabaseMaintenanceAgent()
        health = await db_agent.analyze_database_health(session, proj.id)
        assert health["engine"].startswith("PostgreSQL")
        assert len(health["index_recommendations"]) >= 1

        index_res = await db_agent.propose_index_optimization(
            db=session,
            project_id=proj.id,
            table_name="telemetry_metric_records",
            index_name="ix_telemetry_project_timestamp",
            columns=["project_id", "timestamp"],
        )
        assert "CREATE INDEX CONCURRENTLY" in index_res["sql"]
        assert index_res["status"] == "pending_approval"
        assert index_res["is_destructive"] is False

        # 2. Performance benchmark optimization
        perf_agent = PerformanceOptimizer()
        bottlenecks = await perf_agent.analyze_performance_bottlenecks(session, proj.id)
        assert bottlenecks["bottlenecks_detected"] >= 1

        perf_res = await perf_agent.benchmark_and_propose_optimization(
            db=session,
            project_id=proj.id,
            optimization_type="slow_endpoint",
            target_component="/api/v1/projects",
        )
        assert perf_res["benchmark_evidence"]["latency_reduction_percent"] > 50.0
        assert perf_res["approval_id"] is not None


@pytest.mark.asyncio
async def test_technical_debt_and_documentation():
    """Verify technical debt backlog scoring and documentation sync with zero secret leakage."""
    async with get_db_session() as session:
        proj = await get_or_create_test_project(session, "TechDebt Project")

        # 1. Technical Debt
        debt_agent = TechnicalDebtAgent()
        summary = await debt_agent.scan_technical_debt(session, proj.id)
        assert summary["technical_debt_score"] > 80.0
        assert summary["health_grade"] in ["A", "B"]

        items = await debt_agent.list_debt_items(session, proj.id)
        assert len(items) >= 3

        # 2. Documentation Sync
        doc_agent = DocumentationMaintenanceAgent()
        doc_res = await doc_agent.audit_and_sync_docs(
            project_id=proj.id,
            commit_sha="d5036f51",
        )
        assert doc_res["status"] == "synchronized"
        assert "PASSED" in doc_res["secret_leak_check"]
        assert len(doc_res["updated_documents"]) >= 3


@pytest.mark.asyncio
async def test_continuous_improvement_proposals():
    """Verify synthesized continuous improvement proposals and deduplication."""
    async with get_db_session() as session:
        proj = await get_or_create_test_project(session, "Improvement Project")
        improvement_agent = ContinuousImprovementAgent()

        proposals = await improvement_agent.generate_proposals(session, proj.id)
        assert len(proposals) >= 3
        categories = [p.category for p in proposals]
        assert "cost" in categories
        assert "performance" in categories
        assert "architecture" in categories

        # Deduplication check
        proposals2 = await improvement_agent.generate_proposals(session, proj.id)
        assert len(proposals2) == len(proposals)


@pytest.mark.asyncio
async def test_maintenance_fastapi_endpoints():
    """Verify FastAPI maintenance REST endpoints."""
    async with get_db_session() as session:
        proj = await get_or_create_test_project(session, "API Maint Project")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Get / Configure policy
        pol_res = await client.get(f"/api/v1/maintenance/policy?project_id={proj.id}")
        assert pol_res.status_code == 200

        # Schedule task
        task_res = await client.post(
            "/api/v1/maintenance/tasks",
            json={
                "project_id": proj.id,
                "maintenance_type": "code_quality",
                "priority": "high",
            },
        )
        assert task_res.status_code == 200
        assert task_res.json()["status"] == "scheduled"

        # Code quality scan
        q_res = await client.get(f"/api/v1/maintenance/quality/latest?project_id={proj.id}")
        assert q_res.status_code == 200
        assert q_res.json()["quality_score"] > 80.0

        # Dependencies scan
        dep_res = await client.post(f"/api/v1/maintenance/dependencies/scan?project_id={proj.id}")
        assert dep_res.status_code == 200
        assert len(dep_res.json()) >= 1

        # Database health
        db_res = await client.get(f"/api/v1/maintenance/database/health?project_id={proj.id}")
        assert db_res.status_code == 200
        assert "connection_pool" in db_res.json()

        # Tech debt
        debt_res = await client.get(f"/api/v1/maintenance/tech-debt?project_id={proj.id}")
        assert debt_res.status_code == 200
        assert "technical_debt_score" in debt_res.json()

        # Improvements
        imp_res = await client.get(f"/api/v1/maintenance/improvements?project_id={proj.id}")
        assert imp_res.status_code == 200
        assert len(imp_res.json()) >= 1
