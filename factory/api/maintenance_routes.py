"""
FastAPI Routes for Autonomous Maintenance & Continuous Improvement Platform.
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from factory.core.database import get_db_session
from factory.core.logger import logger
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

router = APIRouter(prefix="/maintenance", tags=["Maintenance & Continuous Improvement"])

# Singletons
scheduler = MaintenanceScheduler()
quality_agent = CodeQualityAgent()
dep_agent = DependencyManagementAgent()
security_agent = SecurityRemediationAgent()
bug_agent = BugDetectionAndFixAgent()
regression_engine = RegressionEngine()
db_agent = DatabaseMaintenanceAgent()
perf_optimizer = PerformanceOptimizer()
debt_agent = TechnicalDebtAgent()
doc_agent = DocumentationMaintenanceAgent()
improvement_agent = ContinuousImprovementAgent()


# Request Schemas
class ConfigurePolicyRequest(BaseModel):
    project_id: str
    schedule: str = "daily"
    is_enabled: bool = True
    auto_remediate_level1: bool = True
    require_approval_level2: bool = True
    maintenance_window: str = "02:00-04:00 UTC"


class ScheduleTaskRequest(BaseModel):
    project_id: str
    maintenance_type: str
    trigger_type: str = "on_demand"
    priority: str = "medium"
    assigned_agents: Optional[List[int]] = None


class QualityScanRequest(BaseModel):
    project_id: str
    task_id: Optional[str] = None


class DependencyUpgradeRequest(BaseModel):
    project_id: str
    package_name: str
    target_version: str


class SecurityRemediationRequest(BaseModel):
    project_id: str
    finding_id: str
    category: str
    file_path: str
    proposed_patch: str = ""


class CreateBugFromIncidentRequest(BaseModel):
    incident_id: str


class RunRegressionRequest(BaseModel):
    project_id: str
    changed_files: List[str] = Field(default_factory=list)
    run_full_suite: bool = False


class ProposeIndexRequest(BaseModel):
    project_id: str
    table_name: str
    index_name: str
    columns: List[str]


class ProposePerfOptimizationRequest(BaseModel):
    project_id: str
    optimization_type: str
    target_component: str


class SyncDocsRequest(BaseModel):
    project_id: str
    commit_sha: Optional[str] = None


# Endpoints
@router.get("/policy")
async def get_policy(project_id: str):
    """Retrieve maintenance policy for a project."""
    async with get_db_session() as session:
        policy = await scheduler.get_policy(session, project_id)
        return {
            "id": policy.id,
            "project_id": policy.project_id,
            "schedule": policy.schedule,
            "is_enabled": policy.is_enabled,
            "auto_remediate_level1": policy.auto_remediate_level1,
            "require_approval_level2": policy.require_approval_level2,
            "maintenance_window": policy.maintenance_window,
        }


@router.post("/policy")
async def configure_policy(payload: ConfigurePolicyRequest):
    """Configure or update maintenance policy."""
    async with get_db_session() as session:
        policy = await scheduler.configure_policy(
            db=session,
            project_id=payload.project_id,
            schedule=payload.schedule,
            is_enabled=payload.is_enabled,
            auto_remediate_level1=payload.auto_remediate_level1,
            require_approval_level2=payload.require_approval_level2,
            maintenance_window=payload.maintenance_window,
        )
        return {"id": policy.id, "status": "configured", "schedule": policy.schedule}


@router.post("/tasks")
async def schedule_task(payload: ScheduleTaskRequest):
    """Queue a new maintenance task."""
    async with get_db_session() as session:
        task = await scheduler.schedule_task(
            db=session,
            project_id=payload.project_id,
            maintenance_type=payload.maintenance_type,
            trigger_type=payload.trigger_type,
            priority=payload.priority,
            assigned_agents=payload.assigned_agents,
        )
        return {
            "id": task.id,
            "maintenance_type": task.maintenance_type,
            "status": task.status,
            "git_branch": task.git_branch,
        }


@router.get("/tasks")
async def list_tasks(project_id: Optional[str] = None, status: Optional[str] = None):
    """List maintenance tasks."""
    async with get_db_session() as session:
        tasks = await scheduler.list_tasks(session, project_id=project_id, status=status)
        return [
            {
                "id": t.id,
                "project_id": t.project_id,
                "maintenance_type": t.maintenance_type,
                "trigger_type": t.trigger_type,
                "priority": t.priority,
                "assigned_agents": t.assigned_agents,
                "status": t.status,
                "git_branch": t.git_branch,
                "created_at": t.created_at.isoformat() if t.created_at else None,
                "completed_at": t.completed_at.isoformat() if t.completed_at else None,
            }
            for t in tasks
        ]


@router.post("/quality/scan")
async def run_quality_scan(payload: QualityScanRequest):
    """Trigger on-demand code quality analysis."""
    async with get_db_session() as session:
        report = await quality_agent.analyze_project_quality(
            db=session,
            project_id=payload.project_id,
            task_id=payload.task_id,
        )
        return {
            "id": report.id,
            "quality_score": report.quality_score,
            "maintainability_rating": report.maintainability_rating,
            "test_coverage_percent": report.test_coverage_percent,
            "issues_breakdown": report.issues_breakdown,
            "recommendations": report.recommendations,
        }


@router.get("/quality/latest")
async def get_latest_quality(project_id: str):
    """Fetch latest code quality report."""
    async with get_db_session() as session:
        report = await quality_agent.get_latest_report(session, project_id)
        if not report:
            # Fallback scan
            report = await quality_agent.analyze_project_quality(session, project_id)
        return {
            "id": report.id,
            "quality_score": report.quality_score,
            "maintainability_rating": report.maintainability_rating,
            "complexity_score": report.complexity_score,
            "duplication_percent": report.duplication_percent,
            "test_coverage_percent": report.test_coverage_percent,
            "issues_breakdown": report.issues_breakdown,
            "recommendations": report.recommendations,
        }


@router.post("/dependencies/scan")
async def scan_dependencies(project_id: str):
    """Scan dependencies for outdated packages, licenses, and CVEs."""
    async with get_db_session() as session:
        vulns = await dep_agent.scan_dependencies(session, project_id)
        return [
            {
                "id": v.id,
                "package_name": v.package_name,
                "current_version": v.current_version,
                "recommended_version": v.recommended_version,
                "vulnerability_cve": v.vulnerability_cve,
                "severity": v.severity,
                "ecosystem": v.ecosystem,
                "status": v.status,
            }
            for v in vulns
        ]


@router.post("/dependencies/upgrade")
async def upgrade_dependency(payload: DependencyUpgradeRequest):
    """Propose dependency upgrade PR awaiting Level 2 approval."""
    async with get_db_session() as session:
        res = await dep_agent.create_upgrade_branch_and_pr(
            db=session,
            project_id=payload.project_id,
            package_name=payload.package_name,
            target_version=payload.target_version,
        )
        return res


@router.get("/security/findings")
async def get_security_findings(project_id: str):
    """Get security vulnerability findings."""
    async with get_db_session() as session:
        findings = await security_agent.scan_security_findings(session, project_id)
        return findings


@router.post("/security/remediate")
async def remediate_security_finding(payload: SecurityRemediationRequest):
    """Generate security remediation PR with Level 2 approval gate."""
    async with get_db_session() as session:
        res = await security_agent.remediate_vulnerability(
            db=session,
            project_id=payload.project_id,
            finding_id=payload.finding_id,
            category=payload.category,
            file_path=payload.file_path,
            proposed_patch=payload.proposed_patch,
        )
        return res


@router.get("/bugs")
async def list_bugs(project_id: Optional[str] = None, status: Optional[str] = None):
    """List detected software bugs."""
    async with get_db_session() as session:
        bugs = await bug_agent.list_bugs(session, project_id=project_id, status=status)
        return [
            {
                "id": b.id,
                "project_id": b.project_id,
                "title": b.title,
                "description": b.description,
                "status": b.status,
                "git_branch": b.git_branch,
                "pr_url": b.pr_url,
                "test_evidence": b.test_evidence,
                "created_at": b.created_at.isoformat() if b.created_at else None,
            }
            for b in bugs
        ]


@router.post("/bugs/{bug_id}/fix")
async def trigger_bug_fix(bug_id: str):
    """Execute autonomous bug fixing pipeline and generate PR."""
    async with get_db_session() as session:
        res = await bug_agent.auto_generate_bug_fix(session, bug_id)
        return res


@router.post("/regression/run")
async def run_regression_suite(payload: RunRegressionRequest):
    """Execute impact-based regression test suite."""
    res = await regression_engine.execute_targeted_regression(
        changed_files=payload.changed_files,
        project_id=payload.project_id,
        run_full_suite=payload.run_full_suite,
    )
    return res


@router.get("/database/health")
async def get_database_health(project_id: str):
    """Get database maintenance diagnostics, index recommendations, and connection metrics."""
    async with get_db_session() as session:
        health = await db_agent.analyze_database_health(session, project_id)
        return health


@router.post("/database/optimize-index")
async def propose_database_index(payload: ProposeIndexRequest):
    """Propose non-blocking index optimization with Level 2 approval gate."""
    async with get_db_session() as session:
        res = await db_agent.propose_index_optimization(
            db=session,
            project_id=payload.project_id,
            table_name=payload.table_name,
            index_name=payload.index_name,
            columns=payload.columns,
        )
        return res


@router.get("/performance/bottlenecks")
async def get_performance_bottlenecks(project_id: str):
    """Inspect production telemetry for performance bottlenecks."""
    async with get_db_session() as session:
        res = await perf_optimizer.analyze_performance_bottlenecks(session, project_id)
        return res


@router.post("/performance/optimize")
async def propose_performance_optimization(payload: ProposePerfOptimizationRequest):
    """Generate empirical benchmark-validated performance optimization PR."""
    async with get_db_session() as session:
        res = await perf_optimizer.benchmark_and_propose_optimization(
            db=session,
            project_id=payload.project_id,
            optimization_type=payload.optimization_type,
            target_component=payload.target_component,
        )
        return res


@router.get("/tech-debt")
async def get_technical_debt(project_id: str):
    """Get technical debt score, health grade, and backlog items."""
    async with get_db_session() as session:
        summary = await debt_agent.scan_technical_debt(session, project_id)
        items = await debt_agent.list_debt_items(session, project_id)
        summary["items"] = [
            {
                "id": i.id,
                "title": i.title,
                "category": i.category,
                "severity": i.severity,
                "debt_score_impact": i.debt_score_impact,
                "effort_hours": i.effort_hours,
                "remediation_plan": i.remediation_plan,
                "status": i.status,
            }
            for i in items
        ]
        return summary


@router.post("/docs/sync")
async def sync_documentation(payload: SyncDocsRequest):
    """Audit and synchronize technical documentation with commit changes."""
    res = await doc_agent.audit_and_sync_docs(
        project_id=payload.project_id,
        commit_sha=payload.commit_sha,
    )
    return res


@router.get("/improvements")
async def list_improvements(project_id: str):
    """Get prioritized continuous improvement proposals."""
    async with get_db_session() as session:
        proposals = await improvement_agent.list_proposals(session, project_id)
        if not proposals:
            proposals = await improvement_agent.generate_proposals(session, project_id)
        return [
            {
                "id": p.id,
                "title": p.title,
                "category": p.category,
                "problem_statement": p.problem_statement,
                "supporting_evidence": p.supporting_evidence,
                "expected_benefit": p.expected_benefit,
                "implementation_complexity": p.implementation_complexity,
                "potential_risk": p.potential_risk,
                "estimated_cost_usd": p.estimated_cost_usd,
                "status": p.status,
                "created_at": p.created_at.isoformat() if p.created_at else None,
            }
            for p in proposals
        ]


@router.post("/improvements/generate")
async def generate_improvements(project_id: str):
    """Trigger cross-engine continuous improvement proposal synthesis."""
    async with get_db_session() as session:
        proposals = await improvement_agent.generate_proposals(session, project_id)
        return [
            {
                "id": p.id,
                "title": p.title,
                "category": p.category,
                "expected_benefit": p.expected_benefit,
                "status": p.status,
            }
            for p in proposals
        ]
