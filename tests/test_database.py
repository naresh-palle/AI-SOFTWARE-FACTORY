"""
Tests for Database Schema, Initialization, and Entity CRUD.
"""

import pytest
from sqlalchemy import select
from factory.agents.registry import AgentRegistry
from factory.core.database import get_db_session, init_db
from factory.models.schema import AgentRegistryRecord, Project, User


@pytest.mark.asyncio
async def test_init_db_and_sync_agents():
    await init_db()
    async with get_db_session() as session:
        synced = await AgentRegistry.sync_with_db(session)
        # Verify all 97 agents are in the database
        stmt = select(AgentRegistryRecord)
        res = await session.execute(stmt)
        all_agents = res.scalars().all()
        assert len(all_agents) == 97

        # Verify a sample from categories A through J
        role_1 = next((a for a in all_agents if a.role_number == 1), None)
        assert role_1 is not None
        assert role_1.name == "business_analyst"

        role_97 = next((a for a in all_agents if a.role_number == 97), None)
        assert role_97 is not None
        assert role_97.name == "application_maintenance"


@pytest.mark.asyncio
async def test_project_crud():
    await init_db()
    async with get_db_session() as session:
        proj = Project(
            name="Test SaaS App",
            requirement_text="Build a SaaS with payments and auth",
            platform_target="website",
            execution_mode="autonomous",
            status="planning"
        )
        session.add(proj)
        await session.flush()
        proj_id = proj.id

    async with get_db_session() as session:
        stmt = select(Project).where(Project.id == proj_id)
        res = await session.execute(stmt)
        fetched = res.scalar_one_or_none()
        assert fetched is not None
        assert fetched.name == "Test SaaS App"
        assert fetched.current_stage == 1
