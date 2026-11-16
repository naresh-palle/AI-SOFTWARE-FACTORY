"""
Tests for Phase 7: Intelligent Observability, AIOps & Self-Healing Platform.
Verifies telemetry collection, tracing, monitoring probes, anomaly detection,
alert deduplication, incident management, automated RCA, 3-tier self-healing,
reliability SLOs, FinOps intelligence, and FastAPI endpoints.
"""

import pytest
from datetime import datetime, timedelta
from httpx import ASGITransport, AsyncClient

from factory.core.database import get_db_session, init_db
from factory.models.schema import (
    Project,
    TelemetryMetricRecord,
    AlertRule,
    AlertEvent,
    IncidentRecord,
    RCAReport,
    SelfHealingAction,
    SLOConfiguration,
    DeploymentRelease,
)
from factory.observability.telemetry import (
    TelemetryCollector,
    Span,
    generate_trace_id,
    generate_span_id,
)
from factory.observability.monitoring.app_monitor import ApplicationMonitoringAgent
from factory.observability.monitoring.infra_monitor import InfrastructureMonitoringAgent
from factory.observability.aiops.anomaly_detector import AIOpsAnomalyDetector
from factory.observability.alerts.alert_manager import AlertManager
from factory.observability.incidents.incident_manager import IncidentManager
from factory.observability.incidents.rca_agent import RootCauseAnalysisAgent
from factory.observability.self_healing.healing_engine import SelfHealingEngine
from factory.observability.slo.slo_manager import SLOManager
from factory.observability.slo.cost_intelligence import CostIntelligenceEngine
from factory.api.main import app


@pytest.fixture(autouse=True)
async def setup_db():
    await init_db()


async def get_or_create_test_project(session, name="Obs Test Project") -> Project:
    from sqlalchemy import select
    q = select(Project).where(Project.name == name)
    res = await session.execute(q)
    proj = res.scalar_one_or_none()
    if not proj:
        proj = Project(
            name=name,
            requirement_text="Observability and self-healing test harness",
            platform_target="website",
            status="active",
        )
        session.add(proj)
        await session.commit()
        await session.refresh(proj)
    return proj


@pytest.mark.asyncio
async def test_w3c_trace_context_and_telemetry():
    """Verify OpenTelemetry W3C trace context format and telemetry buffering/persistence."""
    trace_id = generate_trace_id()
    span_id = generate_span_id()

    assert len(trace_id) == 32
    assert len(span_id) == 16

    span = Span(name="test_operation", trace_id=trace_id, parent_span_id=span_id)
    span.set_attribute("http.method", "GET")
    span.set_attribute("http.status_code", 200)

    traceparent = span.to_w3c_traceparent()
    assert traceparent.startswith(f"00-{trace_id}-")

    span.finish()
    assert span.duration_ms >= 0

    collector = TelemetryCollector()
    async with get_db_session() as session:
        proj = await get_or_create_test_project(session, "Trace Project")
        collector.record_metric(
            project_id=proj.id,
            metric_name="application.latency_ms",
            value=124.5,
            unit="ms",
            dimensions={"route": "/api/v1/health"},
        )
        flushed = await collector.flush_to_db(session)
        assert flushed >= 1


@pytest.mark.asyncio
async def test_application_and_infra_monitoring():
    """Verify active synthetic probing and host/worker telemetry sampling."""
    async with get_db_session() as session:
        proj = await get_or_create_test_project(session, "Probe Project")

        # 1. Probe application
        app_monitor = ApplicationMonitoringAgent()
        probe_res = await app_monitor.probe_application(
            db=session,
            project_id=proj.id,
            endpoint_url="http://test/probe",
        )
        assert "status_code" in probe_res
        assert "latency_ms" in probe_res
        assert "is_healthy" in probe_res

        # 2. Infra sampling
        infra_monitor = InfrastructureMonitoringAgent()
        infra_metrics = await infra_monitor.sample_infrastructure_telemetry(
            db=session,
            project_id=proj.id,
        )
        assert len(infra_metrics) >= 4
        metric_names = [m["metric_name"] for m in infra_metrics]
        assert "system.cpu_percent" in metric_names
        assert "system.memory_percent" in metric_names


@pytest.mark.asyncio
async def test_aiops_anomaly_detector():
    """Verify statistical baseline calculation and threshold breach detection."""
    async with get_db_session() as session:
        proj = await get_or_create_test_project(session, "AIOps Project")

        # Ingest baseline metrics (low latency ~ 50ms)
        for i in range(10):
            session.add(
                TelemetryMetricRecord(
                    project_id=proj.id,
                    metric_name="test.latency",
                    metric_value=50.0 + (i % 3),
                    unit="ms",
                    timestamp=datetime.utcnow() - timedelta(minutes=15 - i),
                )
            )
        # Ingest an anomalous spike (800ms)
        session.add(
            TelemetryMetricRecord(
                project_id=proj.id,
                metric_name="test.latency",
                metric_value=850.0,
                unit="ms",
                timestamp=datetime.utcnow(),
            )
        )
        await session.commit()

        detector = AIOpsAnomalyDetector()
        anomalies = await detector.detect_anomalies(
            db=session,
            project_id=proj.id,
            metric_name="test.latency",
        )
        assert len(anomalies) >= 1
        assert anomalies[0]["value"] == 850.0
        assert anomalies[0]["z_score"] > 2.0


@pytest.mark.asyncio
async def test_alert_manager_fingerprint_deduplication():
    """Verify alert rule evaluation, SHA-256 fingerprint deduplication, and suppression."""
    async with get_db_session() as session:
        proj = await get_or_create_test_project(session, "Alert Project")

        alert_mgr = AlertManager()
        rule = await alert_mgr.create_rule(
            db=session,
            project_id=proj.id,
            name="High CPU Alert",
            metric_name="system.cpu_percent",
            condition=">",
            threshold=80.0,
            severity="high",
        )
        assert rule.id is not None

        # First evaluation: breach threshold (92% > 80%) -> Alert fires
        events1 = await alert_mgr.evaluate_metric_against_rules(
            db=session,
            project_id=proj.id,
            metric_name="system.cpu_percent",
            current_value=92.0,
        )
        assert len(events1) == 1
        first_event = events1[0]
        assert first_event.status == "firing"
        assert first_event.metric_value == 92.0

        # Second evaluation immediately after: duplicate fingerprint within suppression window
        events2 = await alert_mgr.evaluate_metric_against_rules(
            db=session,
            project_id=proj.id,
            metric_name="system.cpu_percent",
            current_value=95.0,
        )
        # Suppressed due to active firing deduplication window
        assert len(events2) == 0


@pytest.mark.asyncio
async def test_incident_lifecycle_and_rca_agent():
    """Verify incident creation, automated RCA correlation, and lifecycle transitions."""
    async with get_db_session() as session:
        proj = await get_or_create_test_project(session, "Incident Project")

        # Create simulated recent deployment release
        release = DeploymentRelease(
            project_id=proj.id,
            version="v2.4.0-test",
            commit_sha="a1b2c3d4e5f6",
            environment="production",
            status="active",
            created_at=datetime.utcnow() - timedelta(minutes=5),
        )
        session.add(release)

        # Ingest error rate spike
        session.add(
            TelemetryMetricRecord(
                project_id=proj.id,
                metric_name="application.error_rate",
                metric_value=12.5,
                unit="percent",
                timestamp=datetime.utcnow(),
            )
        )
        await session.commit()

        inc_mgr = IncidentManager()
        incident = await inc_mgr.create_manual_incident(
            db=session,
            project_id=proj.id,
            title="Production Error Rate Spike",
            affected_service="payment-gateway",
            severity="critical",
            environment="production",
            impact_summary="Payment transactions failing following recent deployment",
        )
        assert incident.status == "detected"

        # Run automated RCA
        rca_agent = RootCauseAnalysisAgent()
        rca = await rca_agent.investigate_incident(db=session, incident_id=incident.id)

        assert rca.incident_id == incident.id
        assert rca.confidence_score >= 0.8
        assert rca.recommended_action == "rollback_release"
        assert rca.healing_tier == 2

        # Verify incident status transitioned
        await session.refresh(incident)
        assert incident.status == "rca_completed"

        # Transition to resolved
        updated_inc = await inc_mgr.transition_status(
            db=session,
            incident_id=incident.id,
            new_status="resolved",
            notes="Rollback verified successfully",
        )
        assert updated_inc.status == "resolved"
        assert updated_inc.resolved_at is not None


@pytest.mark.asyncio
async def test_self_healing_3_tier_policy_and_rate_limits():
    """Verify Tier 1 autonomous actions, Tier 2 approval gating, Tier 3 restriction, and rate limits."""
    async with get_db_session() as session:
        proj = await get_or_create_test_project(session, "Healing Project")
        engine = SelfHealingEngine()

        # 1. Tier 1 Action: Autonomous execution (restart_container)
        a1 = await engine.execute_healing_action(
            db=session,
            project_id=proj.id,
            action_type="restart_container",
            parameters={"service": "frontend", "container_id": "c-01"},
        )
        assert a1.tier == 1
        assert a1.status == "succeeded"
        assert "health probe returned HTTP 200 OK" in a1.execution_log

        # 2. Tier 2 Action: Requires approval (scale_service)
        a2 = await engine.execute_healing_action(
            db=session,
            project_id=proj.id,
            action_type="scale_service",
            parameters={"service": "backend", "target_replicas": 3},
            force_approved=False,
        )
        assert a2.tier == 2
        assert a2.status == "pending_approval"
        assert a2.approval_id is not None

        # 3. Tier 3 Action: Strictly restricted / Human only
        a3 = await engine.execute_healing_action(
            db=session,
            project_id=proj.id,
            action_type="database_migration_revert",
            parameters={"target_version": "v1.0"},
        )
        assert a3.tier == 3
        assert a3.status == "pending_approval"
        assert "strictly restricted" in a3.execution_log

        # 4. Rate Limiting: Max 3 actions per 15 minutes
        # Already executed 1 restart_container; execute 2 more
        await engine.execute_healing_action(db=session, project_id=proj.id, action_type="restart_container")
        await engine.execute_healing_action(db=session, project_id=proj.id, action_type="restart_container")

        # 4th action trips the circuit breaker
        a4 = await engine.execute_healing_action(db=session, project_id=proj.id, action_type="restart_container")
        assert a4.status == "failed"
        assert "Circuit breaker tripped" in a4.execution_log


@pytest.mark.asyncio
async def test_slo_manager_and_finops_intelligence():
    """Verify SLO evaluation, error budget consumption, and FinOps analysis."""
    async with get_db_session() as session:
        proj = await get_or_create_test_project(session, "SLO Project")

        # Ingest healthy HTTP telemetry
        for _ in range(20):
            session.add(
                TelemetryMetricRecord(
                    project_id=proj.id,
                    metric_name="http.status_code",
                    metric_value=200,
                    unit="code",
                    timestamp=datetime.utcnow() - timedelta(hours=1),
                )
            )
        await session.commit()

        # Configure SLO: 99.9% target
        slo_mgr = SLOManager()
        slo = await slo_mgr.configure_slo(
            db=session,
            project_id=proj.id,
            name="Availability SLO",
            target_percentage=99.9,
            evaluation_window_days=30,
        )
        assert slo.id is not None

        evaluated_slo = await slo_mgr.evaluate_slo(db=session, slo_id=slo.id)
        assert evaluated_slo.current_sli == 100.0
        assert evaluated_slo.error_budget_remaining_percent == 100.0
        assert evaluated_slo.status == "healthy"

        # Reliability metrics
        rel_metrics = await slo_mgr.calculate_incident_mttr_metrics(db=session, project_id=proj.id)
        assert "mttr_minutes" in rel_metrics
        assert "mtta_minutes" in rel_metrics

        # FinOps analysis
        finops = CostIntelligenceEngine()
        costs = await finops.analyze_costs(db=session, project_id=proj.id)
        assert costs["total_spend_usd"] > 0
        assert "llm_tokens" in costs["breakdown"]

        recs = await finops.get_optimization_recommendations(db=session, project_id=proj.id)
        assert len(recs) >= 1


@pytest.mark.asyncio
async def test_observability_fastapi_endpoints():
    """Verify FastAPI observability REST endpoints."""
    async with get_db_session() as session:
        proj = await get_or_create_test_project(session, "API Test Project")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Ingest metric
        m_res = await client.post(
            "/api/v1/observability/metrics",
            json={
                "project_id": proj.id,
                "metric_name": "api.latency",
                "metric_value": 45.2,
                "unit": "ms",
            },
        )
        assert m_res.status_code == 200
        assert m_res.json()["status"] == "ingested"

        # List metrics
        list_m = await client.get(f"/api/v1/observability/metrics?project_id={proj.id}")
        assert list_m.status_code == 200
        assert len(list_m.json()) >= 1

        # Probe endpoint
        probe_res = await client.post(
            "/api/v1/observability/probe",
            json={"project_id": proj.id, "endpoint_url": "http://test/health"},
        )
        assert probe_res.status_code == 200
        assert "is_healthy" in probe_res.json()

        # Reliability metrics
        rel_res = await client.get(f"/api/v1/observability/reliability/metrics?project_id={proj.id}")
        assert rel_res.status_code == 200
        assert "mttr_minutes" in rel_res.json()

        # FinOps costs
        costs_res = await client.get(f"/api/v1/observability/finops/costs?project_id={proj.id}")
        assert costs_res.status_code == 200
        assert "total_spend_usd" in costs_res.json()
