"""
Cloud Worker & Persistent Execution API Endpoints.
Provides worker registration, heartbeat, job leasing, checkpointing, and lifecycle management.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import desc, func, select

from factory.core.config import settings
from factory.core.database import get_db_session
from factory.core.logger import logger
from factory.models.schema import DeadLetterJob, Project, WorkerNode, WorkflowCheckpoint, WorkflowJob
from factory.workflow.engine import PersistentWorkflowEngine
from factory.workflow.queue import WorkflowQueue
from factory.workflow.recovery import WorkflowRecoveryMonitor
from factory.workflow.cost_tracker import CloudCostTracker


router = APIRouter(prefix="/cloud", tags=["Cloud Worker & Execution Engine"])
engine = PersistentWorkflowEngine()
queue = WorkflowQueue()
recovery = WorkflowRecoveryMonitor()
cost_tracker = CloudCostTracker()


def verify_worker_auth(x_worker_token: Optional[str] = Header(None)) -> bool:
    """Validate internal worker authentication token."""
    expected = settings.WORKER_AUTH_TOKEN
    if not expected:
        return True
    if x_worker_token != expected:
        raise HTTPException(status_code=401, detail="Invalid worker authorization token")
    return True


# ==========================================
# Pydantic Request / Response Models
# ==========================================

class WorkerRegisterRequest(BaseModel):
    worker_name: str
    hostname: Optional[str] = None
    ip_address: Optional[str] = None
    cpu_cores: int = 2
    memory_mb: int = 4096
    tags: Dict[str, Any] = Field(default_factory=dict)


class WorkerHeartbeatRequest(BaseModel):
    worker_id: str
    status: Optional[str] = None
    current_job_id: Optional[str] = None
    cpu_percent: Optional[float] = None
    memory_percent: Optional[float] = None


class CheckpointSubmitRequest(BaseModel):
    job_id: str
    worker_id: str
    stage_number: int
    stage_title: str
    status: str = "completed"
    evidence: List[str] = Field(default_factory=list)
    artifacts: Dict[str, Any] = Field(default_factory=dict)
    duration_ms: int = 0


class JobClaimRequest(BaseModel):
    worker_id: str


class JobFailRequest(BaseModel):
    job_id: str
    worker_id: str
    error_message: str
    is_fatal: bool = False


class JobCompleteRequest(BaseModel):
    job_id: str
    worker_id: str
    final_data: Dict[str, Any] = Field(default_factory=dict)


class WorkflowSubmitRequest(BaseModel):
    project_id: str
    target_stage: int = 23
    priority: int = 5
    idempotency_key: Optional[str] = None


# ==========================================
# Worker Node APIs
# ==========================================

@router.post("/workers/register")
async def register_worker(
    req: WorkerRegisterRequest,
    _auth: bool = Depends(verify_worker_auth),
):
    """Register a new cloud worker node into the cluster."""
    async with get_db_session() as session:
        # Check if worker exists with same name
        q = select(WorkerNode).where(WorkerNode.worker_name == req.worker_name)
        existing = (await session.execute(q)).scalar_one_or_none()
        if existing:
            existing.status = "idle"
            existing.last_heartbeat = datetime.utcnow()
            existing.cpu_cores = req.cpu_cores
            existing.memory_mb = req.memory_mb
            await session.commit()
            return {
                "worker_id": existing.id,
                "worker_name": existing.worker_name,
                "status": existing.status,
                "registered": True,
            }

        worker = WorkerNode(
            worker_name=req.worker_name,
            hostname=req.hostname or "fargate-host",
            ip_address=req.ip_address or "10.0.0.1",
            status="idle",
            cpu_cores=req.cpu_cores,
            memory_mb=req.memory_mb,
            last_heartbeat=datetime.utcnow(),
            registered_at=datetime.utcnow(),
            tags=req.tags,
        )
        session.add(worker)
        await session.commit()
        await session.refresh(worker)

    logger.info(f"Worker API: Registered worker {worker.worker_name} ({worker.id})")
    return {
        "worker_id": worker.id,
        "worker_name": worker.worker_name,
        "status": worker.status,
        "registered": True,
    }


@router.post("/workers/heartbeat")
async def worker_heartbeat(
    req: WorkerHeartbeatRequest,
    _auth: bool = Depends(verify_worker_auth),
):
    """Update worker heartbeat timestamp and telemetry."""
    async with get_db_session() as session:
        q = select(WorkerNode).where(WorkerNode.id == req.worker_id)
        worker = (await session.execute(q)).scalar_one_or_none()
        if not worker:
            raise HTTPException(status_code=404, detail="Worker not found")

        worker.last_heartbeat = datetime.utcnow()
        if req.status:
            worker.status = req.status
        if req.current_job_id:
            worker.current_job_id = req.current_job_id
        await session.commit()

    return {"status": "ok", "worker_id": req.worker_id, "timestamp": datetime.utcnow().isoformat()}


@router.post("/workers/claim")
async def claim_next_job(
    req: JobClaimRequest,
    _auth: bool = Depends(verify_worker_auth),
):
    """Claim the highest-priority pending workflow job."""
    job = await queue.claim_job(req.worker_id)
    if not job:
        return {"claimed": False, "job": None}
    return {
        "claimed": True,
        "job": {
            "id": job.id,
            "project_id": job.project_id,
            "job_type": job.job_type,
            "current_stage": job.current_stage,
            "target_stage": job.target_stage,
            "priority": job.priority,
            "lease_expires_at": job.lease_expires_at.isoformat() if job.lease_expires_at else None,
        },
    }


@router.post("/workers/checkpoints")
async def submit_checkpoint(
    req: CheckpointSubmitRequest,
    _auth: bool = Depends(verify_worker_auth),
):
    """Submit stage execution checkpoint from worker."""
    cp = await queue.record_checkpoint(
        job_id=req.job_id,
        stage_number=req.stage_number,
        stage_title=req.stage_title,
        status=req.status,
        evidence=req.evidence,
        artifacts=req.artifacts,
        duration_ms=req.duration_ms,
    )
    return {
        "checkpoint_id": cp.id,
        "stage_number": cp.stage_number,
        "status": cp.status,
        "created_at": cp.created_at.isoformat(),
    }


@router.post("/workers/complete")
async def complete_job_api(
    req: JobCompleteRequest,
    _auth: bool = Depends(verify_worker_auth),
):
    """Mark a workflow job as completed."""
    job = await queue.complete_job(req.job_id, req.worker_id, req.final_data)
    return {"job_id": job.id, "status": job.status, "completed_at": job.completed_at.isoformat()}


@router.post("/workers/fail")
async def fail_job_api(
    req: JobFailRequest,
    _auth: bool = Depends(verify_worker_auth),
):
    """Report a job execution failure."""
    job = await queue.fail_job(req.job_id, req.error_message, req.is_fatal)
    return {"job_id": job.id, "status": job.status, "retries": job.retry_count}


@router.get("/workers")
async def list_workers():
    """List all registered worker nodes and their status."""
    async with get_db_session() as session:
        q = select(WorkerNode).order_by(desc(WorkerNode.registered_at))
        workers = (await session.execute(q)).scalars().all()
        return [
            {
                "id": w.id,
                "worker_name": w.worker_name,
                "hostname": w.hostname,
                "ip_address": w.ip_address,
                "status": w.status,
                "cpu_cores": w.cpu_cores,
                "memory_mb": w.memory_mb,
                "current_job_id": w.current_job_id,
                "last_heartbeat": w.last_heartbeat.isoformat() if w.last_heartbeat else None,
                "total_jobs_completed": w.total_jobs_completed or 0,
            }
            for w in workers
        ]


# ==========================================
# Workflow Job Lifecycle & Dashboard APIs
# ==========================================

@router.post("/submit")
async def submit_workflow_job(req: WorkflowSubmitRequest):
    """Submit a project into the persistent execution queue."""
    try:
        job = await queue.enqueue_job(
            project_id=req.project_id,
            job_type="full_pipeline",
            priority=req.priority,
            target_stage=req.target_stage,
            idempotency_key=req.idempotency_key,
        )
        return {
            "job_id": job.id,
            "project_id": job.project_id,
            "status": job.status,
            "current_stage": job.current_stage,
            "target_stage": job.target_stage,
            "priority": job.priority,
            "created_at": job.created_at.isoformat(),
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/jobs")
async def list_workflow_jobs(
    project_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100),
):
    """List workflow jobs with status, stage, priority, and assigned worker."""
    jobs = await queue.list_jobs(project_id=project_id, status=status, limit=limit)
    return [
        {
            "id": j.id,
            "project_id": j.project_id,
            "job_type": j.job_type,
            "status": j.status,
            "priority": j.priority,
            "current_stage": j.current_stage,
            "target_stage": j.target_stage,
            "assigned_worker_id": j.assigned_worker_id,
            "retry_count": j.retry_count,
            "error_message": j.error_message,
            "checkpoint_data": j.checkpoint_data,
            "created_at": j.created_at.isoformat() if j.created_at else None,
            "updated_at": j.updated_at.isoformat() if j.updated_at else None,
        }
        for j in jobs
    ]


@router.get("/jobs/{job_id}")
async def get_workflow_job_detail(job_id: str):
    """Get detailed status and checkpoint history for a job."""
    job = await queue.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    checkpoints = await queue.list_checkpoints(job_id)

    return {
        "job": {
            "id": job.id,
            "project_id": job.project_id,
            "status": job.status,
            "priority": job.priority,
            "current_stage": job.current_stage,
            "target_stage": job.target_stage,
            "assigned_worker_id": job.assigned_worker_id,
            "retry_count": job.retry_count,
            "error_message": job.error_message,
            "created_at": job.created_at.isoformat() if job.created_at else None,
        },
        "checkpoints": [
            {
                "id": c.id,
                "stage_number": c.stage_number,
                "stage_title": c.stage_title,
                "status": c.status,
                "evidence": c.evidence_json,
                "artifacts": c.artifacts_json,
                "duration_ms": c.duration_ms,
                "created_at": c.created_at.isoformat(),
            }
            for c in checkpoints
        ],
    }


@router.post("/jobs/{job_id}/pause")
async def pause_job_endpoint(job_id: str):
    """Pause an active workflow job."""
    try:
        job = await queue.pause_job(job_id)
        return {"job_id": job.id, "status": job.status}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/jobs/{job_id}/resume")
async def resume_job_endpoint(job_id: str):
    """Resume a paused workflow job."""
    try:
        job = await queue.resume_job(job_id)
        return {"job_id": job.id, "status": job.status}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/jobs/{job_id}/cancel")
async def cancel_job_endpoint(job_id: str):
    """Cancel a workflow job."""
    try:
        job = await queue.cancel_job(job_id)
        return {"job_id": job.id, "status": job.status}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/jobs/{job_id}/retry")
async def retry_job_endpoint(job_id: str):
    """Manually retry a failed or dead-letter job."""
    try:
        job = await queue.retry_failed_job(job_id)
        return {"job_id": job.id, "status": job.status, "retries_reset": True}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/status")
async def get_cloud_execution_status():
    """Aggregated telemetry on cloud infrastructure, workers, queue, and costs."""
    async with get_db_session() as session:
        # Worker stats
        w_query = select(WorkerNode.status, func.count(WorkerNode.id)).group_by(WorkerNode.status)
        w_counts = dict((await session.execute(w_query)).all())

        # Job stats
        j_query = select(WorkflowJob.status, func.count(WorkflowJob.id)).group_by(WorkflowJob.status)
        j_counts = dict((await session.execute(j_query)).all())

        # Total workers
        total_workers = sum(w_counts.values())
        active_workers = w_counts.get("busy", 0) + w_counts.get("idle", 0)

        # Dead letter jobs
        dlq_count = (await session.execute(select(func.count(DeadLetterJob.id)))).scalar() or 0

    return {
        "infrastructure": {
            "provider": "AWS ECS / Fargate",
            "cluster_name": settings.AWS_ECS_CLUSTER,
            "region": settings.AWS_REGION,
            "s3_bucket": settings.AWS_S3_ARTIFACTS_BUCKET,
            "status": "Healthy",
        },
        "workers": {
            "total_registered": total_workers,
            "active": active_workers,
            "idle": w_counts.get("idle", 0),
            "busy": w_counts.get("busy", 0),
            "unhealthy": w_counts.get("unhealthy", 0),
            "terminated": w_counts.get("terminated", 0),
        },
        "jobs": {
            "queued": j_counts.get("queued", 0),
            "running": j_counts.get("running", 0) + j_counts.get("assigned", 0),
            "paused": j_counts.get("paused", 0),
            "blocked_on_approval": j_counts.get("blocked_on_approval", 0),
            "completed": j_counts.get("completed", 0),
            "failed": j_counts.get("failed", 0),
            "cancelled": j_counts.get("cancelled", 0),
            "dead_letter_queue": dlq_count,
        },
        "cost_governance": {
            "default_project_budget_usd": settings.PROJECT_DEFAULT_BUDGET_USD,
            "vcpu_hourly_rate_usd": settings.WORKER_COST_PER_VCPU_HOUR_USD,
            "memory_gb_hourly_rate_usd": settings.WORKER_COST_PER_GB_HOUR_USD,
        },
    }


@router.post("/recovery")
async def trigger_recovery_check():
    """Manually invoke the orphaned job and dead worker recovery cycle."""
    recovered_jobs = await recovery.recover_orphaned_jobs()
    unhealthy_workers = await recovery.prune_dead_workers()
    return {
        "status": "success",
        "recovered_jobs_count": len(recovered_jobs),
        "recovered_jobs": recovered_jobs,
        "unhealthy_workers_count": len(unhealthy_workers),
        "unhealthy_workers": unhealthy_workers,
    }
