"""
Incident Management Engine.
Manages the lifecycle of operational incidents from initial detection through resolution,
correlating alerts, traces, logs, and root cause analysis reports.
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy import select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from factory.core.logger import logger
from factory.models.schema import IncidentRecord, AlertEvent, RCAReport, SelfHealingAction


class IncidentManager:
    """Orchestrates production incident detection, tracking, and resolution lifecycles."""

    VALID_STATUSES = [
        "detected",
        "investigating",
        "rca_completed",
        "remediating",
        "resolved",
        "closed",
    ]

    async def create_incident_from_alert(
        self,
        db: AsyncSession,
        alert_event: AlertEvent,
        affected_service: Optional[str] = None,
        impact_summary: Optional[str] = None,
    ) -> IncidentRecord:
        """Create an incident automatically from a critical or high-severity alert event."""
        service = affected_service or alert_event.context_json.get("service") or "application-service"
        summary = impact_summary or f"Automated incident triggered by alert: {alert_event.title} (Value: {alert_event.metric_value}, Threshold: {alert_event.threshold})"
        trace_id = alert_event.context_json.get("trace_id")
        env = alert_event.context_json.get("environment", "production")

        incident = IncidentRecord(
            project_id=alert_event.project_id,
            title=f"Incident: {alert_event.title}",
            environment=env,
            severity=alert_event.severity,
            status="detected",
            affected_service=service,
            impact_summary=summary,
            lead_alert_id=alert_event.id,
            trace_id=trace_id,
            detected_at=datetime.utcnow(),
        )
        db.add(incident)
        await db.commit()
        await db.refresh(incident)

        logger.info(f"Created operational incident {incident.id} for alert {alert_event.id} ({incident.title})")
        return incident

    async def create_manual_incident(
        self,
        db: AsyncSession,
        project_id: str,
        title: str,
        affected_service: str,
        severity: str = "medium",
        environment: str = "production",
        impact_summary: str = "",
        trace_id: Optional[str] = None,
    ) -> IncidentRecord:
        """Create an incident manually by an operator or test suite."""
        incident = IncidentRecord(
            project_id=project_id,
            title=title,
            environment=environment,
            severity=severity,
            status="detected",
            affected_service=affected_service,
            impact_summary=impact_summary or f"Manual incident logged for {affected_service}",
            trace_id=trace_id,
            detected_at=datetime.utcnow(),
        )
        db.add(incident)
        await db.commit()
        await db.refresh(incident)

        logger.info(f"Manual incident {incident.id} created for project {project_id}")
        return incident

    async def transition_status(
        self,
        db: AsyncSession,
        incident_id: str,
        new_status: str,
        notes: Optional[str] = None,
    ) -> IncidentRecord:
        """Transition incident through its standardized lifecycle."""
        if new_status not in self.VALID_STATUSES:
            raise ValueError(f"Invalid status '{new_status}'. Must be one of {self.VALID_STATUSES}")

        q = select(IncidentRecord).where(IncidentRecord.id == incident_id)
        res = await db.execute(q)
        incident = res.scalar_one_or_none()
        if not incident:
            raise ValueError(f"Incident with ID {incident_id} not found")

        old_status = incident.status
        incident.status = new_status
        now = datetime.utcnow()

        if new_status == "investigating" and not incident.acknowledged_at:
            incident.acknowledged_at = now
        elif new_status in ("resolved", "closed") and not incident.resolved_at:
            incident.resolved_at = now

        if notes:
            incident.impact_summary = f"{incident.impact_summary}\n[{now.isoformat()}] [{new_status.upper()}]: {notes}"

        await db.commit()
        await db.refresh(incident)

        logger.info(f"Incident {incident_id} transitioned from {old_status} -> {new_status}")
        return incident

    async def get_active_incidents(
        self,
        db: AsyncSession,
        project_id: Optional[str] = None,
    ) -> List[IncidentRecord]:
        """Fetch all incidents that are not yet closed."""
        query = select(IncidentRecord).where(IncidentRecord.status != "closed")
        if project_id:
            query = query.where(IncidentRecord.project_id == project_id)
        query = query.order_by(desc(IncidentRecord.detected_at))
        res = await db.execute(query)
        return list(res.scalars().all())

    async def get_incident(
        self,
        db: AsyncSession,
        incident_id: str,
    ) -> Optional[IncidentRecord]:
        """Fetch incident by primary key."""
        q = select(IncidentRecord).where(IncidentRecord.id == incident_id)
        res = await db.execute(q)
        return res.scalar_one_or_none()

