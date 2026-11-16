"""
Unified Workflow Engine Facade.
Coordinates durable queues, stage execution, checkpointing, budget verification, and recovery.
"""

import time
from typing import Any, Dict, List, Optional
from datetime import datetime

from factory.core.logger import logger
from factory.orchestrator.master import MasterOrchestrator
from factory.models.schema import WorkflowJob, WorkflowCheckpoint, DeadLetterJob
from factory.workflow.cost_tracker import CloudCostTracker
from factory.workflow.queue import WorkflowQueue
from factory.workflow.recovery import WorkflowRecoveryMonitor
from factory.workflow.retry import RetryPolicy


class PersistentWorkflowEngine:
    """Master durable workflow engine orchestrating persistent jobs across cloud workers."""

    def __init__(
        self,
        queue: Optional[WorkflowQueue] = None,
        recovery: Optional[WorkflowRecoveryMonitor] = None,
        cost_tracker: Optional[CloudCostTracker] = None,
        orchestrator: Optional[MasterOrchestrator] = None,
    ):
        self.queue = queue or WorkflowQueue()
        self.recovery = recovery or WorkflowRecoveryMonitor()
        self.cost_tracker = cost_tracker or CloudCostTracker()
        self.orchestrator = orchestrator or MasterOrchestrator()

    async def submit_project_workflow(
        self,
        project_id: str,
        target_stage: int = 23,
        priority: int = 5,
        idempotency_key: Optional[str] = None,
    ) -> WorkflowJob:
        """Submit a project into the persistent execution queue."""
        return await self.queue.enqueue_job(
            project_id=project_id,
            job_type="full_pipeline",
            priority=priority,
            target_stage=target_stage,
            idempotency_key=idempotency_key,
        )

    async def execute_job_lifecycle(
        self,
        job_id: str,
        worker_id: str,
        cpu_cores: int = 2,
        memory_mb: int = 4096,
    ) -> WorkflowJob:
        """Execute stages for a claimed job, advancing through checkpoints until completion or approval."""
        job = await self.queue.get_job(job_id)
        if not job:
            raise ValueError(f"Job not found: {job_id}")

        project_id = job.project_id
        start_stage = job.current_stage or 1
        target_stage = job.target_stage or 23

        logger.info(
            f"PersistentWorkflowEngine: Worker {worker_id} executing job {job_id} for project {project_id} (stages {start_stage} -> {target_stage})"
        )

        current = start_stage
        while current <= target_stage:
            # 1. Budget enforcement check
            if await self.cost_tracker.is_budget_exceeded(project_id):
                error_msg = f"Project {project_id} exceeded default budget cap. Execution suspended."
                logger.error(f"PersistentWorkflowEngine: {error_msg}")
                return await self.queue.fail_job(job_id, error_msg, is_fatal=True)

            # 2. Renew lease before starting stage
            await self.queue.renew_lease(job_id, worker_id)

            # 3. Execute stage via MasterOrchestrator
            stage_start_time = time.time()
            try:
                stage_res = await self.orchestrator.execute_stage(project_id, current)
            except Exception as exc:
                duration_ms = int((time.time() - stage_start_time) * 1000)
                logger.exception(f"PersistentWorkflowEngine: Stage {current} failed for job {job_id}")
                return await self.queue.fail_job(job_id, str(exc), is_fatal=False)

            duration_ms = int((time.time() - stage_start_time) * 1000)
            stage_seconds = max(1.0, duration_ms / 1000.0)

            # 4. Record runtime cost
            await self.cost_tracker.record_execution_cost(
                project_id=project_id,
                duration_seconds=stage_seconds,
                cpu_cores=cpu_cores,
                memory_mb=memory_mb,
                stage_name=stage_res.title,
            )

            # 5. Record stage checkpoint
            await self.queue.record_checkpoint(
                job_id=job_id,
                stage_number=current,
                stage_title=stage_res.title,
                status=stage_res.status,
                evidence=stage_res.execution_evidence,
                artifacts=stage_res.artifacts,
                duration_ms=duration_ms,
            )

            # 6. Check stage outcome
            if stage_res.status == "blocked_on_approval":
                logger.info(
                    f"PersistentWorkflowEngine: Job {job_id} paused at stage {current} awaiting human approval."
                )
                break
            elif stage_res.status == "failed":
                error_msg = stage_res.error_message or f"Stage {current} failed during execution"
                return await self.queue.fail_job(job_id, error_msg, is_fatal=False)

            current += 1

        # Check if job reached the target stage successfully
        if current > target_stage:
            return await self.queue.complete_job(job_id, worker_id)

        # Re-fetch updated job state if paused on approval
        return await self.queue.get_job(job_id)
