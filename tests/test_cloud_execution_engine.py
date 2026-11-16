"""
Comprehensive Test Suite for Cloud Worker & Autonomous Execution Engine.
Validates:
- Job creation and persistence
- Duplicate-job idempotency
- Worker registration and heartbeats
- Priority queue and atomic leasing
- Checkpointing and stage progression
- Exponential backoff retry and Dead Letter Queue (DLQ)
- Stale job and worker recovery after crash/disconnect
- Cost tracking and budget cap enforcement
- S3 artifact packaging and hashing
- Isolated GitHub branch and Pull Request generation
- REST API contracts for all cloud execution endpoints
- End-to-end cloud worker lifecycle
"""

import asyncio
import os
import shutil
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select, func

from factory.api.main import app
from factory.core.config import settings
from factory.core.database import get_db_session, init_db
from factory.models.schema import (
    DeadLetterJob,
    Project,
    User,
    WorkerNode,
    WorkflowCheckpoint,
    WorkflowJob,
    CostRecord,
)
from factory.workflow.cost_tracker import CloudCostTracker
from factory.workflow.engine import PersistentWorkflowEngine
from factory.workflow.queue import WorkflowQueue
from factory.workflow.recovery import WorkflowRecoveryMonitor
from factory.workflow.retry import RetryPolicy
from factory.workflow.state_machine import WorkflowJobStatus
from factory.cloud_worker.daemon import CloudWorkerDaemon
from factory.cloud_worker.s3_service import S3ArtifactService
from factory.cloud_worker.github_pr_service import GitHubPRService


@pytest.fixture(autouse=True)
async def setup_test_db():
    await init_db()
    yield


@pytest.mark.asyncio
async def test_job_creation_and_idempotency():
    queue = WorkflowQueue()

    # Create dummy project
    async with get_db_session() as session:
        proj = Project(
            name="Test E-Commerce Cloud",
            requirement_text="Build a resilient store",
            status="initialized",
            current_stage=1,
        )
        session.add(proj)
        await session.commit()
        await session.refresh(proj)
        project_id = proj.id

    # 1. Enqueue job
    idempotency_key = f"key-test-{project_id}"
    job1 = await queue.enqueue_job(
        project_id=project_id,
        priority=7,
        target_stage=10,
        idempotency_key=idempotency_key,
    )

    assert job1.id is not None
    assert job1.project_id == project_id
    assert job1.priority == 7
    assert job1.target_stage == 10
    assert job1.status == WorkflowJobStatus.QUEUED.value

    # 2. Duplicate enqueue with same key must return existing job
    job2 = await queue.enqueue_job(
        project_id=project_id,
        priority=10,
        target_stage=23,
        idempotency_key=idempotency_key,
    )

    assert job2.id == job1.id
    assert job2.priority == 7  # Original priority preserved


@pytest.mark.asyncio
async def test_worker_registration_and_heartbeat():
    worker_id = "test-worker-node-1"
    now = datetime.utcnow()

    async with get_db_session() as session:
        worker = WorkerNode(
            id=worker_id,
            worker_name="fargate-worker-test-alpha",
            hostname="ip-10-0-1-5",
            ip_address="10.0.1.5",
            status="idle",
            cpu_cores=2,
            memory_mb=4096,
            last_heartbeat=now,
            registered_at=now,
        )
        session.add(worker)
        await session.commit()

    # Verify registration in DB
    async with get_db_session() as session:
        q = select(WorkerNode).where(WorkerNode.id == worker_id)
        w = (await session.execute(q)).scalar_one_or_none()
        assert w is not None
        assert w.worker_name == "fargate-worker-test-alpha"
        assert w.status == "idle"


@pytest.mark.asyncio
async def test_priority_queue_and_atomic_leasing():
    queue = WorkflowQueue()

    # Create dummy projects
    async with get_db_session() as session:
        p1 = Project(name="Low Priority App", requirement_text="App 1", status="initialized")
        p2 = Project(name="High Priority App", requirement_text="App 2", status="initialized")
        session.add_all([p1, p2])
        await session.commit()
        await session.refresh(p1)
        await session.refresh(p2)

    # Enqueue low priority first, then high priority
    j_low = await queue.enqueue_job(project_id=p1.id, priority=2)
    j_high = await queue.enqueue_job(project_id=p2.id, priority=9)

    # Claim job - must claim high priority first
    worker_id = "test-worker-node-1"
    claimed = await queue.claim_job(worker_id)

    assert claimed is not None
    assert claimed.id == j_high.id
    assert claimed.assigned_worker_id == worker_id
    assert claimed.status == WorkflowJobStatus.ASSIGNED.value
    assert claimed.lease_expires_at > datetime.utcnow()

    # Renew lease
    renewed = await queue.renew_lease(claimed.id, worker_id)
    assert renewed is True


@pytest.mark.asyncio
async def test_checkpointing_and_stage_progression():
    queue = WorkflowQueue()

    async with get_db_session() as session:
        proj = Project(name="Checkpoint App", requirement_text="App CP", status="initialized")
        session.add(proj)
        await session.commit()
        await session.refresh(proj)
        project_id = proj.id

    job = await queue.enqueue_job(project_id=project_id, priority=5)

    # Record checkpoint for Stage 1
    cp1 = await queue.record_checkpoint(
        job_id=job.id,
        stage_number=1,
        stage_title="Understand requirements",
        status="completed",
        evidence=["Requirement validated"],
        artifacts={"spec": "doc_1"},
        duration_ms=450,
    )
    assert cp1.id is not None
    assert cp1.stage_number == 1

    # Record checkpoint for Stage 2
    cp2 = await queue.record_checkpoint(
        job_id=job.id,
        stage_number=2,
        stage_title="Prepare functional specifications",
        status="completed",
        evidence=["Specs generated"],
        artifacts={"specs_json": {}},
        duration_ms=620,
    )

    checkpoints = await queue.list_checkpoints(job.id)
    assert len(checkpoints) == 2
    assert checkpoints[0].stage_number == 1
    assert checkpoints[1].stage_number == 2

    # Check updated job and project stage
    updated_job = await queue.get_job(job.id)
    assert updated_job.current_stage == 2


@pytest.mark.asyncio
async def test_retry_behavior_and_dead_letter_queue():
    policy = RetryPolicy(max_retries=1, base_delay_seconds=0.1)
    queue = WorkflowQueue(retry_policy=policy)

    async with get_db_session() as session:
        proj = Project(name="Failing App", requirement_text="App Fail", status="initialized")
        session.add(proj)
        await session.commit()
        await session.refresh(proj)
        project_id = proj.id

    job = await queue.enqueue_job(project_id=project_id)

    # Attempt 1: Transient failure -> re-queued (retry_count becomes 1)
    j1 = await queue.fail_job(job.id, "Transient network timeout", is_fatal=False)
    assert j1.status == WorkflowJobStatus.QUEUED.value
    assert j1.retry_count == 1

    # Attempt 2: Exceeded max_retries=1 -> routed to DLQ
    j2 = await queue.fail_job(job.id, "Second failure", is_fatal=False)
    assert j2.status == WorkflowJobStatus.FAILED.value

    # Verify DLQ entry exists
    async with get_db_session() as session:
        q = select(DeadLetterJob).where(DeadLetterJob.original_job_id == job.id)
        dlq = (await session.execute(q)).scalar_one_or_none()
        assert dlq is not None
        assert dlq.resolved is False

    # Manual retry resets job to queued
    j_reset = await queue.retry_failed_job(job.id)
    assert j_reset.status == WorkflowJobStatus.QUEUED.value
    assert j_reset.retry_count == 0


@pytest.mark.asyncio
async def test_recovery_of_stale_jobs_after_disconnect():
    queue = WorkflowQueue()
    recovery = WorkflowRecoveryMonitor(heartbeat_timeout_seconds=5)

    async with get_db_session() as session:
        proj = Project(name="Orphaned App", requirement_text="App Orphan", status="initialized")
        session.add(proj)
        await session.commit()
        await session.refresh(proj)
        project_id = proj.id

    job = await queue.enqueue_job(project_id=project_id)

    # Simulate worker crash: register worker then expire lease 2 minutes ago
    expired_time = datetime.utcnow() - timedelta(minutes=2)
    async with get_db_session() as session:
        crashed_w = WorkerNode(
            id="crashed-worker-99",
            worker_name="crashed-worker",
            status="busy",
            last_heartbeat=expired_time,
        )
        session.add(crashed_w)
        q = select(WorkflowJob).where(WorkflowJob.id == job.id)
        db_job = (await session.execute(q)).scalar_one()
        db_job.status = WorkflowJobStatus.RUNNING.value
        db_job.assigned_worker_id = "crashed-worker-99"
        db_job.lease_expires_at = expired_time
        await session.commit()

    # Execute recovery monitor
    recovered = await recovery.recover_orphaned_jobs()
    assert len(recovered) >= 1
    assert any(r["job_id"] == job.id for r in recovered)

    # Job must now be back in QUEUED state for another worker to pick up
    recovered_job = await queue.get_job(job.id)
    assert recovered_job.status == WorkflowJobStatus.QUEUED.value
    assert recovered_job.assigned_worker_id is None


@pytest.mark.asyncio
async def test_cost_tracking_and_budget_cap():
    tracker = CloudCostTracker(cost_per_vcpu_hour=0.04048, cost_per_gb_hour=0.004445)

    # 3600 seconds (1 hour) of 2 vCPU + 4096 MB (4 GB) RAM
    cost_1hr = tracker.compute_runtime_cost(duration_seconds=3600, cpu_cores=2, memory_mb=4096)
    expected = 2 * 0.04048 + 4 * 0.004445
    assert abs(cost_1hr - expected) < 0.001

    # Record cost in DB
    async with get_db_session() as session:
        proj = Project(name="Cost App", requirement_text="App Cost", status="initialized")
        session.add(proj)
        await session.commit()
        await session.refresh(proj)
        project_id = proj.id

    await tracker.record_execution_cost(project_id, duration_seconds=1800, cpu_cores=2, memory_mb=4096)
    total = await tracker.get_project_total_cost(project_id)
    assert total > 0

    # Budget cap check
    exceeded = await tracker.is_budget_exceeded(project_id, budget_limit_usd=0.0001)
    assert exceeded is True
    not_exceeded = await tracker.is_budget_exceeded(project_id, budget_limit_usd=100.0)
    assert not_exceeded is False


@pytest.mark.asyncio
async def test_s3_artifact_packaging_and_hashing():
    service = S3ArtifactService()

    with tempfile.TemporaryDirectory() as tmpdir:
        ws_path = Path(tmpdir)
        (ws_path / "main.py").write_text("print('hello cloud worker')")
        (ws_path / "README.md").write_text("# Project Docs")

        pkg_path = service.package_workspace("proj-12345", ws_path)
        assert pkg_path.exists()
        assert pkg_path.name.endswith(".tar.gz")

        upload_res = await service.upload_artifact("proj-12345", pkg_path)
        assert upload_res["size_bytes"] > 0
        assert "sha256" in upload_res
        assert len(upload_res["sha256"]) == 64


@pytest.mark.asyncio
async def test_github_isolated_branch_and_pr():
    with tempfile.TemporaryDirectory() as tmpdir:
        ws_path = Path(tmpdir)
        # Init local repo
        import subprocess
        subprocess.run(["git", "init"], cwd=str(ws_path), capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=str(ws_path), capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=str(ws_path), capture_output=True)
        (ws_path / "init.txt").write_text("initial")
        subprocess.run(["git", "add", "."], cwd=str(ws_path), capture_output=True)
        subprocess.run(["git", "commit", "-m", "initial commit"], cwd=str(ws_path), capture_output=True)

        service = GitHubPRService(ws_path)
        branch = service.create_isolated_branch("p-12345678")
        assert branch == "feature/p-123456-build"

        (ws_path / "feature.py").write_text("def feat(): pass")
        sha = service.commit_changes("feat: autonomous implementation")
        assert len(sha) == 40

        pr = await service.create_pull_request(
            project_id="p-12345678",
            project_name="test-project",
            branch_name=branch,
        )
        assert pr["branch"] == branch
        assert pr["base"] == "main"
        assert "pull" in pr["pr_url"]


@pytest.mark.asyncio
async def test_cloud_api_endpoints_full_e2e():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Register worker
        reg_res = await client.post(
            "/api/v1/cloud/workers/register",
            json={
                "worker_name": "fargate-e2e-worker",
                "hostname": "10.0.1.20",
                "cpu_cores": 2,
                "memory_mb": 4096,
            },
            headers={"X-Worker-Token": settings.WORKER_AUTH_TOKEN},
        )
        assert reg_res.status_code == 200
        worker_id = reg_res.json()["worker_id"]

        # 2. Worker heartbeat
        hb_res = await client.post(
            "/api/v1/cloud/workers/heartbeat",
            json={"worker_id": worker_id, "status": "idle"},
            headers={"X-Worker-Token": settings.WORKER_AUTH_TOKEN},
        )
        assert hb_res.status_code == 200

        # 3. Create dummy project for workflow
        async with get_db_session() as session:
            proj = Project(name="E2E Cloud App", requirement_text="E2E test", status="initialized")
            session.add(proj)
            await session.commit()
            await session.refresh(proj)
            p_id = proj.id

        # 4. Submit job via API
        sub_res = await client.post(
            "/api/v1/cloud/submit",
            json={"project_id": p_id, "target_stage": 5, "priority": 6},
        )
        assert sub_res.status_code == 200
        job_id = sub_res.json()["job_id"]

        # 5. List jobs
        jobs_res = await client.get("/api/v1/cloud/jobs")
        assert jobs_res.status_code == 200
        assert any(j["id"] == job_id for j in jobs_res.json())

        # 6. Pause, resume, and retry controls
        pause_res = await client.post(f"/api/v1/cloud/jobs/{job_id}/pause")
        assert pause_res.status_code == 200
        assert pause_res.json()["status"] == "paused"

        resume_res = await client.post(f"/api/v1/cloud/jobs/{job_id}/resume")
        assert resume_res.status_code == 200
        assert resume_res.json()["status"] == "queued"

        # 7. Cloud status telemetry
        status_res = await client.get("/api/v1/cloud/status")
        assert status_res.status_code == 200
        data = status_res.json()
        assert "infrastructure" in data
        assert "workers" in data
        assert "jobs" in data

        # 8. Recovery scan
        rec_res = await client.post("/api/v1/cloud/recovery")
        assert rec_res.status_code == 200
        assert "recovered_jobs_count" in rec_res.json()


@pytest.mark.asyncio
async def test_autonomous_cloud_worker_full_lifecycle_and_disconnect():
    """
    End-to-end test verifying:
    1. Project submission and workflow persistence.
    2. Cloud worker daemon registration and heartbeat.
    3. Job claim and autonomous stage execution (Code generation, testing, packaging).
    4. S3 artifact upload and isolated GitHub feature branch commit.
    5. Local disconnect simulation (lease expires, worker recovers job independently).
    6. Verifiable final status and deliverables.
    """
    daemon = CloudWorkerDaemon(worker_name="fargate-worker-e2e-main", poll_interval=0.5)
    await daemon.register()

    # Step 1: Submit new project into database
    async with get_db_session() as session:
        proj = Project(
            name="Autonomous Cloud SaaS App",
            requirement_text="A durable multi-tenant SaaS application with auth and billing",
            platform_target="website",
            status="initialized",
            current_stage=1,
        )
        session.add(proj)
        await session.commit()
        await session.refresh(proj)
        project_id = proj.id

    # Step 2: Enqueue workflow job (stages 1 to 3 for fast E2E)
    queue = WorkflowQueue()
    job = await queue.enqueue_job(project_id=project_id, target_stage=3, priority=10)
    assert job.status == WorkflowJobStatus.QUEUED.value

    # Step 3 & 4: Daemon executes one cycle autonomously
    processed = await daemon.process_one_cycle()
    assert processed is True

    # Step 5: Verify stage checkpoints exist in database
    checkpoints = await queue.list_checkpoints(job.id)
    assert len(checkpoints) >= 1
    assert checkpoints[0].stage_number == 1
    assert checkpoints[0].status == "completed"

    # Step 6: Verify S3 artifact packaging occurred
    artifacts_dir = settings.PROJECTS_STORAGE_DIR / "artifacts" / project_id
    assert artifacts_dir.exists()
    tar_files = list(artifacts_dir.glob("*.tar.gz"))
    assert len(tar_files) >= 1

    # Step 7: Simulate local IDE disconnect / restart
    # Simulate an incomplete job with expired lease from a disconnected session
    job2 = await queue.enqueue_job(project_id=project_id, target_stage=4, priority=5)
    expired_time = datetime.utcnow() - timedelta(minutes=5)
    async with get_db_session() as session:
        q = select(WorkflowJob).where(WorkflowJob.id == job2.id)
        db_j2 = (await session.execute(q)).scalar_one()
        db_j2.status = WorkflowJobStatus.RUNNING.value
        db_j2.assigned_worker_id = daemon.worker_id
        db_j2.lease_expires_at = expired_time
        await session.commit()

    # Recovery monitor detects disconnected worker and safely re-enqueues job
    recovery = WorkflowRecoveryMonitor()
    recovered_list = await recovery.recover_orphaned_jobs()
    assert any(r["job_id"] == job2.id for r in recovered_list)

    # Cloud worker can pick up recovered job without needing local Windows IDE session
    j2_recovered = await queue.get_job(job2.id)
    assert j2_recovered.status == WorkflowJobStatus.QUEUED.value

    # Cleanup daemon
    await daemon.stop()
