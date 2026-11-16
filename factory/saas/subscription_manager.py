"""
Subscription & Plan Entitlement Manager.
Manages SaaS subscription tiers (Free, Starter, Professional, Business, Enterprise),
plan upgrades, downgrades, cancellations, and entitlement enforcement.
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy import select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from factory.core.logger import logger
from factory.models.schema import SubscriptionPlan, SubscriptionRecord, Tenant, Organization


class SubscriptionManager:
    """Manages subscription lifecycles, plans, quotas, and feature entitlements."""

    DEFAULT_PLANS = [
        {
            "plan_code": "free",
            "name": "Community Free",
            "description": "Essential development workflows for individual builders.",
            "price_monthly_usd": 0.0,
            "price_yearly_usd": 0.0,
            "limits_json": {
                "max_projects": 1,
                "max_monthly_executions": 50,
                "max_tokens": 100000,
                "concurrency_limit": 1,
                "autonomous_deployment_allowed": False,
            },
        },
        {
            "plan_code": "starter",
            "name": "Developer Starter",
            "description": "Standard multi-agent development for growing projects.",
            "price_monthly_usd": 49.0,
            "price_yearly_usd": 490.0,
            "limits_json": {
                "max_projects": 5,
                "max_monthly_executions": 250,
                "max_tokens": 1000000,
                "concurrency_limit": 2,
                "autonomous_deployment_allowed": True,
            },
        },
        {
            "plan_code": "professional",
            "name": "Engineering Professional",
            "description": "Full autonomous factory capabilities with cloud workers.",
            "price_monthly_usd": 199.0,
            "price_yearly_usd": 1990.0,
            "limits_json": {
                "max_projects": 20,
                "max_monthly_executions": 1000,
                "max_tokens": 5000000,
                "concurrency_limit": 5,
                "autonomous_deployment_allowed": True,
            },
        },
        {
            "plan_code": "business",
            "name": "Autonomous Business",
            "description": "High-concurrency multi-user team platform with advanced integrations.",
            "price_monthly_usd": 499.0,
            "price_yearly_usd": 4990.0,
            "limits_json": {
                "max_projects": 100,
                "max_monthly_executions": 5000,
                "max_tokens": 25000000,
                "concurrency_limit": 15,
                "autonomous_deployment_allowed": True,
            },
        },
        {
            "plan_code": "enterprise",
            "name": "Enterprise Autonomous Factory",
            "description": "Custom quotas, dedicated infrastructure, and enterprise SLAs.",
            "price_monthly_usd": 1999.0,
            "price_yearly_usd": 19990.0,
            "limits_json": {
                "max_projects": 1000,
                "max_monthly_executions": 50000,
                "max_tokens": 100000000,
                "concurrency_limit": 50,
                "autonomous_deployment_allowed": True,
            },
        },
    ]

    async def initialize_plans(self, db: AsyncSession):
        """Seed default plans into database if not present."""
        for p in self.DEFAULT_PLANS:
            q = select(SubscriptionPlan).where(SubscriptionPlan.plan_code == p["plan_code"])
            existing = (await db.execute(q)).scalar_one_or_none()
            if not existing:
                plan = SubscriptionPlan(
                    plan_code=p["plan_code"],
                    name=p["name"],
                    description=p["description"],
                    price_monthly_usd=p["price_monthly_usd"],
                    price_yearly_usd=p["price_yearly_usd"],
                    limits_json=p["limits_json"],
                    is_active=True,
                    created_at=datetime.utcnow(),
                )
                db.add(plan)
        await db.commit()

    async def list_plans(self, db: AsyncSession) -> List[SubscriptionPlan]:
        """Fetch all active plans."""
        await self.initialize_plans(db)
        q = select(SubscriptionPlan).where(SubscriptionPlan.is_active == True)
        res = await db.execute(q)
        return list(res.scalars().all())

    async def get_plan(self, db: AsyncSession, plan_code: str) -> Optional[SubscriptionPlan]:
        """Fetch single plan by code."""
        await self.initialize_plans(db)
        q = select(SubscriptionPlan).where(SubscriptionPlan.plan_code == plan_code.lower())
        res = await db.execute(q)
        return res.scalar_one_or_none()

    async def create_subscription(
        self,
        db: AsyncSession,
        tenant_id: str,
        organization_id: Optional[str] = None,
        plan_code: str = "free",
        billing_interval: str = "monthly",
        provider: str = "stripe",
        provider_sub_id: Optional[str] = None,
    ) -> SubscriptionRecord:
        """Create or update active tenant subscription."""
        plan = await self.get_plan(db, plan_code)
        if not plan:
            raise ValueError(f"Plan '{plan_code}' not found")

        if not organization_id:
            q_org = select(Organization).where(Organization.tenant_id == tenant_id)
            org = (await db.execute(q_org)).scalar_one_or_none()
            if not org:
                org = Organization(
                    tenant_id=tenant_id,
                    name=f"Org-{tenant_id[:8]}",
                    slug=f"org-{tenant_id[:8]}",
                    billing_email=f"billing@{tenant_id[:8]}.local",
                    created_at=datetime.utcnow(),
                )
                db.add(org)
                await db.flush()
            organization_id = org.id

        # Deactivate existing active subscription if any
        q_curr = select(SubscriptionRecord).where(
            and_(
                SubscriptionRecord.tenant_id == tenant_id,
                SubscriptionRecord.status.in_(["active", "trialing"]),
            )
        )
        existing = (await db.execute(q_curr)).scalar_one_or_none()
        if existing:
            existing.status = "canceled"
            existing.updated_at = datetime.utcnow()

        duration_days = 365 if billing_interval == "yearly" else 30
        now = datetime.utcnow()
        sub = SubscriptionRecord(
            tenant_id=tenant_id,
            organization_id=organization_id,
            plan_id=plan.id,
            status="active",
            billing_interval=billing_interval,
            current_period_start=now,
            current_period_end=now + timedelta(days=duration_days),
            provider=provider,
            provider_subscription_id=provider_sub_id or f"sub_{provider}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            created_at=now,
            updated_at=now,
        )
        db.add(sub)
        await db.commit()
        await db.refresh(sub)
        logger.info(f"Created subscription {sub.id} ({plan_code}) for tenant {tenant_id}")
        return sub

    async def get_active_subscription(
        self,
        db: AsyncSession,
        tenant_id: str,
    ) -> Optional[SubscriptionRecord]:
        """Get current active subscription for a tenant."""
        q = (
            select(SubscriptionRecord)
            .where(
                and_(
                    SubscriptionRecord.tenant_id == tenant_id,
                    SubscriptionRecord.status.in_(["active", "trialing"]),
                )
            )
            .order_by(desc(SubscriptionRecord.created_at))
        )
        res = await db.execute(q)
        return res.scalar_one_or_none()

    async def upgrade_subscription(
        self,
        db: AsyncSession,
        tenant_id: str,
        new_plan_code: str,
    ) -> SubscriptionRecord:
        """Upgrade active subscription to higher tier."""
        sub = await self.get_active_subscription(db, tenant_id)
        if not sub:
            raise ValueError(f"No active subscription found for tenant {tenant_id}")

        new_plan = await self.get_plan(db, new_plan_code)
        if not new_plan:
            raise ValueError(f"Plan '{new_plan_code}' not found")

        sub.plan_id = new_plan.id
        sub.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(sub)
        logger.info(f"Upgraded tenant {tenant_id} to plan '{new_plan_code}'")
        return sub

    async def cancel_subscription(
        self,
        db: AsyncSession,
        tenant_id: str,
        at_period_end: bool = True,
        immediately: bool = False,
    ) -> SubscriptionRecord:
        """Cancel subscription immediately or at period end."""
        sub = await self.get_active_subscription(db, tenant_id)
        if not sub:
            raise ValueError(f"No active subscription found for tenant {tenant_id}")

        if immediately:
            sub.status = "canceled"
            sub.cancel_at_period_end = False
        elif at_period_end:
            sub.cancel_at_period_end = True
        else:
            sub.status = "canceled"
        sub.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(sub)
        return sub

    async def check_entitlement(
        self,
        db: AsyncSession,
        tenant_id: str,
        feature_key: str,
        requested_amount: int = 1,
    ) -> bool:
        """Verify whether tenant is permitted to perform action under plan quotas."""
        sub = await self.get_active_subscription(db, tenant_id)
        if not sub:
            # Default to free tier
            plan = await self.get_plan(db, "free")
        else:
            q_plan = select(SubscriptionPlan).where(SubscriptionPlan.id == sub.plan_id)
            plan = (await db.execute(q_plan)).scalar_one_or_none()

        if not plan:
            return False

        limits = plan.limits_json or {}
        limit_val = limits.get(feature_key)

        if limit_val is None:
            return True
        if isinstance(limit_val, bool):
            return limit_val
        return limit_val >= requested_amount
