"""
FastAPI Routes for Autonomous AI Software Development Factory.
"""

import json
import secrets
from datetime import datetime
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import desc, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from factory.agents.dynamic_selector import DynamicAgentSelector, ProjectPlan
from factory.agents.registry import AGENT_CATALOG, AgentMetadata
from factory.core.config import EnvironmentType, settings
from factory.core.database import get_db
from factory.core.logger import logger
from factory.models.schema import (
    ApprovalRecord,
    AuditLog,
    CostRecord,
    DeploymentHistory,
    DeveloperAccountReference,
    ExternalIntegration,
    GitHubRepositoryRecord,
    OAuthConnection,
    Project,
    ProjectArchitecture,
    SecurityFinding,
    Task,
    TestingResult,
)
from factory.orchestrator.master import MasterOrchestrator

router = APIRouter()
orchestrator = MasterOrchestrator()


def public_error_detail(exc: Exception) -> str:
    """Return a client-safe error. Debug mode keeps the exception text."""
    if settings.DEBUG:
        return str(exc)
    return "Internal server error"


def _constant_time_equal(provided: str, expected: str) -> bool:
    try:
        return secrets.compare_digest(provided.encode("utf-8"), expected.encode("utf-8"))
    except Exception:
        return False


async def require_operator(authorization: Optional[str] = Header(default=None)) -> None:
    """Protect operator routes when a token is configured, and always in production."""
    configured = settings.FACTORY_API_TOKEN or ""
    if settings.ENVIRONMENT == EnvironmentType.PRODUCTION and not configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Operator authentication is not configured",
        )
    if not configured:
        return
    expected = f"Bearer {configured}"
    if not _constant_time_equal(authorization or "", expected):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")


api = APIRouter(prefix="/api/v1", dependencies=[Depends(require_operator)])


class AnalyzeRequest(BaseModel):
    requirement_text: str = Field(..., min_length=5, description="Natural language software requirement")
    platform_target: Optional[str] = Field("fullstack", description="website, android, ios, combined, fullstack")


class CreateProjectRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    requirement_text: str = Field(..., min_length=5)
    platform_target: str = Field("fullstack")
    execution_mode: str = Field("autonomous")


class ApprovalResponseRequest(BaseModel):
    decision: str = Field(..., pattern="^(approved|rejected)$")
    notes: Optional[str] = None
    approver_email: Optional[str] = "admin@factory.local"


def _approval_payload(record: ApprovalRecord) -> Dict[str, Any]:
    return {
        "id": record.id,
        "project_id": record.project_id,
        "stage": record.stage,
        "action_type": record.action_type,
        "description": record.description,
        "status": record.status,
        "notes": record.notes,
        "created_at": record.created_at,
        "decided_at": record.decided_at,
    }


@router.get("/health", tags=["System"])
async def health_check(db: AsyncSession = Depends(get_db)):
    await db.execute(text("SELECT 1"))
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "environment": settings.ENVIRONMENT,
        "default_execution_mode": settings.DEFAULT_EXECUTION_MODE,
        "llm_provider": settings.DEFAULT_LLM_PROVIDER,
        "database": "connected",
    }


@api.post("/analyze", response_model=ProjectPlan, tags=["Orchestration"])
async def analyze_requirement(req: AnalyzeRequest):
    """Analyze a natural-language requirement and return tech stack and agent assignment."""
    try:
        selector = DynamicAgentSelector()
        plan = await selector.analyze_and_select(
            requirement_text=req.requirement_text,
            user_platform_target=req.platform_target,
        )
        return plan
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise HTTPException(status_code=500, detail=public_error_detail(e))


@api.post("/projects", status_code=status.HTTP_201_CREATED, tags=["Projects"])
async def create_project(req: CreateProjectRequest):
    """Initialize a new autonomous software project."""
    try:
        project = await orchestrator.initialize_project(
            name=req.name,
            requirement_text=req.requirement_text,
            platform_target=req.platform_target,
            execution_mode=req.execution_mode,
        )
        state = await orchestrator.get_orchestration_state(project.id)
        return {"project_id": project.id, "name": project.name, "state": state}
    except Exception as e:
        logger.error(f"Project creation failed: {e}")
        raise HTTPException(status_code=500, detail=public_error_detail(e))


@api.get("/projects", tags=["Projects"])
async def list_projects(db: AsyncSession = Depends(get_db)):
    """List all registered projects."""
    stmt = select(Project).order_by(desc(Project.created_at))
    res = await db.execute(stmt)
    projects = res.scalars().all()
    return [
        {
            "id": p.id,
            "name": p.name,
            "platform_target": p.platform_target,
            "execution_mode": p.execution_mode,
            "status": p.status,
            "current_stage": p.current_stage,
            "created_at": p.created_at,
        }
        for p in projects
    ]


@api.get("/projects/{project_id}", tags=["Projects"])
async def get_project(project_id: str):
    """Get project details and current orchestration state."""
    try:
        state = await orchestrator.get_orchestration_state(project_id)
        return state
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=public_error_detail(e))


@api.post("/projects/{project_id}/execute", tags=["Orchestration"])
async def execute_project_pipeline(
    project_id: str,
    stop_at_stage: int = Query(23, ge=1, le=23),
):
    """Trigger autonomous stage execution pipeline for a project."""
    try:
        state = await orchestrator.run_pipeline(project_id, stop_at_stage=stop_at_stage)
        return state
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=public_error_detail(e))


@api.get("/projects/{project_id}/approvals", tags=["Approvals"])
async def get_project_approvals(project_id: str, db: AsyncSession = Depends(get_db)):
    """Get all approval records for a project."""
    stmt = select(ApprovalRecord).where(ApprovalRecord.project_id == project_id)
    res = await db.execute(stmt)
    return [_approval_payload(record) for record in res.scalars().all()]


@api.post("/approvals/{approval_id}/respond", tags=["Approvals"])
async def respond_to_approval(
    approval_id: str,
    req: ApprovalResponseRequest,
    db: AsyncSession = Depends(get_db),
):
    """Approve or reject a human approval checkpoint."""
    stmt = select(ApprovalRecord).where(ApprovalRecord.id == approval_id)
    res = await db.execute(stmt)
    record = res.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="Approval record not found")
    if record.status != "pending":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Approval is already decided")

    record.status = req.decision
    record.notes = req.notes
    record.decided_at = datetime.utcnow()
    db.add(
        AuditLog(
            project_id=record.project_id,
            action=f"APPROVAL_{req.decision.upper()}",
            actor=req.approver_email or "admin",
            details_json={"approval_id": approval_id, "notes": req.notes},
        )
    )
    return {"status": "success", "approval_id": approval_id, "decision": req.decision}


@api.get("/agents", response_model=List[AgentMetadata], tags=["Agents"])
async def list_agents():
    """List the complete catalog of 97 logical specialist agents."""
    return AGENT_CATALOG


@api.get("/audit-logs", tags=["Audit"])
async def get_audit_logs(
    project_id: Optional[str] = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve system audit logs."""
    stmt = select(AuditLog)
    if project_id:
        stmt = stmt.where(AuditLog.project_id == project_id)
    stmt = stmt.order_by(desc(AuditLog.created_at)).limit(limit)
    res = await db.execute(stmt)
    return res.scalars().all()


@api.get("/overview/stats", tags=["Overview"])
async def get_overview_stats(db: AsyncSession = Depends(get_db)):
    """Aggregated statistics for the factory overview dashboard."""
    # Projects summary
    p_res = await db.execute(select(Project))
    projects = p_res.scalars().all()
    total_projects = len(projects)
    active_projects = sum(1 for p in projects if p.status in ("in_progress", "planning"))
    completed_projects = sum(1 for p in projects if p.status == "completed")
    failed_projects = sum(1 for p in projects if p.status == "failed")

    # Pending approvals
    app_res = await db.execute(select(ApprovalRecord).where(ApprovalRecord.status == "pending"))
    pending_approvals = app_res.scalars().all()

    # Costs
    cost_res = await db.execute(select(CostRecord))
    costs = cost_res.scalars().all()
    total_cost_usd = sum(c.amount_usd for c in costs)

    # Recent Audit Logs
    audit_res = await db.execute(select(AuditLog).order_by(desc(AuditLog.created_at)).limit(10))
    recent_activities = audit_res.scalars().all()

    # Active tasks
    task_res = await db.execute(select(Task).where(Task.status == "in_progress"))
    active_tasks = task_res.scalars().all()
    running_workflows = len(set(t.project_id for t in active_tasks))

    return {
        "total_projects": total_projects,
        "active_projects": active_projects,
        "completed_projects": completed_projects,
        "failed_projects": failed_projects,
        "total_agents": len(AGENT_CATALOG),
        "active_agents_count": len(active_tasks),
        "pending_approvals_count": len(pending_approvals),
        "running_workflows": running_workflows,
        "total_cost_usd": round(total_cost_usd, 2),
        "system_status": "healthy",
        "recent_activities": [
            {
                "id": a.id,
                "project_id": a.project_id,
                "action": a.action,
                "actor": a.actor,
                "details": a.details_json,
                "created_at": a.created_at,
            }
            for a in recent_activities
        ],
    }


@api.get("/projects/{project_id}/tasks", tags=["Tasks"])
async def get_project_tasks(project_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieve all tasks for a specific project."""
    stmt = select(Task).where(Task.project_id == project_id).order_by(Task.stage)
    res = await db.execute(stmt)
    tasks = res.scalars().all()
    return [
        {
            "id": t.id,
            "project_id": t.project_id,
            "stage": t.stage,
            "agent_name": t.agent_name,
            "title": t.title,
            "description": t.description,
            "status": t.status,
            "execution_evidence": t.execution_evidence,
            "started_at": t.started_at,
            "completed_at": t.completed_at,
        }
        for t in tasks
    ]


@api.get("/projects/{project_id}/architecture", tags=["Architecture"])
async def get_project_architecture(project_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieve architecture details and diagram for a project."""
    stmt = select(ProjectArchitecture).where(ProjectArchitecture.project_id == project_id)
    res = await db.execute(stmt)
    arch = res.scalar_one_or_none()
    if not arch:
        raise HTTPException(status_code=404, detail="Architecture not found for this project")
    return {
        "project_id": arch.project_id,
        "frontend_stack": arch.frontend_stack,
        "backend_stack": arch.backend_stack,
        "mobile_stack": arch.mobile_stack,
        "database_stack": arch.database_stack,
        "cache_stack": arch.cache_stack,
        "cloud_stack": arch.cloud_stack,
        "ci_cd_stack": arch.ci_cd_stack,
        "selected_agents": arch.selected_agents,
        "mermaid_diagram": arch.mermaid_diagram,
        "estimated_cost_usd": arch.estimated_cost_usd,
        "created_at": arch.created_at,
    }


@api.get("/projects/{project_id}/github", tags=["GitHub"])
async def get_project_github(project_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieve GitHub repository connection for a project."""
    stmt = select(GitHubRepositoryRecord).where(GitHubRepositoryRecord.project_id == project_id)
    res = await db.execute(stmt)
    repo = res.scalar_one_or_none()
    repo_url = repo.repo_url if repo else None
    connected = bool(repo_url and str(repo_url).startswith("https://github.com/"))
    pull_requests: List[Dict[str, Any]] = []
    latest_commit = repo.latest_commit_hash if repo else None
    storage = settings.PROJECTS_STORAGE_DIR.resolve()
    candidate = (storage / project_id).resolve()
    root = candidate if candidate != storage and storage in candidate.parents and candidate.is_dir() else None
    if root is not None:
        pr_file = root / "pull_requests.json"
        if pr_file.is_file():
            loaded = json.loads(pr_file.read_text(encoding="utf-8"))
            if isinstance(loaded, list):
                pull_requests = loaded
        if latest_commit is None and (root / ".git").exists():
            import subprocess

            proc = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=root,
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
            if proc.returncode == 0:
                latest_commit = proc.stdout.strip()
    return {
        "connected": connected,
        "repo_name": repo.repo_name if repo else None,
        "repo_url": repo_url if connected else None,
        "local_repo": None if connected else repo_url,
        "default_branch": repo.default_branch if repo else "main",
        "current_branch": repo.current_branch if repo else "main",
        "latest_commit_hash": latest_commit,
        "pull_requests": pull_requests,
    }


@api.get("/meta/status", tags=["Meta"])
async def get_meta_status(db: AsyncSession = Depends(get_db)):
    """Retrieve Meta Developer Center integration status."""
    acc_res = await db.execute(select(DeveloperAccountReference).where(DeveloperAccountReference.platform == "meta"))
    accounts = acc_res.scalars().all()

    int_res = await db.execute(select(ExternalIntegration).where(ExternalIntegration.provider == "meta"))
    integrations = int_res.scalars().all()

    return {
        "configured": bool(settings.META_APP_ID),
        "app_id": settings.META_APP_ID if settings.META_APP_ID else "Not Configured",
        "has_app_secret": bool(settings.META_APP_SECRET),
        "accounts_connected": len(accounts),
        "active_integrations": [
            {
                "id": i.id,
                "project_id": i.project_id,
                "type": i.integration_type,
                "is_active": i.is_active,
            }
            for i in integrations
        ],
        "supported_products": [
            {"product": "Facebook Login", "status": "Ready", "permissions": ["email", "public_profile"]},
            {"product": "Instagram Graph API", "status": "Configured", "permissions": ["instagram_basic", "pages_show_list"]},
            {"product": "WhatsApp Business Platform", "status": "Ready", "permissions": ["whatsapp_business_messaging"]},
            {"product": "Messenger API", "status": "Configured", "permissions": ["pages_messaging"]},
            {"product": "Threads API", "status": "Available", "permissions": ["threads_basic"]},
        ],
    }


@api.get("/integrations", tags=["Integrations"])
async def get_external_integrations(db: AsyncSession = Depends(get_db)):
    """Retrieve all external API integrations."""
    stmt = select(ExternalIntegration)
    res = await db.execute(stmt)
    records = res.scalars().all()
    return [
        {
            "id": r.id,
            "project_id": r.project_id,
            "provider": r.provider,
            "integration_type": r.integration_type,
            "is_active": r.is_active,
            "config": r.config_json,
        }
        for r in records
    ]


@api.get("/security/findings", tags=["Security"])
async def get_security_findings(db: AsyncSession = Depends(get_db)):
    """Retrieve security audit findings."""
    stmt = select(SecurityFinding).order_by(desc(SecurityFinding.created_at))
    res = await db.execute(stmt)
    records = res.scalars().all()
    return [
        {
            "id": r.id,
            "project_id": r.project_id,
            "severity": r.severity,
            "title": r.title,
            "description": r.description,
            "tool": r.tool,
            "status": r.remediation_status,
            "created_at": r.created_at,
        }
        for r in records
    ]


@api.get("/qa/results", tags=["QA"])
async def get_qa_results(db: AsyncSession = Depends(get_db)):
    """Retrieve QA test suite execution results."""
    stmt = select(TestingResult).order_by(desc(TestingResult.executed_at))
    res = await db.execute(stmt)
    records = res.scalars().all()
    return [
        {
            "id": r.id,
            "project_id": r.project_id,
            "test_suite": r.test_suite,
            "total_tests": r.total_tests,
            "passed_tests": r.passed_tests,
            "failed_tests": r.failed_tests,
            "evidence_path": r.evidence_path,
            "executed_at": r.executed_at,
        }
        for r in records
    ]


@api.get("/deployments", tags=["Deployments"])
async def get_deployments(db: AsyncSession = Depends(get_db)):
    """Retrieve deployment history records."""
    stmt = select(DeploymentHistory).order_by(desc(DeploymentHistory.deployed_at))
    res = await db.execute(stmt)
    records = res.scalars().all()
    return [
        {
            "id": r.id,
            "project_id": r.project_id,
            "environment": r.environment,
            "status": r.status,
            "commit_sha": r.commit_sha,
            "endpoint_url": r.endpoint_url,
            "deployed_at": r.deployed_at,
        }
        for r in records
    ]


@api.get("/costs", tags=["Cost"])
async def get_cost_records(db: AsyncSession = Depends(get_db)):
    """Retrieve FinOps cost records and breakdown."""
    stmt = select(CostRecord).order_by(desc(CostRecord.recorded_at))
    res = await db.execute(stmt)
    records = res.scalars().all()
    total = sum(r.amount_usd for r in records)
    by_category: Dict[str, float] = {}
    for r in records:
        by_category[r.category] = by_category.get(r.category, 0.0) + r.amount_usd
    return {
        "total_usd": round(total, 2),
        "by_category": {k: round(v, 2) for k, v in by_category.items()},
        "records": [
            {
                "id": r.id,
                "project_id": r.project_id,
                "category": r.category,
                "amount_usd": r.amount_usd,
                "details": r.details,
                "recorded_at": r.recorded_at,
            }
            for r in records
        ],
    }


@api.get("/database/status", tags=["Database"])
async def get_database_status(db: AsyncSession = Depends(get_db)):
    """Retrieve database health and table metrics."""
    # Table counts
    p_count = (await db.execute(select(Project))).scalars().all()
    t_count = (await db.execute(select(Task))).scalars().all()
    app_count = (await db.execute(select(ApprovalRecord))).scalars().all()
    audit_count = (await db.execute(select(AuditLog))).scalars().all()

    return {
        "engine": "PostgreSQL (asyncpg)" if "postgres" in settings.DATABASE_URL else "SQLite (aiosqlite)",
        "connection": "healthy",
        "tables": {
            "projects": len(p_count),
            "agents": len(AGENT_CATALOG),
            "tasks": len(t_count),
            "approvals": len(app_count),
            "audit_logs": len(audit_count),
        },
    }


@api.get("/system/settings", tags=["System"])
async def get_system_settings():
    """Retrieve system configuration settings (sensitive keys masked)."""
    return {
        "app_name": settings.APP_NAME,
        "environment": settings.ENVIRONMENT,
        "default_execution_mode": settings.DEFAULT_EXECUTION_MODE,
        "default_llm_provider": settings.DEFAULT_LLM_PROVIDER,
        "ollama_base_url": settings.OLLAMA_BASE_URL,
        "ollama_model": settings.OLLAMA_MODEL,
        "github_username": settings.GITHUB_USERNAME,
        "has_github_token": bool(settings.GITHUB_TOKEN),
        "has_meta_app": bool(settings.META_APP_ID),
        "encryption_configured": bool(settings.ENCRYPTION_KEY),
    }


router.include_router(api)
