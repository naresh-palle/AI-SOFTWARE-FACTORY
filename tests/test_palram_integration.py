"""
PALRAM AI soft-launch integration tests.

Covers website-to-factory authentication (invite-only → admin approve → login)
and tenant-scoped project creation against the existing FastAPI surface.
"""

from datetime import datetime, timezone

import pytest
from httpx import ASGITransport, AsyncClient

from factory.api.main import app
from factory.core.config import settings
from factory.core.database import init_db


@pytest.fixture(autouse=True)
async def setup_db():
    await init_db()


@pytest.mark.asyncio
async def test_invite_only_register_approve_login_and_create_project(monkeypatch):
    """Soft-launch path: pending registration, admin approve, login, create project."""
    monkeypatch.setattr(settings, "REGISTRATION_MODE", "invite_only")
    monkeypatch.setattr(settings, "FACTORY_API_TOKEN", "test-operator-token")
    monkeypatch.setattr(settings, "ALLOW_TENANT_HEADER_AUTH", False)

    email = f"studio_{datetime.now(timezone.utc).timestamp()}@palramai.test"
    password = "SoftLaunchPass123!"
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1) Health (public)
        health = await client.get("/health")
        assert health.status_code == 200
        assert health.json()["status"] == "healthy"

        # 2) Invite-only registration — no JWT issued
        reg = await client.post(
            "/api/v1/saas/auth/register",
            json={
                "name": "Studio Founder",
                "email": email,
                "password": password,
                "organization_name": "PALRAM Soft Launch Co",
                "plan_tier": "starter",
            },
        )
        assert reg.status_code == 200, reg.text
        reg_body = reg.json()
        assert reg_body["registration_status"] == "pending_approval"
        assert "access_token" not in reg_body
        assert "token" not in reg_body
        tenant_id = reg_body["tenant"]["id"]

        # 3) Login blocked until approval
        denied = await client.post(
            "/api/v1/saas/auth/login",
            json={"email": email, "password": password},
        )
        assert denied.status_code == 401
        assert "pending" in denied.json()["detail"].lower()

        # 4) Admin endpoints require auth
        unauth_admin = await client.get("/api/v1/saas/admin/tenants")
        assert unauth_admin.status_code == 401

        admin_headers = {"Authorization": "Bearer test-operator-token"}
        approve = await client.post(
            f"/api/v1/saas/admin/tenants/{tenant_id}/approve",
            headers=admin_headers,
        )
        assert approve.status_code == 200, approve.text
        assert approve.json()["status"] == "active"

        # 5) Login after approval
        login = await client.post(
            "/api/v1/saas/auth/login",
            json={"email": email, "password": password},
        )
        assert login.status_code == 200, login.text
        token = login.json()["access_token"]
        customer_headers = {"Authorization": f"Bearer {token}"}

        me = await client.get("/api/v1/saas/auth/me", headers=customer_headers)
        assert me.status_code == 200
        assert me.json()["tenant"]["id"] == tenant_id

        # 6) Create project with customer JWT (tenant-scoped)
        created = await client.post(
            "/api/v1/projects",
            headers=customer_headers,
            json={
                "name": "Soft Launch Demo App",
                "requirement_text": "Build a simple task tracker with user auth and REST API.",
                "platform_target": "fullstack",
            },
        )
        assert created.status_code == 201, created.text
        project_id = created.json()["project_id"]

        listed = await client.get("/api/v1/projects", headers=customer_headers)
        assert listed.status_code == 200
        ids = {p["id"] for p in listed.json()}
        assert project_id in ids
        assert all(p.get("tenant_id") in (None, tenant_id) for p in listed.json())


@pytest.mark.asyncio
async def test_cors_allowlist_includes_palram_origins():
    from factory.core.config import cors_allow_origins

    origins = cors_allow_origins(settings)
    assert "https://palramai.in" in origins or any("palramai.in" in o for o in origins)
    assert "*" not in origins


@pytest.mark.asyncio
async def test_open_registration_still_issues_token(monkeypatch):
    monkeypatch.setattr(settings, "REGISTRATION_MODE", "open")
    email = f"open_{datetime.now(timezone.utc).timestamp()}@palramai.test"
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        reg = await client.post(
            "/api/v1/saas/auth/register",
            json={
                "name": "Open User",
                "email": email,
                "password": "OpenModePass123!",
                "organization_name": "Open Mode Org",
            },
        )
        assert reg.status_code == 200, reg.text
        body = reg.json()
        assert body["registration_status"] == "active"
        assert body.get("access_token")
