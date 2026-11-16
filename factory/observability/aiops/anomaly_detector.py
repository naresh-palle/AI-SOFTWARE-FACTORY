"""
Intelligent AIOps Anomaly Detection Engine.
Calculates statistical baseline metrics and detects anomalous operational behavior
such as CPU spikes, memory leaks, latency degradation, error rate surges, and queue backlogs.
"""

import math
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy import select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from factory.models.schema import TelemetryMetricRecord


class AnomalyReport:
    """Represents a detected operational anomaly with supporting telemetry evidence."""

    def __init__(
        self,
        metric_name: str,
        current_value: float,
        baseline_value: float,
        deviation_factor: float,
        severity: str,
        hypothesis: str,
        evidence: Dict[str, Any],
    ):
        self.metric_name = metric_name
        self.current_value = current_value
        self.baseline_value = baseline_value
        self.deviation_factor = deviation_factor
        self.severity = severity
        self.hypothesis = hypothesis
        self.evidence = evidence
        self.detected_at = datetime.utcnow().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric_name": self.metric_name,
            "current_value": self.current_value,
            "baseline_value": self.baseline_value,
            "deviation_factor": round(self.deviation_factor, 2),
            "severity": self.severity,
            "hypothesis": self.hypothesis,
            "evidence": self.evidence,
            "detected_at": self.detected_at,
        }


class AIOpsAnomalyDetector:
    """Evaluates telemetry streams against statistical baselines to detect anomalous patterns."""

    DEFAULT_BASELINES = {
        "system.cpu_percent": {"mean": 25.0, "std": 10.0, "critical_threshold": 85.0},
        "system.memory_percent": {"mean": 45.0, "std": 12.0, "critical_threshold": 90.0},
        "application.latency_ms": {"mean": 45.0, "std": 20.0, "critical_threshold": 500.0},
        "application.error_rate": {"mean": 0.5, "std": 0.5, "critical_threshold": 5.0},
        "queue.backlog_depth": {"mean": 2.0, "std": 2.0, "critical_threshold": 25.0},
    }

    @classmethod
    def evaluate_metric(
        cls,
        metric_name: str,
        value: float,
        custom_baseline: Optional[Dict[str, float]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Evaluate a metric value against baseline. Returns anomaly dict if anomalous, else None."""
        base = custom_baseline or cls.DEFAULT_BASELINES.get(metric_name)
        if not base:
            return None

        mean = base["mean"]
        std = max(1.0, base["std"])
        critical_thresh = base["critical_threshold"]

        deviation = (value - mean) / std

        # 1. Critical Threshold Breach
        if value >= critical_thresh:
            rep = AnomalyReport(
                metric_name=metric_name,
                current_value=value,
                baseline_value=mean,
                deviation_factor=deviation,
                severity="critical" if value > critical_thresh * 1.1 else "high",
                hypothesis=f"Severe breach of {metric_name} ({value} exceeds critical limit of {critical_thresh})",
                evidence={"threshold": critical_thresh, "std_deviations": round(deviation, 2)},
            )
            return rep.to_dict()

        # 2. Significant Statistical Outlier (> 3 standard deviations)
        if deviation >= 3.0:
            rep = AnomalyReport(
                metric_name=metric_name,
                current_value=value,
                baseline_value=mean,
                deviation_factor=deviation,
                severity="medium",
                hypothesis=f"Statistical anomaly in {metric_name} ({round(deviation, 1)} standard deviations above baseline)",
                evidence={"baseline_mean": mean, "deviation": round(deviation, 2)},
            )
            return rep.to_dict()

        return None

    async def detect_anomalies(
        self,
        db: AsyncSession,
        project_id: str,
        metric_name: str,
    ) -> List[Dict[str, Any]]:
        """Query historical metrics from DB, compute dynamic z-score baseline, and detect outliers."""
        q = (
            select(TelemetryMetricRecord)
            .where(
                and_(
                    TelemetryMetricRecord.project_id == project_id,
                    TelemetryMetricRecord.metric_name == metric_name,
                )
            )
            .order_by(desc(TelemetryMetricRecord.timestamp))
            .limit(50)
        )
        res = await db.execute(q)
        records = list(res.scalars().all())

        if len(records) < 2:
            return []

        values = [r.metric_value for r in records]
        mean = sum(values) / len(values)
        variance = sum((v - mean) ** 2 for v in values) / len(values)
        std_dev = max(1.0, math.sqrt(variance))

        anomalies = []
        for r in records[:5]:  # inspect recent records
            z_score = abs(r.metric_value - mean) / std_dev
            if z_score >= 2.0:
                anomalies.append({
                    "metric_name": metric_name,
                    "value": r.metric_value,
                    "baseline_mean": round(mean, 2),
                    "std_dev": round(std_dev, 2),
                    "z_score": round(z_score, 2),
                    "severity": "critical" if z_score > 3.0 else "high",
                    "timestamp": r.timestamp.isoformat() if r.timestamp else None,
                })

        return anomalies
