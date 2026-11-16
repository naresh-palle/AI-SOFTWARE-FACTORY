"""
Usage Metering & Centralized Quota Enforcement Engine.
Tracks real-time AI token consumption, cloud worker minutes, and storage,
enforcing hard limits and generating soft quota threshold alerts.
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy import select, func, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from factory.core.logger import logger
from factory.models.schema import UsageEvent, QuotaPolicy, SubscriptionRecord, SubscriptionPlan


class QuotaExceededError(Exception):
    """Raised when tenant exceeds hard quota limit."""
    pass


class UsageMeteringEngine:
    """Records consumption events and calculates aggregate billing & resource metrics."""

    DEFAULT_QUOTAS = {
        "ai_tokens": {"hard_limit": 1000000.0, "soft_alert": 800000.0},
        "worker_minutes": {"hard_limit": 600.0, "soft_alert": 480.0},
        "build_minutes": {"hard_limit": 300.0, "soft_alert": 240.0},
        "storage_mb": {"hard_limit": 5000.0, "soft_alert": 4000.0},
        "deployments": {"hard_limit": 50.0, "soft_alert": 40.0},
    }

    async def record_usage(
        self,
        db: AsyncSession,
        tenant_id: str,
        metric_type: Optional[str] = None,
        quantity: float = 1.0,
        cost_usd: float = 0.0,
        project_id: Optional[str] = None,
        dimensions: Optional[Dict[str, Any]] = None,
        metric_name: Optional[str] = None,
        enforce: bool = True,
        unit: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> UsageEvent:
        """Ingest single usage measurement and enforce quota policies."""
        final_metric = metric_name or metric_type or "ai_tokens"
        if enforce:
            await self.check_and_enforce_quota(db, tenant_id, final_metric, incoming_quantity=quantity)

        dims = dimensions or metadata or {}
        if unit:
            dims["unit"] = unit

        event = UsageEvent(
            tenant_id=tenant_id,
            project_id=project_id,
            metric_type=final_metric,
            quantity=float(quantity),
            cost_usd=float(cost_usd),
            dimensions_json=dims,
            timestamp=datetime.utcnow(),
        )
        db.add(event)
        await db.commit()
        await db.refresh(event)
        return event

    async def check_and_enforce_quota(
        self,
        db: AsyncSession,
        tenant_id: str,
        metric_type: str,
        incoming_quantity: float = 1.0,
    ) -> Dict[str, Any]:
        """
        Verify tenant quota limit before commencing execution.
        Raises QuotaExceededError if hard limit is breached.
        """
        # Query monthly usage sum
        start_of_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        q_sum = select(func.sum(UsageEvent.quantity)).where(
            and_(
                UsageEvent.tenant_id == tenant_id,
                UsageEvent.metric_type == metric_type,
                UsageEvent.timestamp >= start_of_month,
            )
        )
        res = await db.execute(q_sum)
        current_used = float(res.scalar() or 0.0)

        # Get quota config or fallback default
        q_policy = select(QuotaPolicy).where(
            and_(
                QuotaPolicy.tenant_id == tenant_id,
                QuotaPolicy.metric_type == metric_type,
            )
        )
        policy = (await db.execute(q_policy)).scalar_one_or_none()

        hard_limit = policy.hard_limit if policy else self.DEFAULT_QUOTAS.get(metric_type, {}).get("hard_limit", 1000000.0)
        soft_threshold = policy.soft_alert_threshold if policy else self.DEFAULT_QUOTAS.get(metric_type, {}).get("soft_alert", 800000.0)

        projected = current_used + incoming_quantity
        if projected > hard_limit:
            logger.error(f"QUOTA BREACH: Tenant {tenant_id} exceeded {metric_type} ({projected}/{hard_limit})")
            raise QuotaExceededError(
                f"Quota exceeded for {metric_type}: Current usage {current_used:.0f} + {incoming_quantity:.0f} "
                f"exceeds hard limit of {hard_limit:.0f}. Upgrade subscription plan to continue."
            )

        is_near_limit = projected >= soft_threshold
        return {
            "metric_type": metric_type,
            "current_used": current_used,
            "projected": projected,
            "hard_limit": hard_limit,
            "percent_consumed": round((projected / hard_limit) * 100.0, 1),
            "soft_alert_triggered": is_near_limit,
        }

    async def get_tenant_usage_summary(
        self,
        db: AsyncSession,
        tenant_id: str,
    ) -> Dict[str, Any]:
        """Aggregate monthly usage by metric type."""
        start_of_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        q = (
            select(
                UsageEvent.metric_type,
                func.sum(UsageEvent.quantity).label("total_quantity"),
                func.sum(UsageEvent.cost_usd).label("total_cost"),
            )
            .where(
                and_(
                    UsageEvent.tenant_id == tenant_id,
                    UsageEvent.timestamp >= start_of_month,
                )
            )
            .group_by(UsageEvent.metric_type)
        )
        res = await db.execute(q)
        rows = res.all()

        usage_map = {}
        for metric, qty, cost in rows:
            quota_info = self.DEFAULT_QUOTAS.get(metric, {"hard_limit": 1000.0})
            usage_map[metric] = {
                "quantity": float(qty or 0.0),
                "cost_usd": round(float(cost or 0.0), 2),
                "hard_limit": quota_info["hard_limit"],
                "remaining": max(0.0, quota_info["hard_limit"] - float(qty or 0.0)),
            }

        # Populate defaults if missing
        for metric, info in self.DEFAULT_QUOTAS.items():
            if metric not in usage_map:
                usage_map[metric] = {
                    "quantity": 0.0,
                    "cost_usd": 0.0,
                    "hard_limit": info["hard_limit"],
                    "remaining": info["hard_limit"],
                }

        return {
            "tenant_id": tenant_id,
            "billing_period": datetime.utcnow().strftime("%B %Y"),
            "metrics": usage_map,
            "usage_breakdown": usage_map,
        }
