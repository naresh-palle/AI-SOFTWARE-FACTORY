"""
FastAPI Routes for Intelligent Observability, AIOps & Self-Healing Platform.
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select, and_, desc

from factory.core.database import get_db_session
from factory.core.logger import logger
from factory.models.schema import (
    TelemetryMetricRecord,
    AlertRule,
    AlertEvent,
    IncidentRecord,
    RCAReport,
    SelfHealingAction,
    SLOConfiguration,
    Project,
)
from factory.observability.telemetry import TelemetryCollector
from factory.observability.monitoring.app_monitor import ApplicationMonitoringAgent
from factory.observability.monitoring.infra_monitor import InfrastructureMonitoringAgent
from factory.observability.aiops.anomaly_detector import AIOpsAnomalyDetector
from factory.observability.alerts.alert_manager import AlertManager
from factory.observability.incidents.incident_manager import IncidentManager
from factory.observability.incidents.rca_agent import RootCauseAnalysisAgent
from factory.observability.self_healing.healing_engine import SelfHealingEngine
from factory.observability.slo.slo_manager import SLOManager
from factory.observability.slo.cost_intelligence import CostIntelligenceEngine

router = APIRouter(prefix="/observability", tags=["Observability & AIOps"])

# Service singletons
telemetry_collector = TelemetryCollector()
app_monitor = ApplicationMonitoringAgent()
infra_monitor = InfrastructureMonitoringAgent()
anomaly_detector = AIOpsAnomalyDetector()
alert_manager = AlertManager()
incident_manager = IncidentManager()
rca_agent = RootCauseAnalysisAgent()
healing_engine = SelfHealingEngine()
slo_manager = SLOManager()
cost_engine = CostIntelligenceEngine()


# ---------------------------------------------------------------------------
# Request Schemas
# ---------------------------------------------------------------------------
class IngestMetricRequest(BaseModel):
    project_id: str
    metric_name: str
    metric_value: float
    unit: str = "count"
    dimensions: Dict[str, Any] = Field(default_factory=dict)


class ProbeRequest(BaseModel):
    project_id: str
    endpoint_url: str = "http://localhost:8000/health"
    timeout_seconds: float = 5.0


class SampleInfraRequest(BaseModel):
    project_id: str


class CreateAlertRuleRequest(BaseModel):
    project_id: str
    name: str
    metric_name: str
    condition: str = ">"
    threshold: float
    duration_seconds: int = 60
    severity: str = "medium"
    notification_channels: List[str] = Field(default_factory=lambda: ["webhook"])


class EvaluateAlertRequest(BaseModel):
    project_id: str
    metric_name: str
    current_value: float
    context: Dict[str, Any] = Field(default_factory=dict)


class CreateIncidentRequest(BaseModel):
    project_id: str
    title: str
    affected_service: str
    severity: str = "medium"
    environment: str = "production"
    impact_summary: str = ""
    trace_id: Optional[str] = None


class TransitionIncidentRequest(BaseModel):
    new_status: str
    notes: Optional[str] = None


class ExecuteHealingRequest(BaseModel):
    project_id: str
    action_type: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    incident_id: Optional[str] = None
    force_approved: bool = False


class ConfigureSLORequest(BaseModel):
    project_id: str
    name: str
    target_percentage: float = 99.9
    evaluation_window_days: int = 30


# ---------------------------------------------------------------------------
# Telemetry & Monitoring Endpoints
# ---------------------------------------------------------------------------
@router.get("/metrics")
async def list_metrics(
    project_id: Optional[str] = None,
    metric_name: Optional[str] = None,
    limit: int = 100,
):
    """Retrieve ingested operational telemetry metrics."""
    async with get_db_session() as session:
        q = select(TelemetryMetricRecord)
        if project_id:
            q = q.where(TelemetryMetricRecord.project_id == project_id)
        if metric_name:
            q = q.where(TelemetryMetricRecord.metric_name == metric_name)
        q = q.order_by(desc(TelemetryMetricRecord.timestamp)).limit(limit)
        res = await session.execute(q)
        records = res.scalars().all()

        return [
            {
                "id": r.id,
                "project_id": r.project_id,
                "metric_name": r.metric_name,
                "metric_value": r.metric_value,
                "unit": r.unit,
                "dimensions": r.dimensions,
                "timestamp": r.timestamp.isoformat() if r.timestamp else None,
            }
            for r in records
        ]


@router.post("/metrics")
async def ingest_metric(payload: IngestMetricRequest):
    """Ingest a single telemetry metric measurement."""
    telemetry_collector.record_metric(
        project_id=payload.project_id,
        metric_name=payload.metric_name,
        value=payload.metric_value,
        unit=payload.unit,
        dimensions=payload.dimensions,
    )
    async with get_db_session() as session:
        count = await telemetry_collector.flush_to_db(session)
    return {"status": "ingested", "records_flushed": count}


@router.post("/probe")
async def run_application_probe(payload: ProbeRequest):
    """Execute live health and latency probe against target application endpoint."""
    async with get_db_session() as session:
        result = await app_monitor.probe_application(
            db=session,
            project_id=payload.project_id,
            endpoint_url=payload.endpoint_url,
            timeout_seconds=payload.timeout_seconds,
        )
        return result


@router.post("/sample-infra")
async def sample_infrastructure(payload: SampleInfraRequest):
    """Collect host, container, and worker infrastructure telemetry."""
    async with get_db_session() as session:
        metrics = await infra_monitor.sample_infrastructure_telemetry(
            db=session,
            project_id=payload.project_id,
        )
        return {"status": "sampled", "metrics_count": len(metrics), "metrics": metrics}


# ---------------------------------------------------------------------------
# Alerts & Anomaly Detection Endpoints
# ---------------------------------------------------------------------------
@router.get("/alerts")
async def list_alert_events(
    project_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
):
    """List firing or historical operational alert events."""
    async with get_db_session() as session:
        q = select(AlertEvent)
        if project_id:
            q = q.where(AlertEvent.project_id == project_id)
        if status:
            q = q.where(AlertEvent.status == status)
        q = q.order_by(desc(AlertEvent.triggered_at)).limit(limit)
        res = await session.execute(q)
        events = res.scalars().all()
        return [
            {
                "id": e.id,
                "rule_id": e.rule_id,
                "project_id": e.project_id,
                "title": e.title,
                "severity": e.severity,
                "metric_value": e.metric_value,
                "threshold": e.threshold,
                "status": e.status,
                "fingerprint": e.fingerprint,
                "context_json": e.context_json,
                "triggered_at": e.triggered_at.isoformat() if e.triggered_at else None,
                "resolved_at": e.resolved_at.isoformat() if e.resolved_at else None,
            }
            for e in events
        ]


@router.get("/alerts/rules")
async def list_alert_rules(project_id: Optional[str] = None):
    """List configured alert rules."""
    async with get_db_session() as session:
        q = select(AlertRule)
        if project_id:
            q = q.where(AlertRule.project_id == project_id)
        res = await session.execute(q)
        rules = res.scalars().all()
        return [
            {
                "id": r.id,
                "project_id": r.project_id,
                "name": r.name,
                "metric_name": r.metric_name,
                "condition": r.condition,
                "threshold": r.threshold,
                "duration_seconds": r.duration_seconds,
                "severity": r.severity,
                "is_enabled": r.is_enabled,
                "notification_channels": r.notification_channels,
            }
            for r in rules
        ]


@router.post("/alerts/rules")
async def create_alert_rule(payload: CreateAlertRuleRequest):
    """Create a new alert rule definition."""
    async with get_db_session() as session:
        rule = AlertRule(
            project_id=payload.project_id,
            name=payload.name,
            metric_name=payload.metric_name,
            condition=payload.condition,
            threshold=payload.threshold,
            duration_seconds=payload.duration_seconds,
            severity=payload.severity,
            notification_channels=payload.notification_channels,
            created_at=datetime.utcnow(),
        )
        session.add(rule)
        await session.commit()
        await session.refresh(rule)
        return {"id": rule.id, "name": rule.name, "metric_name": rule.metric_name}


@router.post("/alerts/evaluate")
async def evaluate_alert_metric(payload: EvaluateAlertRequest):
    """Evaluate metric value against rules with deduplication and incident auto-triggering."""
    async with get_db_session() as session:
        firing_events = await alert_manager.evaluate_metric_against_rules(
            db=session,
            project_id=payload.project_id,
            metric_name=payload.metric_name,
            current_value=payload.current_value,
            context=payload.context,
        )

        created_incidents = []
        for ev in firing_events:
            if ev.severity in ("high", "critical"):
                inc = await incident_manager.create_incident_from_alert(db=session, alert_event=ev)
                created_incidents.append(inc.id)

        return {
            "firing_alerts_count": len(firing_events),
            "firing_alerts": [e.id for e in firing_events],
            "auto_created_incidents": created_incidents,
        }


@router.post("/anomalies/detect")
async def detect_anomalies(project_id: str, metric_name: str = "application.latency_ms"):
    """Detect statistical anomalies using AIOps baseline evaluation."""
    async with get_db_session() as session:
        anomalies = await anomaly_detector.detect_anomalies(
            db=session,
            project_id=project_id,
            metric_name=metric_name,
        )
        return {"metric_name": metric_name, "anomalies_detected": len(anomalies), "anomalies": anomalies}


# ---------------------------------------------------------------------------
# Incident Management & RCA Endpoints
# ---------------------------------------------------------------------------
@router.get("/incidents")
async def list_incidents(project_id: Optional[str] = None):
    """Fetch active operational incidents."""
    async with get_db_session() as session:
        incidents = await incident_manager.get_active_incidents(session, project_id=project_id)
        return [
            {
                "id": inc.id,
                "project_id": inc.project_id,
                "title": inc.title,
                "environment": inc.environment,
                "severity": inc.severity,
                "status": inc.status,
                "affected_service": inc.affected_service,
                "impact_summary": inc.impact_summary,
                "lead_alert_id": inc.lead_alert_id,
                "trace_id": inc.trace_id,
                "detected_at": inc.detected_at.isoformat() if inc.detected_at else None,
                "acknowledged_at": inc.acknowledged_at.isoformat() if inc.acknowledged_at else None,
                "resolved_at": inc.resolved_at.isoformat() if inc.resolved_at else None,
            }
            for inc in incidents
        ]


@router.post("/incidents")
async def create_incident(payload: CreateIncidentRequest):
    """Create an incident manually."""
    async with get_db_session() as session:
        inc = await incident_manager.create_manual_incident(
            db=session,
            project_id=payload.project_id,
            title=payload.title,
            affected_service=payload.affected_service,
            severity=payload.severity,
            environment=payload.environment,
            impact_summary=payload.impact_summary,
            trace_id=payload.trace_id,
        )
        return {"id": inc.id, "title": inc.title, "status": inc.status}


@router.get("/incidents/{incident_id}")
async def get_incident_details(incident_id: str):
    """Get full incident record including RCA report and self-healing actions."""
    async with get_db_session() as session:
        inc = await incident_manager.get_incident(session, incident_id)
        if not inc:
            raise HTTPException(status_code=404, detail="Incident not found")

        q_rca = select(RCAReport).where(RCAReport.incident_id == incident_id)
        rca_res = await session.execute(q_rca)
        rca = rca_res.scalar_one_or_none()

        q_actions = select(SelfHealingAction).where(SelfHealingAction.incident_id == incident_id)
        actions_res = await session.execute(q_actions)
        actions = actions_res.scalars().all()

        return {
            "incident": {
                "id": inc.id,
                "project_id": inc.project_id,
                "title": inc.title,
                "environment": inc.environment,
                "severity": inc.severity,
                "status": inc.status,
                "affected_service": inc.affected_service,
                "impact_summary": inc.impact_summary,
                "trace_id": inc.trace_id,
                "detected_at": inc.detected_at.isoformat() if inc.detected_at else None,
                "acknowledged_at": inc.acknowledged_at.isoformat() if inc.acknowledged_at else None,
                "resolved_at": inc.resolved_at.isoformat() if inc.resolved_at else None,
            },
            "rca": {
                "id": rca.id,
                "probable_root_cause": rca.probable_root_cause,
                "confidence_score": rca.confidence_score,
                "supporting_evidence": rca.supporting_evidence,
                "alternative_explanations": rca.alternative_explanations,
                "recommended_action": rca.recommended_action,
                "healing_tier": rca.healing_tier,
                "risk_assessment": rca.risk_assessment,
                "generated_at": rca.generated_at.isoformat() if rca.generated_at else None,
            }
            if rca
            else None,
            "actions": [
                {
                    "id": a.id,
                    "action_type": a.action_type,
                    "tier": a.tier,
                    "status": a.status,
                    "duration_ms": a.duration_ms,
                    "execution_log": a.execution_log,
                    "created_at": a.created_at.isoformat() if a.created_at else None,
                }
                for a in actions
            ],
        }


@router.post("/incidents/{incident_id}/rca")
async def run_incident_rca(incident_id: str):
    """Trigger automated Root Cause Analysis on an incident."""
    async with get_db_session() as session:
        rca = await rca_agent.investigate_incident(session, incident_id)
        return {
            "incident_id": incident_id,
            "probable_root_cause": rca.probable_root_cause,
            "confidence_score": rca.confidence_score,
            "recommended_action": rca.recommended_action,
            "healing_tier": rca.healing_tier,
            "risk_assessment": rca.risk_assessment,
            "supporting_evidence": rca.supporting_evidence,
        }


@router.post("/incidents/{incident_id}/transition")
async def transition_incident(incident_id: str, payload: TransitionIncidentRequest):
    """Update status of an operational incident."""
    async with get_db_session() as session:
        inc = await incident_manager.transition_status(
            db=session,
            incident_id=incident_id,
            new_status=payload.new_status,
            notes=payload.notes,
        )
        return {"id": inc.id, "status": inc.status}


# ---------------------------------------------------------------------------
# Self-Healing Endpoints
# ---------------------------------------------------------------------------
@router.post("/self-healing/execute")
async def execute_self_healing(payload: ExecuteHealingRequest):
    """Execute or submit for approval a self-healing remediation action."""
    async with get_db_session() as session:
        action = await healing_engine.execute_healing_action(
            db=session,
            project_id=payload.project_id,
            action_type=payload.action_type,
            parameters=payload.parameters,
            incident_id=payload.incident_id,
            force_approved=payload.force_approved,
        )
        return {
            "id": action.id,
            "action_type": action.action_type,
            "tier": action.tier,
            "status": action.status,
            "approval_id": action.approval_id,
            "duration_ms": action.duration_ms,
            "execution_log": action.execution_log,
        }


@router.get("/self-healing/actions")
async def list_self_healing_actions(
    project_id: Optional[str] = None,
    limit: int = 50,
):
    """List execution history of self-healing actions."""
    async with get_db_session() as session:
        q = select(SelfHealingAction)
        if project_id:
            q = q.where(SelfHealingAction.project_id == project_id)
        q = q.order_by(desc(SelfHealingAction.created_at)).limit(limit)
        res = await session.execute(q)
        actions = res.scalars().all()
        return [
            {
                "id": a.id,
                "project_id": a.project_id,
                "incident_id": a.incident_id,
                "action_type": a.action_type,
                "tier": a.tier,
                "status": a.status,
                "approval_id": a.approval_id,
                "duration_ms": a.duration_ms,
                "execution_log": a.execution_log,
                "created_at": a.created_at.isoformat() if a.created_at else None,
            }
            for a in actions
        ]


# ---------------------------------------------------------------------------
# Reliability, SLO & FinOps Endpoints
# ---------------------------------------------------------------------------
@router.get("/slo")
async def get_slos(project_id: str):
    """List and evaluate SLO configurations for a project."""
    async with get_db_session() as session:
        slos = await slo_manager.get_project_slos(session, project_id)
        evaluated = []
        for s in slos:
            ev = await slo_manager.evaluate_slo(session, s.id)
            evaluated.append({
                "id": ev.id,
                "name": ev.name,
                "target_percentage": ev.target_percentage,
                "evaluation_window_days": ev.evaluation_window_days,
                "current_sli": ev.current_sli,
                "error_budget_remaining_percent": ev.error_budget_remaining_percent,
                "status": ev.status,
                "updated_at": ev.updated_at.isoformat() if ev.updated_at else None,
            })
        return evaluated


@router.post("/slo")
async def configure_slo_endpoint(payload: ConfigureSLORequest):
    """Create or update an SLO target definition."""
    async with get_db_session() as session:
        slo = await slo_manager.configure_slo(
            db=session,
            project_id=payload.project_id,
            name=payload.name,
            target_percentage=payload.target_percentage,
            evaluation_window_days=payload.evaluation_window_days,
        )
        return {
            "id": slo.id,
            "name": slo.name,
            "target_percentage": slo.target_percentage,
            "status": slo.status,
        }


@router.get("/reliability/metrics")
async def get_reliability_metrics(project_id: Optional[str] = None):
    """Get operational velocity metrics (MTTD, MTTA, MTTR)."""
    async with get_db_session() as session:
        metrics = await slo_manager.calculate_incident_mttr_metrics(session, project_id=project_id)
        return metrics


@router.get("/finops/costs")
async def get_cost_analysis(project_id: Optional[str] = None):
    """Get FinOps cloud, token, and compute cost metrics."""
    async with get_db_session() as session:
        costs = await cost_engine.analyze_costs(session, project_id=project_id)
        return costs


@router.get("/finops/recommendations")
async def get_cost_recommendations(project_id: Optional[str] = None):
    """Get actionable FinOps cost optimization recommendations."""
    async with get_db_session() as session:
        recs = await cost_engine.get_optimization_recommendations(session, project_id=project_id)
        return recs
