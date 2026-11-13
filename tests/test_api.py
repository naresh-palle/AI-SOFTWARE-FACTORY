"""
Tests for Factory FastAPI Endpoints.
"""

import pytest
from httpx import ASGITransport, AsyncClient
from factory.api.main import app
from factory.core.config import EnvironmentType, settings
from factory.core.database import init_db
from factory.orchestrator.master import MasterOrchestrator


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


@pytest.mark.asyncio
async def test_cors_does_not_send_credentials_for_wildcard_origins():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/health", headers={"Origin": "https://evil.example"})
        assert res.status_code == 200
        assert res.headers.get("access-control-allow-credentials") != "true"


@pytest.mark.asyncio
async def test_operator_token_is_required_when_configured(monkeypatch):
    monkeypatch.setattr(settings, "FACTORY_API_TOKEN", "test-token-value")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        denied = await client.get("/api/v1/agents")
        assert denied.status_code == 401
        allowed = await client.get(
            "/api/v1/agents",
            headers={"Authorization": "Bearer test-token-value"},
        )
        assert allowed.status_code == 200


@pytest.mark.asyncio
async def test_production_without_operator_token_is_unavailable(monkeypatch):
    monkeypatch.setattr(settings, "ENVIRONMENT", EnvironmentType.PRODUCTION)
    monkeypatch.setattr(settings, "FACTORY_API_TOKEN", None)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/v1/agents")
        assert res.status_code == 503
        health = await client.get("/health")
        assert health.status_code == 200


@pytest.mark.asyncio
async def test_approval_decision_is_recorded_once():
    await init_db()
    orchestrator = MasterOrchestrator()
    project = await orchestrator.initialize_project(
        name="API Approval",
        requirement_text="A website that needs one production decision.",
        platform_target="website",
    )
    await orchestrator.execute_stage(project.id, 20)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        listed = await client.get(f"/api/v1/projects/{project.id}/approvals")
        assert listed.status_code == 200
        approval_id = listed.json()[0]["id"]
        assert listed.json()[0]["decided_at"] is None
        body = {"decision": "approved", "notes": "ship"}
        decided = await client.post(f"/api/v1/approvals/{approval_id}/respond", json=body)
        assert decided.status_code == 200
        refreshed = await client.get(f"/api/v1/projects/{project.id}/approvals")
        assert refreshed.json()[0]["status"] == "approved"
        assert refreshed.json()[0]["decided_at"] is not None
        repeat = await client.post(f"/api/v1/approvals/{approval_id}/respond", json=body)
        assert repeat.status_code == 409
