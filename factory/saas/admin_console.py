"""
SaaS Administration Console & Platform Analytics
Provides multi-tenant platform monitoring, MRR/ARR, tenant lifecycle management, and financial analytics.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from sqlalchemy import select, func, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from factory.models.schema import (
    Tenant,
    User,
    SubscriptionRecord,
    SubscriptionPlan,
    PaymentTransaction,
    UsageEvent,
    QuotaPolicy
)


class SaaSAdminConsole:
    """Consolidated administrative analytics and tenant operations for platform owners."""

    @staticmethod
    async def get_platform_metrics(db: AsyncSession) -> Dict[str, Any]:
        res_t = await db.execute(select(func.count(Tenant.id)))
        total_tenants = res_t.scalar() or 0

        res_at = await db.execute(select(func.count(Tenant.id)).where(Tenant.status == "active"))
        active_tenants = res_at.scalar() or 0

        res_st = await db.execute(select(func.count(Tenant.id)).where(Tenant.status == "suspended"))
        suspended_tenants = res_st.scalar() or 0

        q_subs = (
            select(SubscriptionRecord, SubscriptionPlan)
            .join(SubscriptionPlan, SubscriptionRecord.plan_id == SubscriptionPlan.id)
            .where(SubscriptionRecord.status == "active")
        )
        active_subs = (await db.execute(q_subs)).all()

        mrr = 0.0
        tier_counts: Dict[str, int] = {}
        for sub, plan in active_subs:
            tier_counts[plan.plan_code] = tier_counts.get(plan.plan_code, 0) + 1
            if sub.billing_interval == "yearly":
                mrr += (plan.price_yearly_usd or 0.0) / 12.0
            else:
                mrr += plan.price_monthly_usd or 0.0

        arr = mrr * 12.0

        q_rev = select(func.sum(PaymentTransaction.amount)).where(
            PaymentTransaction.status == "succeeded"
        )
        res_rev = await db.execute(q_rev)
        completed_payments = res_rev.scalar() or 0.0

        q_tok = select(func.sum(UsageEvent.quantity)).where(
            UsageEvent.metric_type == "ai_tokens"
        )
        res_tok = await db.execute(q_tok)
        total_tokens = res_tok.scalar() or 0.0

        estimated_provider_cost = round((total_tokens / 1000.0) * 0.005, 2)
        gross_margin_pct = (
            round(((completed_payments - estimated_provider_cost) / completed_payments) * 100, 2)
            if completed_payments > 0 else 100.0
        )

        return {
            "tenants": {
                "total": total_tenants,
                "active": active_tenants,
                "suspended": suspended_tenants,
            },
            "subscriptions": {
                "active_count": len(active_subs),
                "by_tier": tier_counts,
                "mrr": round(mrr, 2),
                "arr": round(arr, 2),
                "currency": "USD"
            },
            "financials": {
                "total_revenue_collected": round(float(completed_payments), 2),
                "estimated_ai_cost": estimated_provider_cost,
                "gross_margin_pct": gross_margin_pct
            },
            "usage": {
                "total_ai_tokens": int(total_tokens),
            }
        }

    @staticmethod
    async def list_all_tenants(
        db: AsyncSession,
        limit: int = 50,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        q = select(Tenant)
        if status:
            q = q.where(Tenant.status == status)
        res = await db.execute(q.order_by(desc(Tenant.created_at)).limit(limit))
        tenants = res.scalars().all()

        results = []
        for t in tenants:
            q_sub = (
                select(SubscriptionRecord, SubscriptionPlan)
                .join(SubscriptionPlan, SubscriptionRecord.plan_id == SubscriptionPlan.id)
                .where(
                    and_(
                        SubscriptionRecord.tenant_id == t.id,
                        SubscriptionRecord.status == "active"
                    )
                )
            )
            sub = (await db.execute(q_sub)).first()

            plan_name = sub[1].name if sub else "Community Free"
            plan_tier = sub[1].plan_code if sub else "free"

            q_owner = select(User).where(
                and_(
                    User.tenant_id == t.id,
                    User.role == "owner"
                )
            )
            owner = (await db.execute(q_owner)).scalar_one_or_none()

            now = datetime.utcnow()
            month_start = datetime(now.year, now.month, 1)
            q_usage = select(func.sum(UsageEvent.quantity)).where(
                and_(
                    UsageEvent.tenant_id == t.id,
                    UsageEvent.metric_type == "ai_tokens",
                    UsageEvent.timestamp >= month_start
                )
            )
            token_usage = (await db.execute(q_usage)).scalar() or 0.0

            results.append({
                "id": t.id,
                "name": t.name,
                "status": t.status,
                "plan_name": plan_name,
                "plan_tier": plan_tier,
                "owner_email": owner.email if owner else "Unknown",
                "current_month_tokens": int(token_usage),
                "created_at": t.created_at.isoformat() if t.created_at else None
            })
        return results

    @staticmethod
    async def suspend_tenant(db: AsyncSession, tenant_id: str, reason: str = "Administrative policy violation") -> Tenant:
        q = select(Tenant).where(Tenant.id == tenant_id)
        tenant = (await db.execute(q)).scalar_one_or_none()
        if not tenant:
            raise ValueError(f"Tenant {tenant_id} not found")
        tenant.status = "suspended"
        tenant.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(tenant)
        return tenant

    @staticmethod
    async def reactivate_tenant(db: AsyncSession, tenant_id: str) -> Tenant:
        q = select(Tenant).where(Tenant.id == tenant_id)
        tenant = (await db.execute(q)).scalar_one_or_none()
        if not tenant:
            raise ValueError(f"Tenant {tenant_id} not found")
        tenant.status = "active"
        tenant.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(tenant)
        return tenant

    @staticmethod
    async def override_tenant_quota(
        db: AsyncSession,
        tenant_id: str,
        metric_name: str,
        new_limit: int,
        hard_limit: bool = True
    ) -> QuotaPolicy:
        q = select(QuotaPolicy).where(
            and_(
                QuotaPolicy.tenant_id == tenant_id,
                QuotaPolicy.metric_type == metric_name
            )
        )
        policy = (await db.execute(q)).scalar_one_or_none()

        if policy:
            policy.hard_limit = float(new_limit)
            policy.updated_at = datetime.utcnow()
        else:
            policy = QuotaPolicy(
                id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                metric_type=metric_name,
                hard_limit=float(new_limit),
                soft_alert_threshold=float(new_limit * 0.8),
                reset_period="monthly",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(policy)

        await db.commit()
        await db.refresh(policy)
        return policy
