"""
Tests for Factory FastAPI Endpoints.
"""

import pytest
from httpx import ASGITransport, AsyncClient
from factory.api.main import app
from factory.core.database import init_db


@pytest.mark.asyncio
async def test_health_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/health")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "healthy"
        assert data["app_name"] == "Autonomous AI Software Development Factory"


@pytest.mark.asyncio
async def test_list_agents_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/v1/agents")
        assert res.status_code == 200
        agents = res.json()
        assert len(agents) == 97


@pytest.mark.asyncio
async def test_analyze_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "requirement_text": "Develop an e-commerce platform with Stripe payments and React Native mobile app",
            "platform_target": "fullstack"
        }
        res = await client.post("/api/v1/analyze", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert "Next.js" in data["technology_stack"]["frontend"]
        assert "React Native" in data["technology_stack"]["mobile"]
        assert len(data["selected_agent_roles"]) > 0


@pytest.mark.asyncio
async def test_create_project_and_get():
    await init_db()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "name": "Integration Test Project",
            "requirement_text": "FastAPI backend and Next.js portal with PostgreSQL.",
            "platform_target": "website",
            "execution_mode": "autonomous"
        }
        res = await client.post("/api/v1/projects", json=payload)
        assert res.status_code == 201
        data = res.json()
        project_id = data["project_id"]
        assert project_id is not None

        # Fetch project status
        get_res = await client.get(f"/api/v1/projects/{project_id}")
        assert get_res.status_code == 200
        state = get_res.json()
        assert state["project_name"] == "Integration Test Project"
        assert state["total_stages"] == 23
