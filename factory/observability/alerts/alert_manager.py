"""
Intelligent Alert Management Engine.
Handles alert generation, cryptographic deduplication, grouping, suppression,
and secure webhook / notification dispatch with zero credential leakage.
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy import select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from factory.core.logger import logger
from factory.core.security import hash_string
from factory.models.schema import AlertRule, AlertEvent


class AlertManager:
    """Manages alert lifecycle, deduplication, suppression, and notification routing."""

    @staticmethod
    def compute_fingerprint(project_id: str, rule_id: str, severity: str) -> str:
        """Compute unique SHA-256 deduplication fingerprint."""
        raw = f"{project_id}:{rule_id}:{severity}"
        return hash_string(raw)

    async def create_rule(
        self,
        db: AsyncSession,
        project_id: str,
        name: str,
        metric_name: str,
        condition: str = ">",
        threshold: float = 0.0,
        severity: str = "medium",
        duration_seconds: int = 60,
        notification_channels: Optional[List[str]] = None,
    ) -> AlertRule:
        """Define and persist a new alert rule."""
        rule = AlertRule(
            project_id=project_id,
            name=name,
            metric_name=metric_name,
            condition=condition,
            threshold=threshold,
            severity=severity,
            duration_seconds=duration_seconds,
            notification_channels=notification_channels or ["webhook"],
            created_at=datetime.utcnow(),
        )
        db.add(rule)
        await db.commit()
        await db.refresh(rule)
        logger.info(f"Created alert rule '{name}' for metric {metric_name} ({condition} {threshold})")
        return rule

    async def evaluate_metric_against_rules(
        self,
        db: AsyncSession,
        project_id: str,
        metric_name: str,
        current_value: float,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[AlertEvent]:
        """
        Evaluate active rules for a metric. Breached rules fire alerts unless suppressed by fingerprint.
        """
        q = select(AlertRule).where(
            and_(
                AlertRule.project_id == project_id,
                AlertRule.metric_name == metric_name,
                AlertRule.is_enabled == True,
            )
        )
        res = await db.execute(q)
        rules = list(res.scalars().all())

        firing_events: List[AlertEvent] = []
        now = datetime.utcnow()
        suppression_window = now - timedelta(minutes=5)

        for rule in rules:
            is_breached = False
            if rule.condition == ">" and current_value > rule.threshold:
                is_breached = True
            elif rule.condition == ">=" and current_value >= rule.threshold:
                is_breached = True
            elif rule.condition == "<" and current_value < rule.threshold:
                is_breached = True
            elif rule.condition == "<=" and current_value <= rule.threshold:
                is_breached = True
            elif rule.condition == "==" and current_value == rule.threshold:
                is_breached = True

            if is_breached:
                fingerprint = self.compute_fingerprint(project_id, rule.id, rule.severity)

                # Check suppression window
                q_suppress = select(AlertEvent).where(
                    and_(
                        AlertEvent.fingerprint == fingerprint,
                        AlertEvent.status == "firing",
                        AlertEvent.triggered_at >= suppression_window,
                    )
                )
                suppressed = (await db.execute(q_suppress)).scalar_one_or_none()

                if not suppressed:
                    event = AlertEvent(
                        rule_id=rule.id,
                        project_id=project_id,
                        title=f"{rule.name} Breached",
                        severity=rule.severity,
                        metric_value=current_value,
                        threshold=rule.threshold,
                        status="firing",
                        fingerprint=fingerprint,
                        context_json=context or {},
                        triggered_at=now,
                    )
                    db.add(event)
                    firing_events.append(event)
                    logger.warning(
                        f"Alert firing: {rule.name} ({current_value} {rule.condition} {rule.threshold})"
                    )

        if firing_events:
            await db.commit()
            for ev in firing_events:
                await db.refresh(ev)

        return firing_events
