"""
Tests for Production Security Audit & Defensive Middleware.
Verifies HTTP security headers, rate limiting, request size limits,
and secret leakage detection.
"""

import pytest
from httpx import ASGITransport, AsyncClient
from factory.api.main import app
from factory.core.database import init_db
from factory.core.security_scanner import ProductionSecurityScanner


@pytest.fixture(autouse=True)
async def setup_db():
    await init_db()


@pytest.mark.asyncio
async def test_security_headers_injected():
    """Verify security headers are applied to all API responses."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/v1/saas/subscriptions/plans")
        assert res.status_code == 200
        assert res.headers.get("X-Content-Type-Options") == "nosniff"
        assert res.headers.get("X-Frame-Options") == "DENY"
        assert res.headers.get("X-XSS-Protection") == "1; mode=block"
        assert "Strict-Transport-Security" in res.headers
        assert "Content-Security-Policy" in res.headers


@pytest.mark.asyncio
async def test_rate_limiter_middleware():
    """Verify rate limiter blocks excessive requests."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Auth endpoints have tighter limit of 20
        responses = []
        for _ in range(25):
            r = await client.post("/api/v1/saas/auth/login", json={"email": "fake@test.com", "password": "pass"})
            responses.append(r.status_code)
        
        # At least the later requests must be rate-limited with 429
        assert 429 in responses


@pytest.mark.asyncio
async def test_payload_size_limiter():
    """Verify payload larger than 10MB is rejected with 413."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers = {"Content-Length": str(15 * 1024 * 1024)}  # 15 MB header
        res = await client.post("/api/v1/saas/auth/login", headers=headers, content=b"dummy")
        assert res.status_code == 413
        assert res.json()["error"] == "Payload Too Large"


def test_production_security_scanner():
    """Verify programmatic security scanner detects issues and produces report."""
    report = ProductionSecurityScanner.generate_security_audit_report()
    assert "status" in report
    assert "summary" in report
    assert "findings" in report
    assert report["summary"]["critical_vulnerabilities"] == 0
