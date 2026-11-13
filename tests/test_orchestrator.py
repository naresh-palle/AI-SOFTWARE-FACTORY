"""
Tests for Master Orchestrator, Stage Execution, and Approval Checkpoints.
"""

import pytest
from factory.core.database import init_db
from factory.orchestrator.master import MasterOrchestrator


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
