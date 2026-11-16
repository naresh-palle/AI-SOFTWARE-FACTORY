"""
Durable Workflow Queue and Job Manager.
Supports atomic leasing, checkpointing, idempotency, retry/dead-letter, and lifecycle controls.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from sqlalchemy import desc, select, and_, or_

from factory.core.config import settings
from factory.core.database import get_db_session
from factory.core.logger import logger
from factory.models.schema import (
    DeadLetterJob,
    Project,
    WorkerNode,
    WorkflowCheckpoint,
    WorkflowJob,
)
from factory.workflow.retry import RetryPolicy
from factory.workflow.state_machine import WorkflowJobStatus, can_transition


class WorkflowQueue:
    """Persistent job queue backed by PostgreSQL / SQLite with leasing guarantees."""

    def __init__(self, retry_policy: Optional[RetryPolicy] = None):
        self.retry_policy = retry_policy or RetryPolicy(max_retries=3)

    async def enqueue_job(
        self,
        project_id: str,
        job_type: str = "full_pipeline",
        priority: int = 5,
        target_stage: int = 23,
        idempotency_key: Optional[str] = None,
        timeout_seconds: int = 3600,
    ) -> WorkflowJob:
        """Enqueue a new workflow job idempotently."""
        async with get_db_session() as session:
            # Check idempotency
            if idempotency_key:
                q = select(WorkflowJob).where(WorkflowJob.idempotency_key == idempotency_key)
                existing = (await session.execute(q)).scalar_one_or_none()
                if existing:
                    logger.info(f"WorkflowQueue: Returning idempotent job {existing.id} for key {idempotency_key}")
                    return existing

            # Verify project exists
            p_query = select(Project).where(Project.id == project_id)
            project = (await session.execute(p_query)).scalar_one_or_none()
            if not project:
                raise ValueError(f"Project not found: {project_id}")

            job = WorkflowJob(
                project_id=project_id,
                job_type=job_type,
                status=WorkflowJobStatus.QUEUED.value,
                priority=priority,
                current_stage=project.current_stage or 1,
                target_stage=target_stage,
                timeout_seconds=timeout_seconds,
                idempotency_key=idempotency_key,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            session.add(job)
            await session.commit()
            await session.refresh(job)

            logger.info(f"WorkflowQueue: Enqueued job {job.id} for project {project_id} (priority={priority})")
            return job

    async def claim_job(
        self,
        worker_id: str,
        supported_types: Optional[List[str]] = None,
    ) -> Optional[WorkflowJob]:
        """Atomically claim the highest-priority pending or expired-lease job for a worker."""
        now = datetime.utcnow()
        lease_duration = timedelta(seconds=settings.WORKER_LEASE_DURATION_SECONDS)

        async with get_db_session() as session:
            # Find candidate jobs: either queued or running/assigned with expired lease
            conditions = [
                WorkflowJob.status == WorkflowJobStatus.QUEUED.value,
                and_(
                    WorkflowJob.status.in_([
                        WorkflowJobStatus.ASSIGNED.value,
                        WorkflowJobStatus.RUNNING.value,
                    ]),
                    WorkflowJob.lease_expires_at.isnot(None),
                    WorkflowJob.lease_expires_at < now,
                ),
            ]
            q = (
                select(WorkflowJob)
                .where(or_(*conditions))
                .order_by(desc(WorkflowJob.priority), WorkflowJob.created_at)
                .limit(1)
            )
            job = (await session.execute(q)).scalar_one_or_none()

            if not job:
                return None

            job.status = WorkflowJobStatus.ASSIGNED.value
            job.assigned_worker_id = worker_id
            job.lease_expires_at = now + lease_duration
            if not job.started_at:
                job.started_at = now
            job.updated_at = now

            # Update worker current job
            w_query = select(WorkerNode).where(WorkerNode.id == worker_id)
            worker = (await session.execute(w_query)).scalar_one_or_none()
            if worker:
                worker.status = "busy"
                worker.current_job_id = job.id
                worker.last_heartbeat = now

            await session.commit()
            await session.refresh(job)

            logger.info(f"WorkflowQueue: Worker {worker_id} claimed job {job.id} (project {job.project_id})")
            return job

    async def renew_lease(self, job_id: str, worker_id: str) -> bool:
        """Renew worker lease for an active job."""
        now = datetime.utcnow()
        lease_duration = timedelta(seconds=settings.WORKER_LEASE_DURATION_SECONDS)

        async with get_db_session() as session:
            q = select(WorkflowJob).where(
                and_(
                    WorkflowJob.id == job_id,
                    WorkflowJob.assigned_worker_id == worker_id,
                    WorkflowJob.status.in_([
                        WorkflowJobStatus.ASSIGNED.value,
                        WorkflowJobStatus.RUNNING.value,
                    ]),
                )
            )
            job = (await session.execute(q)).scalar_one_or_none()
            if not job:
                return False

            job.lease_expires_at = now + lease_duration
            job.updated_at = now
            await session.commit()
            return True

    async def record_checkpoint(
        self,
        job_id: str,
        stage_number: int,
        stage_title: str,
        status: str,
        evidence: Optional[List[str]] = None,
        artifacts: Optional[Dict[str, Any]] = None,
        duration_ms: int = 0,
    ) -> WorkflowCheckpoint:
        """Persist stage execution checkpoint and update job progression."""
        now = datetime.utcnow()
        async with get_db_session() as session:
            job_q = select(WorkflowJob).where(WorkflowJob.id == job_id)
            job = (await session.execute(job_q)).scalar_one_or_none()
            if not job:
                raise ValueError(f"Job not found: {job_id}")

            checkpoint = WorkflowCheckpoint(
                job_id=job_id,
                project_id=job.project_id,
                stage_number=stage_number,
                stage_title=stage_title,
                status=status,
                evidence_json=evidence or [],
                artifacts_json=artifacts or {},
                duration_ms=duration_ms,
                created_at=now,
            )
            session.add(checkpoint)

            # Update job state
            job.status = (
                WorkflowJobStatus.BLOCKED_ON_APPROVAL.value
                if status == "blocked_on_approval"
                else WorkflowJobStatus.RUNNING.value
            )
            job.current_stage = stage_number
            job.checkpoint_data = {
                "last_completed_stage": stage_number,
                "last_stage_title": stage_title,
                "status": status,
                "timestamp": now.isoformat(),
            }
            job.updated_at = now

            # Sync project stage
            proj_q = select(Project).where(Project.id == job.project_id)
            project = (await session.execute(proj_q)).scalar_one_or_none()
            if project:
                project.current_stage = stage_number
                project.status = (
                    "awaiting_approval"
                    if status == "blocked_on_approval"
                    else "in_progress"
                )
                project.updated_at = now

            await session.commit()
            await session.refresh(checkpoint)
            logger.info(f"WorkflowQueue: Checkpoint recorded for job {job_id} at stage {stage_number} ({status})")
            return checkpoint

    async def complete_job(
        self,
        job_id: str,
        worker_id: str,
        final_data: Optional[Dict[str, Any]] = None,
    ) -> WorkflowJob:
        """Mark workflow job as successfully completed."""
        now = datetime.utcnow()
        async with get_db_session() as session:
            q = select(WorkflowJob).where(WorkflowJob.id == job_id)
            job = (await session.execute(q)).scalar_one_or_none()
            if not job:
                raise ValueError(f"Job not found: {job_id}")

            job.status = WorkflowJobStatus.COMPLETED.value
            job.completed_at = now
            job.lease_expires_at = None
            job.assigned_worker_id = None
            job.updated_at = now

            # Update project status
            proj_q = select(Project).where(Project.id == job.project_id)
            project = (await session.execute(proj_q)).scalar_one_or_none()
            if project:
                project.status = "completed"
                project.updated_at = now

            # Free worker
            w_q = select(WorkerNode).where(WorkerNode.id == worker_id)
            worker = (await session.execute(w_q)).scalar_one_or_none()
            if worker:
                worker.status = "idle"
                worker.current_job_id = None
                worker.total_jobs_completed = (worker.total_jobs_completed or 0) + 1
                worker.last_heartbeat = now

            await session.commit()
            await session.refresh(job)
            logger.info(f"WorkflowQueue: Job {job_id} marked COMPLETED")
            return job

    async def fail_job(
        self,
        job_id: str,
        error_message: str,
        is_fatal: bool = False,
    ) -> WorkflowJob:
        """Handle job failure with exponential backoff retry or dead-letter queue routing."""
        now = datetime.utcnow()
        async with get_db_session() as session:
            q = select(WorkflowJob).where(WorkflowJob.id == job_id)
            job = (await session.execute(q)).scalar_one_or_none()
            if not job:
                raise ValueError(f"Job not found: {job_id}")

            can_retry = not is_fatal and self.retry_policy.should_retry(job.retry_count, error_message)

            if can_retry:
                job.retry_count += 1
                job.status = WorkflowJobStatus.QUEUED.value
                job.assigned_worker_id = None
                job.lease_expires_at = None
                job.error_message = f"Attempt {job.retry_count} failed: {error_message}"
                job.updated_at = now
                logger.warning(
                    f"WorkflowQueue: Re-queueing job {job_id} for retry attempt {job.retry_count} (error: {error_message})"
                )
            else:
                # Terminal Failure: Route to Dead Letter Queue
                job.status = WorkflowJobStatus.FAILED.value
                job.error_message = error_message
                job.completed_at = now
                job.lease_expires_at = None
                job.assigned_worker_id = None
                job.updated_at = now

                # Insert DLQ entry
                dlq = DeadLetterJob(
                    original_job_id=job.id,
                    project_id=job.project_id,
                    failure_reason=error_message,
                    error_details={"retries_exhausted": job.retry_count >= job.max_retries, "is_fatal": is_fatal},
                    attempts_made=job.retry_count,
                    last_attempt_at=now,
                    created_at=now,
                )
                session.add(dlq)

                # Update project
                proj_q = select(Project).where(Project.id == job.project_id)
                project = (await session.execute(proj_q)).scalar_one_or_none()
                if project:
                    project.status = "failed"
                    project.updated_at = now

                logger.error(f"WorkflowQueue: Job {job_id} routed to DLQ (failed permanently: {error_message})")

            # Free assigned worker if any
            if job.assigned_worker_id:
                w_q = select(WorkerNode).where(WorkerNode.id == job.assigned_worker_id)
                worker = (await session.execute(w_q)).scalar_one_or_none()
                if worker:
                    worker.status = "idle"
                    worker.current_job_id = None

            await session.commit()
            await session.refresh(job)
            return job

    async def pause_job(self, job_id: str) -> WorkflowJob:
        """Pause a queued or running workflow job."""
        async with get_db_session() as session:
            q = select(WorkflowJob).where(WorkflowJob.id == job_id)
            job = (await session.execute(q)).scalar_one_or_none()
            if not job:
                raise ValueError(f"Job not found: {job_id}")

            job.status = WorkflowJobStatus.PAUSED.value
            job.assigned_worker_id = None
            job.lease_expires_at = None
            job.updated_at = datetime.utcnow()
            await session.commit()
            await session.refresh(job)
            logger.info(f"WorkflowQueue: Job {job_id} paused")
            return job

    async def resume_job(self, job_id: str) -> WorkflowJob:
        """Resume a paused workflow job."""
        async with get_db_session() as session:
            q = select(WorkflowJob).where(WorkflowJob.id == job_id)
            job = (await session.execute(q)).scalar_one_or_none()
            if not job:
                raise ValueError(f"Job not found: {job_id}")

            job.status = WorkflowJobStatus.QUEUED.value
            job.updated_at = datetime.utcnow()
            await session.commit()
            await session.refresh(job)
            logger.info(f"WorkflowQueue: Job {job_id} resumed into QUEUED state")
            return job

    async def cancel_job(self, job_id: str) -> WorkflowJob:
        """Cancel a workflow job."""
        async with get_db_session() as session:
            q = select(WorkflowJob).where(WorkflowJob.id == job_id)
            job = (await session.execute(q)).scalar_one_or_none()
            if not job:
                raise ValueError(f"Job not found: {job_id}")

            job.status = WorkflowJobStatus.CANCELLED.value
            job.assigned_worker_id = None
            job.lease_expires_at = None
            job.completed_at = datetime.utcnow()
            job.updated_at = datetime.utcnow()

            proj_q = select(Project).where(Project.id == job.project_id)
            project = (await session.execute(proj_q)).scalar_one_or_none()
            if project:
                project.status = "failed"
                project.updated_at = datetime.utcnow()

            await session.commit()
            await session.refresh(job)
            logger.info(f"WorkflowQueue: Job {job_id} cancelled")
            return job

    async def retry_failed_job(self, job_id: str) -> WorkflowJob:
        """Manually retry a failed or DLQ job, resetting retry count."""
        async with get_db_session() as session:
            q = select(WorkflowJob).where(WorkflowJob.id == job_id)
            job = (await session.execute(q)).scalar_one_or_none()
            if not job:
                raise ValueError(f"Job not found: {job_id}")

            job.status = WorkflowJobStatus.QUEUED.value
            job.retry_count = 0
            job.error_message = None
            job.assigned_worker_id = None
            job.lease_expires_at = None
            job.updated_at = datetime.utcnow()

            # Mark DLQ entries as resolved
            dlq_q = select(DeadLetterJob).where(DeadLetterJob.original_job_id == job_id)
            dlqs = (await session.execute(dlq_q)).scalars().all()
            for d in dlqs:
                d.resolved = True

            await session.commit()
            await session.refresh(job)
            logger.info(f"WorkflowQueue: Job {job_id} manually reset and re-queued")
            return job

    async def get_job(self, job_id: str) -> Optional[WorkflowJob]:
        async with get_db_session() as session:
            q = select(WorkflowJob).where(WorkflowJob.id == job_id)
            return (await session.execute(q)).scalar_one_or_none()

    async def list_jobs(
        self,
        project_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
    ) -> List[WorkflowJob]:
        async with get_db_session() as session:
            conditions = []
            if project_id:
                conditions.append(WorkflowJob.project_id == project_id)
            if status:
                conditions.append(WorkflowJob.status == status)

            q = select(WorkflowJob)
            if conditions:
                q = q.where(and_(*conditions))
            q = q.order_by(desc(WorkflowJob.created_at)).limit(limit)
            return list((await session.execute(q)).scalars().all())

    async def list_checkpoints(self, job_id: str) -> List[WorkflowCheckpoint]:
        async with get_db_session() as session:
            q = (
                select(WorkflowCheckpoint)
                .where(WorkflowCheckpoint.job_id == job_id)
                .order_by(WorkflowCheckpoint.stage_number)
            )
            return list((await session.execute(q)).scalars().all())
