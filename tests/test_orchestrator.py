"""
Tests for Master Orchestrator, Stage Execution, and Approval Checkpoints.
"""

import json

import pytest
from sqlalchemy import func, select

from factory.core.config import settings
from factory.core.database import get_db_session, init_db
from factory.models.schema import ApprovalRecord
from factory.orchestrator.master import MasterOrchestrator, project_workspace


@pytest.mark.asyncio
async def test_orchestrator_initialization_and_stages():
    await init_db()
    orchestrator = MasterOrchestrator()

    # 1. Initialize Project
    project = await orchestrator.initialize_project(
        name="Auto CRM",
        requirement_text="Build a customer relationship portal with email notifications and user auth.",
        platform_target="website",
        execution_mode="autonomous"
    )
    assert project.id is not None
    assert project.current_stage == 1

    # 2. Execute Stage 1
    s1_res = await orchestrator.execute_stage(project.id, 1)
    assert s1_res.status == "completed"
    assert len(s1_res.execution_evidence) > 0

    # 3. Execute Stage 2
    s2_res = await orchestrator.execute_stage(project.id, 2)
    assert s2_res.status == "completed"
    assert len(s2_res.execution_evidence) > 0

    # 4. Check State
    state = await orchestrator.get_orchestration_state(project.id)
    assert state.stages[1].status == "completed"
    assert state.stages[2].status == "completed"


@pytest.mark.asyncio
async def test_orchestrator_approval_checkpoint():
    await init_db()
    orchestrator = MasterOrchestrator()

    project = await orchestrator.initialize_project(
        name="Prod Deployment Test",
        requirement_text="Standard web application requiring production approval gate.",
        platform_target="website",
        execution_mode="autonomous"
    )

    # Trigger stage 20 (Production Approval Gate)
    s20_res = await orchestrator.execute_stage(project.id, 20)
    assert s20_res.status == "blocked_on_approval"
    assert "Production deployment gate" in str(s20_res.error_message)

    state = await orchestrator.get_orchestration_state(project.id)
    assert len(state.pending_approvals) > 0
    assert state.pending_approvals[0]["stage"] == 20
    assert state.stages[20].status == "blocked_on_approval"


@pytest.mark.asyncio
async def test_stage_evidence_is_real_and_tests_are_not_fabricated():
    await init_db()
    orchestrator = MasterOrchestrator()
    project = await orchestrator.initialize_project(
        name="Evidence",
        requirement_text="Record the requirement without pretending work finished.",
        platform_target="website",
    )
    stage_one = await orchestrator.execute_stage(project.id, 1)
    spec_path = settings.PROJECTS_STORAGE_DIR / project.id / "01_requirement_analysis.json"
    payload = json.loads(spec_path.read_text(encoding="utf-8"))
    assert payload["status"] == "recorded"
    assert payload["project_id"] == project.id
    assert stage_one.execution_evidence[0].startswith("File created: 01_requirement_analysis.json (sha256=")
    assert len(stage_one.execution_evidence[0].split("sha256=", 1)[1].rstrip(")")) == 64

    testing = await orchestrator.execute_stage(project.id, 15)
    report = json.loads((settings.PROJECTS_STORAGE_DIR / project.id / "test_report.json").read_text(encoding="utf-8"))
    assert report["status"] == "not_run"
    assert report["passed"] == 0
    assert "10/10" not in " ".join(testing.execution_evidence)

    repository = await orchestrator.execute_stage(project.id, 7)
    assert repository.status == "completed"
    assert (settings.PROJECTS_STORAGE_DIR / project.id / ".git" / "HEAD").is_file()
    evidence = " ".join(repository.execution_evidence)
    assert "No GitHub remote was created" in evidence
    assert "github.com" not in evidence.lower()


@pytest.mark.asyncio
async def test_production_approval_can_be_approved_once():
    await init_db()
    orchestrator = MasterOrchestrator()
    project = await orchestrator.initialize_project(
        name="Approval Resume",
        requirement_text="A website that stops at the production gate until a person approves it.",
        platform_target="website",
    )
    first = await orchestrator.execute_stage(project.id, 20)
    second = await orchestrator.execute_stage(project.id, 20)
    assert first.status == "blocked_on_approval"
    assert second.status == "blocked_on_approval"

    async with get_db_session() as session:
        count = await session.scalar(select(func.count()).select_from(ApprovalRecord).where(ApprovalRecord.project_id == project.id))
        assert count == 1
        record = (await session.execute(select(ApprovalRecord).where(ApprovalRecord.project_id == project.id))).scalar_one()
        record.status = "approved"

    resumed = await orchestrator.execute_stage(project.id, 20)
    assert resumed.status == "completed"
    state = await orchestrator.get_orchestration_state(project.id)
    assert state.current_stage == 21
    assert state.pending_approvals == []


@pytest.mark.asyncio
async def test_rejected_production_approval_fails_closed():
    await init_db()
    orchestrator = MasterOrchestrator()
    project = await orchestrator.initialize_project(
        name="Approval Reject",
        requirement_text="A website whose production release is rejected.",
        platform_target="website",
    )
    await orchestrator.execute_stage(project.id, 20)
    async with get_db_session() as session:
        record = (await session.execute(select(ApprovalRecord).where(ApprovalRecord.project_id == project.id))).scalar_one()
        record.status = "rejected"

    failed = await orchestrator.execute_stage(project.id, 20)
    assert failed.status == "failed"
    state = await orchestrator.get_orchestration_state(project.id)
    assert state.is_failed is True
    again = await orchestrator.execute_stage(project.id, 20)
    assert again.status == "failed"
    async with get_db_session() as session:
        count = await session.scalar(select(func.count()).select_from(ApprovalRecord).where(ApprovalRecord.project_id == project.id))
        assert count == 1


def test_project_workspace_rejects_path_escape():
    with pytest.raises(ValueError):
        project_workspace("..")
    with pytest.raises(ValueError):
        project_workspace("../escape")


@pytest.mark.asyncio
async def test_unknown_stage_is_rejected():
    await init_db()
    orchestrator = MasterOrchestrator()
    project = await orchestrator.initialize_project(
        name="Bad Stage",
        requirement_text="Reject a stage number outside the defined workflow.",
        platform_target="website",
    )
    with pytest.raises(ValueError):
        await orchestrator.execute_stage(project.id, 99)
