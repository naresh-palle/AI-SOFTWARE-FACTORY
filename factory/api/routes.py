"""
FastAPI Routes for Autonomous AI Software Development Factory.
"""

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
    Project,
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


router.include_router(api)
