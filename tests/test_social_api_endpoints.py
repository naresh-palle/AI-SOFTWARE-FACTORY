"""
FastAPI Endpoint Tests for Social Platform Developer Automation Engine.
"""

import pytest
from httpx import ASGITransport, AsyncClient
from factory.api.main import app
from factory.core.database import init_db


@pytest.mark.asyncio
async def test_social_api_endpoints_e2e():
    await init_db()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Meta Developer Status
        r = await client.get("/api/v1/social/meta/status")
        assert r.status_code == 200
        data = r.json()
        assert "supported_products" in data
        assert len(data["supported_products"]) >= 4

        # 2. Register/Configure Meta App
        r_app = await client.post(
            "/api/v1/social/meta/apps",
            json={
                "app_id": "meta_app_route_test",
                "app_name": "Route Test App",
                "client_secret": "secret_abc",
                "redirect_uris": ["https://example.com/oauth/callback"],
                "enabled_products": ["facebook_login", "instagram_graph"],
            },
        )
        assert r_app.status_code == 200
        assert r_app.json()["app_id"] == "meta_app_route_test"

        # 3. Configure Compliance URLs
        r_comp = await client.post(
            "/api/v1/social/meta/compliance",
            json={
                "app_id": "meta_app_route_test",
                "privacy_policy_url": "https://example.com/privacy",
                "data_deletion_url": "https://example.com/data-deletion",
            },
        )
        assert r_comp.status_code == 200
        assert r_comp.json()["privacy_policy_url"] == "https://example.com/privacy"

        # 4. App Review Submit
        r_rev = await client.post(
            "/api/v1/social/meta/app-review",
            json={
                "app_id": "meta_app_route_test",
                "requested_permissions": ["pages_show_list"],
                "use_case_description": "Social monitoring dashboard",
            },
        )
        assert r_rev.status_code == 200
        assert r_rev.json()["status"] == "submitted"

        # 5. Test Graph API Connectivity
        r_test = await client.post("/api/v1/social/meta/test-connection")
        assert r_test.status_code == 200
        assert r_test.json()["success"] is True

        # 6. OAuth Authorize URL
        r_auth = await client.get("/api/v1/social/oauth/facebook/authorize?tenant_id=t1")
        assert r_auth.status_code == 200
        auth_info = r_auth.json()
        assert "auth_url" in auth_info
        state = auth_info["state"]

        # 7. OAuth Callback
        r_cb = await client.get(f"/api/v1/social/oauth/facebook/callback?code=mock_code_123&state={state}")
        assert r_cb.status_code == 200
        assert r_cb.json()["status"] == "connected"

        # 8. List connections
        r_conns = await client.get("/api/v1/social/connections?tenant_id=t1")
        assert r_conns.status_code == 200
        assert len(r_conns.json()) >= 1

        # 9. Facebook Pages & Publish
        r_pages = await client.get("/api/v1/social/facebook/pages")
        assert r_pages.status_code == 200

        r_pub = await client.post(
            "/api/v1/social/facebook/publish",
            json={"message": "Automated post from factory!"},
        )
        assert r_pub.status_code == 200

        # 10. WhatsApp Templates and Send
        r_wa_tpl = await client.get("/api/v1/social/whatsapp/templates")
        assert r_wa_tpl.status_code == 200

        # Sending without opt-in returns 403 policy violation
        r_wa_fail = await client.post(
            "/api/v1/social/whatsapp/send-template",
            json={
                "phone_number_id": "phone_101",
                "recipient_phone": "+15550199",
                "template_name": "order_confirmation_v1",
                "customer_opt_in_verified": False,
            },
        )
        assert r_wa_fail.status_code == 403

        # Sending with opt-in returns 200 accepted
        r_wa_ok = await client.post(
            "/api/v1/social/whatsapp/send-template",
            json={
                "phone_number_id": "phone_101",
                "recipient_phone": "+15550199",
                "template_name": "order_confirmation_v1",
                "customer_opt_in_verified": True,
            },
        )
        assert r_wa_ok.status_code == 200

        # 11. YouTube & X Endpoints
        r_yt = await client.get("/api/v1/social/youtube/channel")
        assert r_yt.status_code == 200

        r_x = await client.get("/api/v1/social/x/pricing")
        assert r_x.status_code == 200
        assert "basic" in r_x.json()

        # 12. Webhooks: GET challenge verification
        r_chal = await client.get(
            "/api/v1/social/webhooks/meta?hub.mode=subscribe&hub.verify_token=factory_meta_verify_token_secure&hub.challenge=test_challenge_code"
        )
        assert r_chal.status_code == 200
        assert r_chal.text == "test_challenge_code"

        # Webhooks: POST incoming event
        r_hook = await client.post("/api/v1/social/webhooks/whatsapp", json={"entry": []})
        assert r_hook.status_code == 200

        # 13. Audit & Logs
        r_logs = await client.get("/api/v1/social/logs")
        assert r_logs.status_code == 200
        logs_data = r_logs.json()
        assert "integration_logs" in logs_data
        assert "connection_history" in logs_data
