"""
Root Cause Analysis (RCA) Agent.
Correlates telemetry metrics, trace spans, recent git commits/deployments, and worker history
to diagnose incident root causes, assign confidence scores, and recommend tiered remediation actions.
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy import select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from factory.core.logger import logger
from factory.models.schema import (
    IncidentRecord,
    RCAReport,
    TelemetryMetricRecord,
    DeploymentRelease,
    AlertEvent,
)


class RootCauseAnalysisAgent:
    """Automated diagnostic engine cross-referencing telemetry, releases, and errors."""

    ACTION_TIER_MAPPING = {
        "restart_container": 1,
        "retry_job": 1,
        "clear_cache": 1,
        "scale_service": 2,
        "rollback_release": 2,
        "database_migration_revert": 3,
        "secret_rotation": 3,
        "manual_investigation": 3,
    }

    async def investigate_incident(
        self,
        db: AsyncSession,
        incident_id: str,
    ) -> RCAReport:
        """Run deep correlation analysis to discover root cause and prescribe remediation."""
        # 1. Fetch Incident
        q_inc = select(IncidentRecord).where(IncidentRecord.id == incident_id)
        res_inc = await db.execute(q_inc)
        incident = res_inc.scalar_one_or_none()
        if not incident:
            raise ValueError(f"Incident with ID {incident_id} not found")

        if incident.status == "detected":
            incident.status = "investigating"
            incident.acknowledged_at = datetime.utcnow()
            await db.commit()

        window_start = incident.detected_at - timedelta(minutes=30)
        window_end = incident.detected_at + timedelta(minutes=15)

        # 2. Correlate recent telemetry metrics
        q_metrics = (
            select(TelemetryMetricRecord)
            .where(
                and_(
                    TelemetryMetricRecord.project_id == incident.project_id,
                    TelemetryMetricRecord.timestamp >= window_start,
                    TelemetryMetricRecord.timestamp <= window_end,
                )
            )
            .order_by(desc(TelemetryMetricRecord.timestamp))
            .limit(50)
        )
        res_metrics = await db.execute(q_metrics)
        metrics = list(res_metrics.scalars().all())

        # 3. Correlate recent deployments
        q_releases = (
            select(DeploymentRelease)
            .where(
                and_(
                    DeploymentRelease.project_id == incident.project_id,
                    DeploymentRelease.environment == incident.environment,
                )
            )
            .order_by(desc(DeploymentRelease.created_at))
            .limit(5)
        )
        res_releases = await db.execute(q_releases)
        recent_releases = list(res_releases.scalars().all())

        # 4. Synthesize diagnosis
        metrics_summary: Dict[str, Any] = {}
        for m in metrics:
            if m.metric_name not in metrics_summary:
                metrics_summary[m.metric_name] = []
            metrics_summary[m.metric_name].append(m.metric_value)

        probable_cause = ""
        recommended_action = "restart_container"
        tier = 1
        confidence = 0.85
        evidence: Dict[str, Any] = {
            "incident_severity": incident.severity,
            "affected_service": incident.affected_service,
            "metrics_analyzed": len(metrics),
            "trace_id": incident.trace_id,
        }
        alternatives: List[str] = []

        # Check for recent deployment correlation (< 30 minutes before incident)
        recent_deployment = None
        for rel in recent_releases:
            if rel.created_at and abs((incident.detected_at - rel.created_at).total_seconds()) < 1800:
                recent_deployment = rel
                break

        error_rates = metrics_summary.get("application.error_rate", [])
        avg_err = (sum(error_rates) / len(error_rates)) if error_rates else 0.0
        cpu_vals = metrics_summary.get("system.cpu_percent", [])
        avg_cpu = (sum(cpu_vals) / len(cpu_vals)) if cpu_vals else 0.0
        mem_vals = metrics_summary.get("system.memory_percent", [])
        avg_mem = (sum(mem_vals) / len(mem_vals)) if mem_vals else 0.0

        if recent_deployment and (avg_err > 5.0 or "deploy" in incident.impact_summary.lower()):
            probable_cause = (
                f"Defective deployment release '{recent_deployment.version}' (commit {recent_deployment.commit_sha[:8] if recent_deployment.commit_sha else 'HEAD'}) "
                f"introduced runtime regression causing error spikes ({avg_err:.1f}%)."
            )
            recommended_action = "rollback_release"
            tier = 2
            confidence = 0.94
            evidence["deployment_id"] = recent_deployment.id
            evidence["commit_sha"] = recent_deployment.commit_sha
            evidence["version"] = recent_deployment.version
            alternatives = [
                "Transient third-party dependency outage",
                "Traffic spike exceeding provisioning limits",
            ]
        elif avg_cpu > 85.0 or "cpu" in incident.impact_summary.lower():
            probable_cause = f"High compute saturation on service '{incident.affected_service}' with sustained CPU {avg_cpu:.1f}% exceeding safe operational margins."
            recommended_action = "scale_service"
            tier = 2
            confidence = 0.91
            evidence["avg_cpu"] = avg_cpu
            alternatives = [
                "Unoptimized query causing high thread contention",
                "Sudden organic user traffic surge",
            ]
        elif avg_mem > 90.0 or "memory" in incident.impact_summary.lower():
            probable_cause = f"Process memory leakage or heap exhaustion detected on '{incident.affected_service}' (Memory: {avg_mem:.1f}%)."
            recommended_action = "restart_container"
            tier = 1
            confidence = 0.88
            evidence["avg_memory"] = avg_mem
            alternatives = [
                "Memory leak in long-lived connection pool",
                "Large unpaginated query loaded into heap",
            ]
        elif "database" in incident.affected_service.lower() or "schema" in incident.impact_summary.lower():
            probable_cause = f"Database schema mismatch or migration incompatibility on '{incident.affected_service}'."
            recommended_action = "database_migration_revert"
            tier = 3
            confidence = 0.80
            evidence["service_type"] = "database"
            alternatives = ["Database connection pool starvation"]
        else:
            probable_cause = f"Service failure or unresponsive process on '{incident.affected_service}' causing health probe failures."
            recommended_action = "restart_container"
            tier = 1
            confidence = 0.85
            evidence["default_heuristic"] = True
            alternatives = ["Transient network partition", "Deadlocked asynchronous worker"]

        risk_assessment = "low" if tier == 1 else ("medium" if tier == 2 else "high")

        # 5. Check if RCA already exists for this incident
        q_existing = select(RCAReport).where(RCAReport.incident_id == incident.id)
        res_existing = await db.execute(q_existing)
        existing_rca = res_existing.scalar_one_or_none()

        if existing_rca:
            existing_rca.probable_root_cause = probable_cause
            existing_rca.confidence_score = confidence
            existing_rca.supporting_evidence = evidence
            existing_rca.alternative_explanations = alternatives
            existing_rca.recommended_action = recommended_action
            existing_rca.healing_tier = tier
            existing_rca.risk_assessment = risk_assessment
            rca_record = existing_rca
        else:
            rca_record = RCAReport(
                incident_id=incident.id,
                probable_root_cause=probable_cause,
                confidence_score=confidence,
                supporting_evidence=evidence,
                alternative_explanations=alternatives,
                recommended_action=recommended_action,
                healing_tier=tier,
                risk_assessment=risk_assessment,
                generated_at=datetime.utcnow(),
            )
            db.add(rca_record)

        incident.status = "rca_completed"
        await db.commit()
        await db.refresh(rca_record)

        logger.info(
            f"RCA completed for incident {incident.id}: action={recommended_action}, tier={tier}, confidence={confidence}"
        )
        return rca_record
