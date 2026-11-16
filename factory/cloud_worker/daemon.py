"""
Autonomous Cloud Execution Worker Daemon.
Runs persistently on AWS ECS/Fargate or containerized host, independent of local IDE sessions.
"""

import asyncio
import os
import signal
import socket
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from factory.core.config import settings
from factory.core.database import get_db_session, init_db
from factory.core.logger import logger
from factory.models.schema import WorkerNode, WorkflowJob, Project
from factory.orchestrator.master import project_workspace
from factory.workflow.engine import PersistentWorkflowEngine
from factory.workflow.queue import WorkflowQueue
from factory.workflow.recovery import WorkflowRecoveryMonitor
from factory.cloud_worker.s3_service import S3ArtifactService
from factory.cloud_worker.github_pr_service import GitHubPRService


class CloudWorkerDaemon:
    """Independent worker daemon processing durable workflow jobs."""

    def __init__(
        self,
        worker_name: Optional[str] = None,
        cpu_cores: int = settings.WORKER_DEFAULT_CPU_CORES,
        memory_mb: int = settings.WORKER_DEFAULT_MEMORY_MB,
        poll_interval: float = 3.0,
    ):
        self.worker_id = str(uuid.uuid4())
        self.worker_name = worker_name or f"worker-{socket.gethostname()}-{self.worker_id[:6]}"
        self.cpu_cores = cpu_cores
        self.memory_mb = memory_mb
        self.poll_interval = poll_interval
        self.running = False
        self.engine = PersistentWorkflowEngine()
        self.s3_service = S3ArtifactService()
        self._heartbeat_task: Optional[asyncio.Task] = None

    async def register(self) -> str:
        """Register worker in the database registry."""
        await init_db()
        async with get_db_session() as session:
            worker = WorkerNode(
                id=self.worker_id,
                worker_name=self.worker_name,
                hostname=socket.gethostname(),
                ip_address=socket.gethostbyname(socket.gethostname()) if hasattr(socket, "gethostbyname") else "127.0.0.1",
                status="idle",
                cpu_cores=self.cpu_cores,
                memory_mb=self.memory_mb,
                last_heartbeat=datetime.utcnow(),
                registered_at=datetime.utcnow(),
                total_jobs_completed=0,
                tags={"environment": settings.ENVIRONMENT.value, "version": "cloud-v1"},
            )
            session.add(worker)
            await session.commit()

        logger.info(f"CloudWorkerDaemon: Registered worker {self.worker_name} (id={self.worker_id})")
        return self.worker_id

    async def _heartbeat_loop(self):
        """Send regular heartbeats to keep worker lease alive."""
        interval = max(5, settings.WORKER_HEARTBEAT_TIMEOUT_SECONDS // 3)
        while self.running:
            try:
                await asyncio.sleep(interval)
                async with get_db_session() as session:
                    from sqlalchemy import select
                    q = select(WorkerNode).where(WorkerNode.id == self.worker_id)
                    w = (await session.execute(q)).scalar_one_or_none()
                    if w:
                        w.last_heartbeat = datetime.utcnow()
                        await session.commit()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning(f"CloudWorkerDaemon: Heartbeat error: {e}")

    async def process_one_cycle(self) -> bool:
        """Attempt to claim and execute one queued job. Returns True if a job was processed."""
        job = await self.engine.queue.claim_job(self.worker_id)
        if not job:
            return False

        logger.info(f"CloudWorkerDaemon: Worker {self.worker_name} processing job {job.id}")
        try:
            # 1. Execute stage pipeline up to target_stage
            updated_job = await self.engine.execute_job_lifecycle(
                job_id=job.id,
                worker_id=self.worker_id,
                cpu_cores=self.cpu_cores,
                memory_mb=self.memory_mb,
            )

            # 2. If finished or paused on approval, archive artifacts & create PR
            workspace_dir = project_workspace(job.project_id)
            archive_path = self.s3_service.package_workspace(job.project_id, workspace_dir)
            artifact_info = await self.s3_service.upload_artifact(job.project_id, archive_path)

            # 3. Isolated GitHub branch & Pull Request
            github_pr = GitHubPRService(workspace_dir)
            branch = github_pr.create_isolated_branch(job.project_id)
            github_pr.commit_changes(f"chore({job.project_id[:8]}): autonomous build artifacts")
            pr_data = await github_pr.create_pull_request(
                project_id=job.project_id,
                project_name=f"project-{job.project_id[:8]}",
                branch_name=branch,
                artifact_url=artifact_info.get("url"),
            )

            logger.info(
                f"CloudWorkerDaemon: Finished cycle for job {job.id}. Artifact: {artifact_info.get('url')}, PR: {pr_data.get('pr_url')}"
            )
            return True

        except Exception as e:
            logger.exception(f"CloudWorkerDaemon: Error executing job {job.id}: {e}")
            await self.engine.queue.fail_job(job.id, str(e), is_fatal=False)
            return True

    async def start(self):
        """Start daemon execution loop."""
        self.running = True
        await self.register()
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        logger.info(f"CloudWorkerDaemon: Started listening for jobs on {self.worker_name}")

        while self.running:
            try:
                processed = await self.process_one_cycle()
                if not processed:
                    await asyncio.sleep(self.poll_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"CloudWorkerDaemon: Error in main loop: {e}")
                await asyncio.sleep(self.poll_interval)

    async def stop(self):
        """Gracefully stop daemon and deregister."""
        self.running = False
        if self._heartbeat_task:
            self._heartbeat_task.cancel()

        async with get_db_session() as session:
            from sqlalchemy import select
            q = select(WorkerNode).where(WorkerNode.id == self.worker_id)
            w = (await session.execute(q)).scalar_one_or_none()
            if w:
                w.status = "terminated"
                w.current_job_id = None
                await session.commit()

        logger.info(f"CloudWorkerDaemon: Worker {self.worker_name} stopped cleanly")


async def main():
    daemon = CloudWorkerDaemon()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, lambda: asyncio.create_task(daemon.stop()))
        except NotImplementedError:
            pass

    try:
        await daemon.start()
    except (asyncio.CancelledError, KeyboardInterrupt):
        await daemon.stop()


if __name__ == "__main__":
    asyncio.run(main())
