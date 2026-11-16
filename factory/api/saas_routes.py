"""
FastAPI Routes for Multi-Tenant SaaS Platform, Customer Management & Billing Engine.
"""

from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Header, Query, Request, status
from pydantic import BaseModel, Field

from factory.api.auth_deps import extract_saas_auth_context, require_platform_admin
from factory.core.database import get_db_session
from factory.core.logger import logger
from factory.saas.tenant_manager import TenantManager, TenantIsolationError
from factory.saas.auth_manager import CustomerAuthManager
from factory.saas.org_manager import OrganizationManager, PermissionDeniedError
from factory.saas.subscription_manager import SubscriptionManager
from factory.saas.billing_engine import PaymentBillingEngine
from factory.saas.usage_meter import UsageMeteringEngine, QuotaExceededError
from factory.saas.model_provider_manager import ModelCatalogManager, CustomerIntegrationManager
from factory.saas.support_manager import SupportManager, NotificationManager
from factory.saas.admin_console import SaaSAdminConsole

router = APIRouter(prefix="/saas", tags=["Multi-Tenant SaaS Platform"])

# Singletons
tenant_mgr = TenantManager()
auth_mgr = CustomerAuthManager()
org_mgr = OrganizationManager()
sub_mgr = SubscriptionManager()
billing_engine = PaymentBillingEngine()
usage_meter = UsageMeteringEngine()


# ---------------------------------------------------------
# Request Models
# ---------------------------------------------------------

class CustomerRegisterRequest(BaseModel):
    name: str
    email: str
    password: str
    organization_name: str
    plan_tier: str = "free"

class CustomerLoginRequest(BaseModel):
    email: str
    password: str

class CreateOrgRequest(BaseModel):
    name: str

class InviteMemberRequest(BaseModel):
    email: str
    role: str = "developer"

class AcceptInviteRequest(BaseModel):
    token: str
    user_id: str

class SubscribePlanRequest(BaseModel):
    plan_tier: str
    billing_cycle: str = "monthly"

class UpgradePlanRequest(BaseModel):
    new_plan_tier: str
    billing_cycle: Optional[str] = None

class CancelSubscriptionRequest(BaseModel):
    immediately: bool = False

class ProcessPaymentRequest(BaseModel):
    amount: float
    currency: str = "USD"
    gateway: str = "stripe"
    description: Optional[str] = None
    idempotency_key: Optional[str] = None

class RecordUsageRequest(BaseModel):
    metric_name: str
    quantity: float
    unit: str = "count"
    project_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class StoreCredentialRequest(BaseModel):
    provider: str
    credential_type: str
    secret_value: str
    key_identifier: Optional[str] = None
    scopes: Optional[List[str]] = None

class CreateSupportTicketRequest(BaseModel):
    subject: str
    message: str
    category: str = "general"
    priority: str = "medium"

class AddTicketMessageRequest(BaseModel):
    message: str

class SuspendTenantRequest(BaseModel):
    reason: str = "Policy violation"

class OverrideQuotaRequest(BaseModel):
    metric_name: str
    new_limit: int
    hard_limit: bool = True


# ---------------------------------------------------------
# Auth & Tenant Helper
# ---------------------------------------------------------

def _extract_auth_context(authorization: Optional[str], x_tenant_id: Optional[str] = None) -> Dict[str, Any]:
    return extract_saas_auth_context(authorization, x_tenant_id)


# ---------------------------------------------------------
# Customer Authentication & Registration Endpoints
# ---------------------------------------------------------

@router.post("/auth/register")
async def register_customer(payload: CustomerRegisterRequest):
    """Register new customer account with tenant and default organization.

    Soft launch defaults to invite-only: account is created as pending_approval
    until a platform administrator approves the tenant.
    """
    async with get_db_session() as session:
        await sub_mgr.initialize_plans(session)
        await ModelCatalogManager.seed_default_providers(session)

        try:
            result = await auth_mgr.register_customer(
                db=session,
                email=payload.email,
                password=payload.password,
                full_name=payload.name,
                organization_name=payload.organization_name
            )
            pending = result.get("registration_status") == "pending_approval"
            if pending:
                await NotificationManager.create_notification(
                    db=session,
                    tenant_id=result["tenant_id"],
                    title="Registration received — awaiting approval",
                    message=(
                        f"Thanks {payload.name}. Your PALRAM AI Studio access request "
                        "is pending administrator approval."
                    ),
                    severity="info"
                )
                return {
                    "status": "pending_approval",
                    "registration_status": "pending_approval",
                    "message": (
                        "Registration received. An administrator must approve "
                        "your account before you can sign in."
                    ),
                    "user": {
                        "id": result["user_id"],
                        "email": result["email"],
                        "full_name": result["full_name"],
                        "role": result["role"]
                    },
                    "tenant": {
                        "id": result["tenant_id"],
                        "name": payload.organization_name,
                        "status": "pending_approval",
                    },
                    "organization": {
                        "id": result["organization_id"],
                        "name": result["organization_name"]
                    }
                }

            await NotificationManager.create_notification(
                db=session,
                tenant_id=result["tenant_id"],
                title="Welcome to PALRAM AI Studio!",
                message=f"Welcome {payload.name}! Workspace activated under the {payload.plan_tier.upper()} plan.",
                severity="info"
            )
            return {
                "status": "active",
                "registration_status": "active",
                "access_token": result["token"],
                "token": result["token"],
                "user": {
                    "id": result["user_id"],
                    "email": result["email"],
                    "full_name": result["full_name"],
                    "role": result["role"]
                },
                "tenant": {
                    "id": result["tenant_id"],
                    "name": payload.organization_name,
                    "status": "active",
                },
                "organization": {
                    "id": result["organization_id"],
                    "name": result["organization_name"]
                }
            }
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/auth/login")
async def login_customer(payload: CustomerLoginRequest):
    """Authenticate customer with email and password."""
    async with get_db_session() as session:
        try:
            res = await auth_mgr.authenticate_customer(session, payload.email, payload.password)
            return {
                "access_token": res["token"],
                "token": res["token"],
                "user": {
                    "id": res["user_id"],
                    "email": res["email"],
                    "role": res["role"]
                },
                "tenant": {
                    "id": res["tenant_id"]
                }
            }
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.get("/auth/me")
async def get_current_user_profile(
    authorization: Optional[str] = Header(None),
    x_tenant_id: Optional[str] = Header(None)
):
    """Fetch profile and tenant context for current authenticated customer."""
    ctx = _extract_auth_context(authorization, x_tenant_id)
    async with get_db_session() as session:
        tenant = await tenant_mgr.get_tenant(session, ctx["tenant_id"])
        if not tenant:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
        active_sub = await sub_mgr.get_active_subscription(session, tenant.id)

        return {
            "user": {
                "id": ctx.get("user_id"),
                "email": ctx.get("email"),
                "role": ctx.get("role")
            },
            "tenant": {
                "id": tenant.id,
                "name": tenant.name,
                "status": tenant.status
            },
            "subscription": {
                "id": active_sub.id,
                "status": active_sub.status,
                "billing_interval": active_sub.billing_interval
            } if active_sub else None
        }


# ---------------------------------------------------------
# Organizations & Team Management
# ---------------------------------------------------------

@router.post("/organizations")
async def create_organization(
    payload: CreateOrgRequest,
    authorization: Optional[str] = Header(None),
    x_tenant_id: Optional[str] = Header(None)
):
    """Create a new organization within the tenant."""
    ctx = _extract_auth_context(authorization, x_tenant_id)
    async with get_db_session() as session:
        OrganizationManager.assert_permission(ctx.get("role", "developer"), "manage_members")
        org = await org_mgr.create_organization(session, ctx["tenant_id"], payload.name, ctx["user_id"])
        return {"id": org.id, "name": org.name, "tenant_id": org.tenant_id}


@router.get("/organizations/{org_id}/members")
async def list_org_members(
    org_id: str,
    authorization: Optional[str] = Header(None),
    x_tenant_id: Optional[str] = Header(None)
):
    """List members of an organization."""
    ctx = _extract_auth_context(authorization, x_tenant_id)
    async with get_db_session() as session:
        TenantManager.validate_tenant_access(ctx["tenant_id"], ctx["tenant_id"])
        members = await org_mgr.list_members(session, org_id)
        return [
            {
                "id": m.id,
                "user_id": m.user_id,
                "role": m.role,
                "is_active": m.is_active,
                "joined_at": m.joined_at.isoformat() if m.joined_at else None
            }
            for m in members
        ]


@router.post("/organizations/{org_id}/invite")
async def invite_member(
    org_id: str,
    payload: InviteMemberRequest,
    authorization: Optional[str] = Header(None),
    x_tenant_id: Optional[str] = Header(None)
):
    """Invite a new team member with an RBAC role."""
    ctx = _extract_auth_context(authorization, x_tenant_id)
    async with get_db_session() as session:
        OrganizationManager.assert_permission(ctx.get("role", "developer"), "manage_members")
        invitation = await org_mgr.invite_member(
            db=session,
            org_id=org_id,
            email=payload.email,
            role=payload.role,
            invited_by=ctx["user_id"]
        )
        return {
            "id": invitation.id,
            "email": invitation.email,
            "role": invitation.role,
            "token": invitation.token,
            "status": invitation.status
        }


@router.post("/organizations/accept-invite")
async def accept_invitation(payload: AcceptInviteRequest):
    """Accept an organization invitation and activate membership."""
    async with get_db_session() as session:
        try:
            member = await org_mgr.accept_invitation(session, payload.token, payload.user_id)
            return {"status": "accepted", "organization_id": member.organization_id, "role": member.role}
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ---------------------------------------------------------
# Subscriptions & Plans
# ---------------------------------------------------------

@router.get("/subscriptions/plans")
async def list_plans():
    """List all available public subscription plans."""
    async with get_db_session() as session:
        plans = await sub_mgr.list_plans(session)
        return [
            {
                "id": p.id,
                "plan_code": p.plan_code,
                "tier": p.plan_code,
                "name": p.name,
                "description": p.description,
                "price_monthly": p.price_monthly_usd,
                "price_yearly": p.price_yearly_usd,
                "limits": p.limits_json
            }
            for p in plans
        ]


@router.get("/subscriptions/active")
async def get_active_subscription(
    authorization: Optional[str] = Header(None),
    x_tenant_id: Optional[str] = Header(None)
):
    """Fetch tenant's active subscription and entitlement limits."""
    ctx = _extract_auth_context(authorization, x_tenant_id)
    async with get_db_session() as session:
        sub = await sub_mgr.get_active_subscription(session, ctx["tenant_id"])
        if not sub:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No active subscription found")
        plan = await sub_mgr.get_plan(session, sub.plan_id) if hasattr(sub, "plan_id") else None
        return {
            "id": sub.id,
            "tenant_id": sub.tenant_id,
            "status": sub.status,
            "billing_cycle": sub.billing_interval,
            "current_period_end": sub.current_period_end.isoformat() if sub.current_period_end else None,
            "cancel_at_period_end": sub.cancel_at_period_end,
            "plan": {
                "name": plan.name if plan else "Custom Plan",
                "tier": plan.plan_code if plan else "custom",
                "price_monthly": plan.price_monthly_usd if plan else 0.0,
                "limits": plan.limits_json if plan else {}
            }
        }


@router.post("/subscriptions/subscribe")
async def subscribe_plan(
    payload: SubscribePlanRequest,
    authorization: Optional[str] = Header(None),
    x_tenant_id: Optional[str] = Header(None)
):
    """Subscribe tenant to a plan tier."""
    ctx = _extract_auth_context(authorization, x_tenant_id)
    async with get_db_session() as session:
        OrganizationManager.assert_permission(ctx.get("role", "developer"), "manage_billing")
        sub = await sub_mgr.create_subscription(
            db=session,
            tenant_id=ctx["tenant_id"],
            plan_code=payload.plan_tier,
            billing_interval=payload.billing_cycle
        )
        return {"status": "subscribed", "subscription_id": sub.id, "plan_tier": payload.plan_tier}


@router.post("/subscriptions/upgrade")
async def upgrade_plan(
    payload: UpgradePlanRequest,
    authorization: Optional[str] = Header(None),
    x_tenant_id: Optional[str] = Header(None)
):
    """Upgrade or downgrade tenant subscription plan tier."""
    ctx = _extract_auth_context(authorization, x_tenant_id)
    async with get_db_session() as session:
        OrganizationManager.assert_permission(ctx.get("role", "developer"), "manage_billing")
        sub = await sub_mgr.upgrade_subscription(
            db=session,
            tenant_id=ctx["tenant_id"],
            new_plan_code=payload.new_plan_tier
        )
        await NotificationManager.create_notification(
            db=session,
            tenant_id=ctx["tenant_id"],
            title="Subscription Upgraded",
            message=f"Plan successfully updated to {payload.new_plan_tier.upper()}.",
            severity="info"
        )
        return {"status": "upgraded", "subscription_id": sub.id, "plan_tier": payload.new_plan_tier}


@router.post("/subscriptions/cancel")
async def cancel_subscription(
    payload: CancelSubscriptionRequest,
    authorization: Optional[str] = Header(None),
    x_tenant_id: Optional[str] = Header(None)
):
    """Cancel tenant subscription."""
    ctx = _extract_auth_context(authorization, x_tenant_id)
    async with get_db_session() as session:
        OrganizationManager.assert_permission(ctx.get("role", "developer"), "manage_billing")
        sub = await sub_mgr.cancel_subscription(session, ctx["tenant_id"], immediately=payload.immediately)
        return {"status": "cancelled", "subscription_id": sub.id}


# ---------------------------------------------------------
# Billing & Payment Gateway
# ---------------------------------------------------------

@router.post("/billing/process-payment")
async def process_payment(
    payload: ProcessPaymentRequest,
    authorization: Optional[str] = Header(None),
    x_tenant_id: Optional[str] = Header(None)
):
    """Process customer payment transaction via Stripe/Razorpay."""
    ctx = _extract_auth_context(authorization, x_tenant_id)
    async with get_db_session() as session:
        OrganizationManager.assert_permission(ctx.get("role", "developer"), "manage_billing")
        tx = await billing_engine.process_payment(
            db=session,
            tenant_id=ctx["tenant_id"],
            amount=payload.amount,
            currency=payload.currency,
            gateway=payload.gateway,
            description=payload.description,
            idempotency_key=payload.idempotency_key
        )
        return {
            "id": tx.id,
            "status": tx.status,
            "amount": tx.amount,
            "currency": tx.currency
        }


@router.post("/billing/webhooks/{gateway}")
async def handle_payment_webhook(gateway: str, request: Request):
    """Secure webhook handler with HMAC verification and idempotency."""
    raw_body = await request.body()
    signature_header = (
        request.headers.get("Stripe-Signature")
        if gateway == "stripe"
        else request.headers.get("X-Razorpay-Signature")
    )

    try:
        payload_data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    async with get_db_session() as session:
        try:
            event = await billing_engine.handle_webhook_event(
                db=session,
                gateway=gateway,
                raw_payload=raw_body,
                signature_header=signature_header,
                payload_data=payload_data
            )
            return {"status": "processed", "event_id": event.id, "processed": event.processed}
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))


@router.get("/billing/invoices")
async def list_invoices(
    authorization: Optional[str] = Header(None),
    x_tenant_id: Optional[str] = Header(None)
):
    """List customer invoices and receipts."""
    ctx = _extract_auth_context(authorization, x_tenant_id)
    async with get_db_session() as session:
        invoices = await billing_engine.list_invoices(session, ctx["tenant_id"])
        return [
            {
                "id": inv.id,
                "invoice_number": inv.invoice_number,
                "amount": inv.amount_paid,
                "currency": inv.currency,
                "status": inv.status,
                "created_at": inv.created_at.isoformat() if inv.created_at else None
            }
            for inv in invoices
        ]


# ---------------------------------------------------------
# Usage Metering & Quotas
# ---------------------------------------------------------

@router.post("/usage/record")
async def record_usage(
    payload: RecordUsageRequest,
    authorization: Optional[str] = Header(None),
    x_tenant_id: Optional[str] = Header(None)
):
    """Record consumption event and enforce quota limits."""
    ctx = _extract_auth_context(authorization, x_tenant_id)
    async with get_db_session() as session:
        try:
            event = await usage_meter.record_usage(
                db=session,
                tenant_id=ctx["tenant_id"],
                metric_name=payload.metric_name,
                quantity=payload.quantity,
                unit=payload.unit,
                project_id=payload.project_id,
                metadata=payload.metadata
            )
            return {"status": "recorded", "event_id": event.id, "quantity": event.quantity}
        except QuotaExceededError as e:
            await NotificationManager.create_notification(
                db=session,
                tenant_id=ctx["tenant_id"],
                title="Quota Limit Exceeded",
                message=str(e),
                severity="critical"
            )
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(e))


@router.get("/usage/summary")
async def get_usage_summary(
    authorization: Optional[str] = Header(None),
    x_tenant_id: Optional[str] = Header(None)
):
    """Get current billing cycle usage metrics and quota status."""
    ctx = _extract_auth_context(authorization, x_tenant_id)
    async with get_db_session() as session:
        return await usage_meter.get_tenant_usage_summary(session, ctx["tenant_id"])


# ---------------------------------------------------------
# AI Models & Customer Credentials
# ---------------------------------------------------------

@router.get("/providers")
async def list_ai_providers():
    """List available AI model catalog, token pricing, and capability tags."""
    async with get_db_session() as session:
        providers = await ModelCatalogManager.seed_default_providers(session)
        return [
            {
                "id": p.id,
                "provider": p.provider_name,
                "model_name": p.model_name,
                "cost_per_1k_input": p.input_cost_per_1k,
                "cost_per_1k_output": p.output_cost_per_1k,
                "is_active": p.is_active
            }
            for p in providers
        ]


@router.post("/credentials")
async def store_credential(
    payload: StoreCredentialRequest,
    authorization: Optional[str] = Header(None),
    x_tenant_id: Optional[str] = Header(None)
):
    """Store encrypted customer BYOK or integration credential."""
    ctx = _extract_auth_context(authorization, x_tenant_id)
    async with get_db_session() as session:
        cred = await CustomerIntegrationManager.store_credential(
            db=session,
            tenant_id=ctx["tenant_id"],
            provider=payload.provider,
            credential_type=payload.credential_type,
            secret_value=payload.secret_value,
            key_identifier=payload.key_identifier,
            scopes=payload.scopes
        )
        return {"status": "stored", "id": cred.id, "provider": cred.platform}


@router.get("/credentials")
async def list_credentials(
    authorization: Optional[str] = Header(None),
    x_tenant_id: Optional[str] = Header(None)
):
    """List tenant credentials (secrets masked)."""
    ctx = _extract_auth_context(authorization, x_tenant_id)
    async with get_db_session() as session:
        return await CustomerIntegrationManager.list_credentials(session, ctx["tenant_id"])


@router.delete("/credentials/{credential_id}")
async def delete_credential(
    credential_id: str,
    authorization: Optional[str] = Header(None),
    x_tenant_id: Optional[str] = Header(None)
):
    """Remove customer credential."""
    ctx = _extract_auth_context(authorization, x_tenant_id)
    async with get_db_session() as session:
        deleted = await CustomerIntegrationManager.delete_credential(session, ctx["tenant_id"], credential_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Credential not found")
        return {"status": "deleted", "id": credential_id}


# ---------------------------------------------------------
# Customer Support & Notifications
# ---------------------------------------------------------

@router.post("/support/tickets")
async def create_support_ticket(
    payload: CreateSupportTicketRequest,
    authorization: Optional[str] = Header(None),
    x_tenant_id: Optional[str] = Header(None)
):
    """Create customer support ticket."""
    ctx = _extract_auth_context(authorization, x_tenant_id)
    async with get_db_session() as session:
        ticket = await SupportManager.create_ticket(
            db=session,
            tenant_id=ctx["tenant_id"],
            user_id=ctx["user_id"],
            subject=payload.subject,
            initial_message=payload.message,
            category=payload.category,
            priority=payload.priority
        )
        return {"id": ticket.id, "subject": ticket.title, "status": ticket.status}


@router.get("/support/tickets")
async def list_support_tickets(
    status: Optional[str] = None,
    authorization: Optional[str] = Header(None),
    x_tenant_id: Optional[str] = Header(None)
):
    """List tickets for the current tenant."""
    ctx = _extract_auth_context(authorization, x_tenant_id)
    async with get_db_session() as session:
        tickets = await SupportManager.list_tickets(session, ctx["tenant_id"], status)
        return [
            {
                "id": t.id,
                "subject": t.title,
                "status": t.status,
                "priority": t.priority,
                "category": t.category,
                "created_at": t.created_at.isoformat() if t.created_at else None
            }
            for t in tickets
        ]


@router.get("/support/tickets/{ticket_id}")
async def get_ticket_details(
    ticket_id: str,
    authorization: Optional[str] = Header(None),
    x_tenant_id: Optional[str] = Header(None)
):
    """Get support ticket conversation history."""
    ctx = _extract_auth_context(authorization, x_tenant_id)
    async with get_db_session() as session:
        ticket = await SupportManager.get_ticket_details(session, ticket_id, ctx["tenant_id"])
        if not ticket:
            raise HTTPException(status_code=404, detail="Support ticket not found")
        return ticket


@router.post("/support/tickets/{ticket_id}/messages")
async def add_ticket_message(
    ticket_id: str,
    payload: AddTicketMessageRequest,
    authorization: Optional[str] = Header(None),
    x_tenant_id: Optional[str] = Header(None)
):
    """Reply to a support ticket."""
    ctx = _extract_auth_context(authorization, x_tenant_id)
    async with get_db_session() as session:
        msg = await SupportManager.add_message(
            db=session,
            ticket_id=ticket_id,
            sender_id=ctx["user_id"],
            sender_role="customer",
            message=payload.message
        )
        return {"id": msg.id, "ticket_id": msg.ticket_id, "message": msg.message_body}


@router.get("/notifications")
async def list_notifications(
    unread_only: bool = False,
    authorization: Optional[str] = Header(None),
    x_tenant_id: Optional[str] = Header(None)
):
    """List notifications for current tenant."""
    ctx = _extract_auth_context(authorization, x_tenant_id)
    async with get_db_session() as session:
        notifications = await NotificationManager.list_notifications(session, ctx["tenant_id"], unread_only)
        return [
            {
                "id": n.id,
                "title": n.title,
                "message": n.message,
                "severity": n.notification_type,
                "is_read": n.is_read,
                "created_at": n.created_at.isoformat() if n.created_at else None
            }
            for n in notifications
        ]


@router.post("/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    authorization: Optional[str] = Header(None),
    x_tenant_id: Optional[str] = Header(None)
):
    """Mark a notification as read."""
    ctx = _extract_auth_context(authorization, x_tenant_id)
    async with get_db_session() as session:
        ok = await NotificationManager.mark_as_read(session, ctx["tenant_id"], notification_id)
        return {"success": ok}


# ---------------------------------------------------------
# SaaS Administration Console Endpoints
# Protected: FACTORY_API_TOKEN or platform-admin JWT.
# No public admin.palramai.in in soft launch — reuse this API surface.
# ---------------------------------------------------------

@router.get("/admin/metrics")
async def get_admin_metrics(_admin: Dict[str, Any] = Depends(require_platform_admin)):
    """Platform owner analytics: MRR, ARR, tenant counts, gross margin, usage."""
    async with get_db_session() as session:
        return await SaaSAdminConsole.get_platform_metrics(session)


@router.get("/admin/tenants")
async def list_admin_tenants(
    limit: int = 50,
    status: Optional[str] = None,
    _admin: Dict[str, Any] = Depends(require_platform_admin),
):
    """List all tenants across the platform with subscription and usage status."""
    async with get_db_session() as session:
        return await SaaSAdminConsole.list_all_tenants(session, limit, status)


@router.post("/admin/tenants/{tenant_id}/approve")
async def approve_tenant_registration(
    tenant_id: str,
    _admin: Dict[str, Any] = Depends(require_platform_admin),
):
    """Approve an invite-only soft-launch registration request."""
    async with get_db_session() as session:
        try:
            result = await auth_mgr.approve_registration(session, tenant_id)
            await NotificationManager.create_notification(
                db=session,
                tenant_id=tenant_id,
                title="Studio access approved",
                message="Your PALRAM AI Studio account is active. You can sign in now.",
                severity="info",
            )
            return result
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/admin/tenants/{tenant_id}/suspend")
async def suspend_tenant(
    tenant_id: str,
    payload: SuspendTenantRequest,
    _admin: Dict[str, Any] = Depends(require_platform_admin),
):
    """Platform administrator action to suspend an abusive or non-paying tenant."""
    async with get_db_session() as session:
        t = await SaaSAdminConsole.suspend_tenant(session, tenant_id, payload.reason)
        return {"status": "suspended", "tenant_id": t.id, "reason": payload.reason}


@router.post("/admin/tenants/{tenant_id}/reactivate")
async def reactivate_tenant(
    tenant_id: str,
    _admin: Dict[str, Any] = Depends(require_platform_admin),
):
    """Reactivate a suspended tenant."""
    async with get_db_session() as session:
        t = await SaaSAdminConsole.reactivate_tenant(session, tenant_id)
        return {"status": "active", "tenant_id": t.id}


@router.post("/admin/tenants/{tenant_id}/override-quota")
async def override_tenant_quota(
    tenant_id: str,
    payload: OverrideQuotaRequest,
    _admin: Dict[str, Any] = Depends(require_platform_admin),
):
    """Custom quota limit override for enterprise/VIP customers."""
    async with get_db_session() as session:
        policy = await SaaSAdminConsole.override_tenant_quota(
            db=session,
            tenant_id=tenant_id,
            metric_name=payload.metric_name,
            new_limit=payload.new_limit,
            hard_limit=payload.hard_limit
        )
        return {
            "status": "overridden",
            "tenant_id": tenant_id,
            "metric_name": policy.metric_type,
            "limit_value": policy.hard_limit
        }
