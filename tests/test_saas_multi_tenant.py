"""
Comprehensive Tests for Phase 9: Multi-Tenant SaaS Platform, Customer Management & Billing Engine.
Verifies multi-tenant data isolation, customer onboarding & PBKDF2 authentication,
8-role RBAC permissions, subscription tiers, Stripe & Razorpay webhook HMAC verification,
idempotency protection, usage metering & quota enforcement, encrypted BYOK credentials,
support ticketing, and SaaS admin console metrics.
"""

import hashlib
import hmac
import json
import pytest
from datetime import datetime, timezone
from httpx import ASGITransport, AsyncClient

from factory.core.database import get_db_session, init_db
from factory.saas.tenant_manager import TenantManager, TenantIsolationError
from factory.saas.auth_manager import CustomerAuthManager
from factory.saas.org_manager import OrganizationManager, PermissionDeniedError
from factory.saas.subscription_manager import SubscriptionManager
from factory.saas.billing_engine import PaymentBillingEngine
from factory.saas.usage_meter import UsageMeteringEngine, QuotaExceededError
from factory.saas.model_provider_manager import ModelCatalogManager, CustomerIntegrationManager
from factory.saas.support_manager import SupportManager, NotificationManager
from factory.saas.admin_console import SaaSAdminConsole
from factory.api.main import app


@pytest.fixture(autouse=True)
async def setup_db():
    await init_db()


@pytest.mark.asyncio
async def test_tenant_creation_and_isolation():
    """Verify tenant provisioning and strict cross-tenant access boundaries."""
    async with get_db_session() as session:
        tenant_mgr = TenantManager()
        tenant_a = await tenant_mgr.create_tenant(session, name="Acme Tech", slug="acme-tech")
        tenant_b = await tenant_mgr.create_tenant(session, name="Beta Corp", slug="beta-corp")

        assert tenant_a.id != tenant_b.id
        assert tenant_a.status == "active"

        # Cross-tenant access validation: accessing tenant_a with tenant_a passes
        TenantManager.validate_tenant_access(tenant_a.id, tenant_a.id)

        # Cross-tenant access validation: accessing tenant_b with tenant_a MUST FAIL
        with pytest.raises(TenantIsolationError):
            TenantManager.validate_tenant_access(tenant_a.id, tenant_b.id)


@pytest.mark.asyncio
async def test_customer_auth_and_pbkdf2():
    """Verify customer registration, PBKDF2 hashing, and JWT tokens."""
    async with get_db_session() as session:
        auth_mgr = CustomerAuthManager()
        sub_mgr = SubscriptionManager()
        await sub_mgr.initialize_plans(session)

        email = f"alice_{datetime.now(timezone.utc).timestamp()}@acmetech.io"
        reg = await auth_mgr.register_customer(
            db=session,
            email=email,
            password="SuperSecretPassword123!",
            full_name="Alice Founder",
            organization_name="Acme Engineering"
        )

        assert "token" in reg
        assert reg["email"] == email

        # Decode and verify JWT
        claims = CustomerAuthManager.decode_jwt_token(reg["token"])
        assert claims["tenant_id"] == reg["tenant_id"]
        assert claims["role"] == "owner"

        # Authenticate with valid password
        auth = await auth_mgr.authenticate_customer(session, email, "SuperSecretPassword123!")
        assert auth is not None
        assert auth["tenant_id"] == reg["tenant_id"]

        # Wrong password raises ValueError
        with pytest.raises(ValueError):
            await auth_mgr.authenticate_customer(session, email, "WrongPassword!")


@pytest.mark.asyncio
async def test_organization_and_rbac_roles():
    """Verify team invitations, 8-role RBAC enforcement, and permission assertions."""
    async with get_db_session() as session:
        auth_mgr = CustomerAuthManager()
        org_mgr = OrganizationManager()

        # Check static RBAC matrix
        assert OrganizationManager.has_permission("owner", "manage_billing") is True
        assert OrganizationManager.has_permission("owner", "create_project") is True
        assert OrganizationManager.has_permission("developer", "manage_billing") is False

        # Asserting billing permission on developer raises PermissionDeniedError
        with pytest.raises(PermissionDeniedError):
            OrganizationManager.assert_permission("developer", "manage_billing")

        # Register owner
        owner_email = f"bob_{datetime.now(timezone.utc).timestamp()}@gamma.io"
        reg = await auth_mgr.register_customer(
            db=session,
            email=owner_email,
            password="SecureBobPassword123!",
            full_name="Bob Manager",
            organization_name="Gamma Labs"
        )
        org_id = reg["organization_id"]
        owner_id = reg["user_id"]

        # Invite member
        dev_email = f"dev_{datetime.now(timezone.utc).timestamp()}@gamma.io"
        inv = await org_mgr.invite_member(
            db=session,
            org_id=org_id,
            email=dev_email,
            role="developer",
            invited_by=owner_id
        )
        assert inv.status == "pending"

        # Accept invitation as new user
        dev_reg = await auth_mgr.register_customer(
            db=session,
            email=dev_email,
            password="DanPassword123!",
            full_name="Dev Dan",
            organization_name="Dan Org"
        )
        member = await org_mgr.accept_invitation(session, inv.token, dev_reg["user_id"])
        assert member.role == "developer"


@pytest.mark.asyncio
async def test_subscription_lifecycle():
    """Verify subscription tiers, upgrades, cancellation, and entitlement checks."""
    async with get_db_session() as session:
        tenant_mgr = TenantManager()
        sub_mgr = SubscriptionManager()

        plans = await sub_mgr.list_plans(session)
        assert len(plans) >= 5

        tenant = await tenant_mgr.create_tenant(session, name="Delta AI", slug="delta-ai")

        # Initial subscription
        sub = await sub_mgr.create_subscription(session, tenant_id=tenant.id, plan_code="starter")
        assert sub.status == "active"

        # Check entitlements
        has_3_projects = await sub_mgr.check_entitlement(session, tenant.id, "max_projects", 3)
        assert has_3_projects is True

        # Upgrade to Professional
        upgraded = await sub_mgr.upgrade_subscription(session, tenant.id, "professional")
        assert upgraded.status == "active"

        # Cancel subscription
        cancelled = await sub_mgr.cancel_subscription(session, tenant.id, immediately=True)
        assert cancelled.status == "canceled"


@pytest.mark.asyncio
async def test_payment_webhooks_and_idempotency():
    """Verify HMAC signature verification, webhook processing, and idempotency protection."""
    async with get_db_session() as session:
        tenant_mgr = TenantManager()
        billing = PaymentBillingEngine()

        tenant = await tenant_mgr.create_tenant(session, name="Epsilon Soft", slug="epsilon-soft")

        # 1. Process payment
        tx = await billing.process_payment(
            db=session,
            tenant_id=tenant.id,
            amount=199.0,
            currency="USD",
            provider="stripe",
            description="Professional Tier Monthly"
        )
        assert tx.status == "succeeded"

        # Check invoice
        invoices = await billing.list_invoices(session, tenant.id)
        assert len(invoices) >= 1

        # 2. Webhook HMAC verification and event processing
        secret = "whsec_test_stripe_secret_key_mock_32b"
        event_id = f"evt_{datetime.now(timezone.utc).timestamp()}"
        payload_dict = {
            "id": event_id,
            "type": "invoice.payment_succeeded",
            "amount": 199.0,
            "customer": tenant.id
        }
        raw_payload = json.dumps(payload_dict).encode()
        sig = hmac.new(secret.encode(), raw_payload, hashlib.sha256).hexdigest()

        event = await billing.handle_webhook_event(
            db=session,
            gateway="stripe",
            raw_payload=raw_payload,
            signature_header=sig,
            payload_data=payload_dict,
            webhook_secret=secret
        )
        assert event.processed is True

        # 3. Duplicate event delivery returns existing record
        dup_event = await billing.handle_webhook_event(
            db=session,
            gateway="stripe",
            raw_payload=raw_payload,
            signature_header=sig,
            payload_data=payload_dict,
            webhook_secret=secret
        )
        assert dup_event.id == event.id


@pytest.mark.asyncio
async def test_usage_metering_and_quota_enforcement():
    """Verify AI token metering, quota policy checks, and QuotaExceededError."""
    async with get_db_session() as session:
        tenant_mgr = TenantManager()
        sub_mgr = SubscriptionManager()
        usage = UsageMeteringEngine()

        tenant = await tenant_mgr.create_tenant(session, name="Zeta Compute", slug="zeta-compute")
        await sub_mgr.create_subscription(session, tenant.id, plan_code="free")

        # Record normal usage
        evt = await usage.record_usage(
            db=session,
            tenant_id=tenant.id,
            metric_name="ai_tokens",
            quantity=5000,
            enforce=True
        )
        assert evt.quantity == 5000

        # Verify summary
        summary = await usage.get_tenant_usage_summary(session, tenant.id)
        assert "ai_tokens" in summary["metrics"]

        # Attempt to exceed quota (exceeding default 1,000,000 limit)
        with pytest.raises(QuotaExceededError):
            await usage.record_usage(
                db=session,
                tenant_id=tenant.id,
                metric_name="ai_tokens",
                quantity=2000000,
                enforce=True
            )


@pytest.mark.asyncio
async def test_byok_encryption_and_model_catalog():
    """Verify reversible AES-Fernet encryption for customer keys and model cost calculation."""
    async with get_db_session() as session:
        tenant_mgr = TenantManager()
        tenant = await tenant_mgr.create_tenant(session, name="Eta Labs", slug="eta-labs")

        providers = await ModelCatalogManager.seed_default_providers(session)
        assert len(providers) >= 6

        cost = await ModelCatalogManager.calculate_cost(session, "gpt-4o", input_tokens=10000, output_tokens=2000)
        assert cost > 0.0

        cred = await CustomerIntegrationManager.store_credential(
            db=session,
            tenant_id=tenant.id,
            provider="openai",
            credential_type="api_key",
            secret_value="sk-proj-super-secret-customer-openai-key-999",
            key_identifier="Prod OpenAI Key"
        )
        assert cred.encrypted_access_token != "sk-proj-super-secret-customer-openai-key-999"

        # Masked
        masked = await CustomerIntegrationManager.get_credential(session, tenant.id, "openai", "api_key", reveal_secret=False)
        assert "secret" not in masked

        # Unmasked
        unmasked = await CustomerIntegrationManager.get_credential(session, tenant.id, "openai", "api_key", reveal_secret=True)
        assert unmasked["secret"] == "sk-proj-super-secret-customer-openai-key-999"


@pytest.mark.asyncio
async def test_support_tickets_and_notifications():
    """Verify customer support ticket thread and notification delivery."""
    async with get_db_session() as session:
        auth_mgr = CustomerAuthManager()
        reg = await auth_mgr.register_customer(
            db=session,
            email=f"theta_{datetime.now(timezone.utc).timestamp()}@theta.io",
            password="SecurePassword123!",
            full_name="Theta User",
            organization_name="Theta Org"
        )
        tenant_id = reg["tenant_id"]
        user_id = reg["user_id"]

        # Notification
        notif = await NotificationManager.create_notification(
            db=session,
            tenant_id=tenant_id,
            title="Payment Success",
            message="Invoice #INV-001 has been settled.",
            severity="info"
        )
        assert notif.is_read is False

        notifications = await NotificationManager.list_notifications(session, tenant_id, unread_only=True)
        assert len(notifications) >= 1

        await NotificationManager.mark_as_read(session, tenant_id, notif.id)
        unread = await NotificationManager.list_notifications(session, tenant_id, unread_only=True)
        assert len(unread) == 0

        # Ticket
        ticket = await SupportManager.create_ticket(
            db=session,
            tenant_id=tenant_id,
            user_id=user_id,
            subject="Request Enterprise Quote",
            initial_message="We need a custom plan with dedicated cloud workers.",
            category="billing",
            priority="high"
        )
        assert ticket.status == "open"

        msg = await SupportManager.add_message(
            db=session,
            ticket_id=ticket.id,
            sender_id=user_id,
            sender_role="support_agent",
            message="We are happy to assist. Our team will contact you shortly."
        )
        assert msg.ticket_id == ticket.id

        details = await SupportManager.get_ticket_details(session, ticket.id, tenant_id)
        assert len(details["messages"]) == 2
        assert details["status"] == "waiting_on_customer"


@pytest.mark.asyncio
async def test_saas_admin_console_metrics():
    """Verify platform-wide MRR, ARR, active tenant tracking, and account suspension."""
    async with get_db_session() as session:
        metrics = await SaaSAdminConsole.get_platform_metrics(session)
        assert "tenants" in metrics
        assert "subscriptions" in metrics
        assert "financials" in metrics
        assert metrics["tenants"]["total"] > 0

        tenants = await SaaSAdminConsole.list_all_tenants(session)
        assert len(tenants) > 0
        first_tenant_id = tenants[0]["id"]

        # Suspend
        suspended = await SaaSAdminConsole.suspend_tenant(session, first_tenant_id, "Non-payment")
        assert suspended.status == "suspended"

        # Reactivate
        reactivated = await SaaSAdminConsole.reactivate_tenant(session, first_tenant_id)
        assert reactivated.status == "active"


@pytest.mark.asyncio
async def test_saas_fastapi_endpoints():
    """Verify SaaS public and authenticated API endpoints via AsyncClient."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Plans catalog endpoint
        res = await client.get("/api/v1/saas/subscriptions/plans")
        assert res.status_code == 200
        plans = res.json()
        assert len(plans) >= 5

        # 2. Register endpoint
        reg_payload = {
            "name": "Integration User",
            "email": f"integ_{datetime.now(timezone.utc).timestamp()}@testcorp.com",
            "password": "PasswordInteg123!",
            "organization_name": "Integ Test Corp",
            "plan_tier": "starter"
        }
        res_reg = await client.post("/api/v1/saas/auth/register", json=reg_payload)
        assert res_reg.status_code == 200
        reg_data = res_reg.json()
        token = reg_data["access_token"]
        tenant_id = reg_data["tenant"]["id"]

        # 3. Auth Me endpoint
        headers = {"Authorization": f"Bearer {token}", "X-Tenant-Id": tenant_id}
        res_me = await client.get("/api/v1/saas/auth/me", headers=headers)
        assert res_me.status_code == 200
        me_data = res_me.json()
        assert me_data["tenant"]["id"] == tenant_id

        # 4. Usage summary endpoint
        res_usage = await client.get("/api/v1/saas/usage/summary", headers=headers)
        assert res_usage.status_code == 200

        # 5. Model providers catalog endpoint
        res_prov = await client.get("/api/v1/saas/providers")
        assert res_prov.status_code == 200
        assert len(res_prov.json()) >= 6

        # 6. Admin metrics endpoint
        res_admin = await client.get("/api/v1/saas/admin/metrics")
        assert res_admin.status_code == 200
        admin_data = res_admin.json()
        assert "mrr" in admin_data["subscriptions"]
