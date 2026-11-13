"""
Dashboard E2E and API Integration Tests.
Verifies all 18 dashboard modules, API contracts, and real-time data flows.
"""

import pytest
from httpx import ASGITransport, AsyncClient
from factory.api.main import app
from factory.core.database import init_db
from factory.orchestrator.master import MasterOrchestrator


@pytest.mark.asyncio
async def test_dashboard_18_modules_api_contracts():
    """Verify backend endpoints serving all 18 dashboard modules."""
    await init_db()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Overview
        r_ov = await client.get("/api/v1/overview/stats")
        assert r_ov.status_code == 200
        stats = r_ov.json()
        assert stats["total_agents"] == 97
        assert "total_projects" in stats
        assert "running_workflows" in stats

        # 2. Agent Management
        r_ag = await client.get("/api/v1/agents")
        assert r_ag.status_code == 200
        assert len(r_ag.json()) == 97

        # 3. Create Project & Analysis
        r_an = await client.post(
            "/api/v1/analyze",
            json={"requirement_text": "E-commerce platform with Stripe and WhatsApp alerts", "platform_target": "fullstack"}
        )
        assert r_an.status_code == 200
        plan = r_an.json()
        assert "Next.js" in plan["technology_stack"]["frontend"]
        assert len(plan["selected_agent_roles"]) > 0

        # Project creation
        r_pr = await client.post(
            "/api/v1/projects",
            json={
                "name": "Dashboard E2E App",
                "requirement_text": "Autonomous CRM and billing dashboard",
                "platform_target": "website",
                "execution_mode": "autonomous"
            }
        )
        assert r_pr.status_code == 201
        project_id = r_pr.json()["project_id"]

        # 4. Project Management
        r_pl = await client.get("/api/v1/projects")
        assert r_pl.status_code == 200
        assert any(p["id"] == project_id for p in r_pl.json())

        # 5. Architecture Viewer
        r_ar = await client.get(f"/api/v1/projects/{project_id}/architecture")
        assert r_ar.status_code == 200
        assert "frontend_stack" in r_ar.json()

        # 6. Task Management
        r_tk = await client.get(f"/api/v1/projects/{project_id}/tasks")
        assert r_tk.status_code == 200

        # 7. GitHub Integration
        r_gh = await client.get(f"/api/v1/projects/{project_id}/github")
        assert r_gh.status_code == 200

        # 8. Meta Developer Center
        r_me = await client.get("/api/v1/meta/status")
        assert r_me.status_code == 200
        assert "supported_products" in r_me.json()

        # 9. API Integrations
        r_in = await client.get("/api/v1/integrations")
        assert r_in.status_code == 200

        # 10. Database Management
        r_db = await client.get("/api/v1/database/status")
        assert r_db.status_code == 200
        assert r_db.json()["connection"] == "healthy"

        # 11. Security Center
        r_sc = await client.get("/api/v1/security/findings")
        assert r_sc.status_code == 200

        # 12. QA Center
        r_qa = await client.get("/api/v1/qa/results")
        assert r_qa.status_code == 200

        # 13. Deployment Center
        r_dp = await client.get("/api/v1/deployments")
        assert r_dp.status_code == 200

        # 14. Cost Management
        r_cs = await client.get("/api/v1/costs")
        assert r_cs.status_code == 200
        assert "total_usd" in r_cs.json()

        # 15. System Settings
        r_st = await client.get("/api/v1/system/settings")
        assert r_st.status_code == 200

        # 16. Audit Logs
        r_au = await client.get("/api/v1/audit-logs")
        assert r_au.status_code == 200
