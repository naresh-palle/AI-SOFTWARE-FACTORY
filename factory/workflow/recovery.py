"""
Workflow Failure Recovery and Orphaned Job Monitor.
Detects expired leases, disconnected workers, and resets interrupted jobs for resumption.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any
from sqlalchemy import select, and_, or_

from factory.core.config import settings
from factory.core.database import get_db_session
from factory.core.logger import logger
from factory.models.schema import WorkerNode, WorkflowJob
from factory.workflow.state_machine import WorkflowJobStatus


class WorkflowRecoveryMonitor:
    """Monitors worker health and recovers jobs whose execution lease has expired."""

    def __init__(
        self,
        heartbeat_timeout_seconds: int = settings.WORKER_HEARTBEAT_TIMEOUT_SECONDS,
    ):
        self.heartbeat_timeout = timedelta(seconds=heartbeat_timeout_seconds)

    async def recover_orphaned_jobs(self) -> List[Dict[str, Any]]:
        """Identify jobs with expired leases or dead workers and re-queue them."""
        now = datetime.utcnow()
        recovered = []

        async with get_db_session() as session:
            # Jobs in assigned or running whose lease has expired
            q = select(WorkflowJob).where(
                and_(
                    WorkflowJob.status.in_([
                        WorkflowJobStatus.ASSIGNED.value,
                        WorkflowJobStatus.RUNNING.value,
                    ]),
                    WorkflowJob.lease_expires_at.isnot(None),
                    WorkflowJob.lease_expires_at < now,
                )
            )
            stale_jobs = (await session.execute(q)).scalars().all()

            for job in stale_jobs:
                prev_worker = job.assigned_worker_id
                job.status = WorkflowJobStatus.QUEUED.value
                job.assigned_worker_id = None
                job.lease_expires_at = None
                job.error_message = (
                    f"Recovered from lease expiration (previous worker: {prev_worker}) at {now.isoformat()}"
                )
                job.updated_at = now

                recovered.append({
                    "job_id": job.id,
                    "project_id": job.project_id,
                    "previous_worker": prev_worker,
                    "last_stage": job.current_stage,
                })
                logger.warning(
                    f"WorkflowRecovery: Recovered orphaned job {job.id} for project {job.project_id} (resuming from stage {job.current_stage})"
                )

            await session.commit()

        return recovered

    async def prune_dead_workers(self) -> List[str]:
        """Mark workers with stale heartbeats as unhealthy."""
        now = datetime.utcnow()
        threshold = now - self.heartbeat_timeout
        unhealthy_workers = []

        async with get_db_session() as session:
            q = select(WorkerNode).where(
                and_(
                    WorkerNode.status.in_(["idle", "busy", "registered"]),
                    WorkerNode.last_heartbeat < threshold,
                )
            )
            stale_workers = (await session.execute(q)).scalars().all()

            for w in stale_workers:
                w.status = "unhealthy"
                w.current_job_id = None
                unhealthy_workers.append(w.id)
                logger.warning(f"WorkflowRecovery: Marked worker {w.id} ({w.worker_name}) UNHEALTHY due to missed heartbeats")

            await session.commit()

        return unhealthy_workers
