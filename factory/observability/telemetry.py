"""
OpenTelemetry Tracing & Telemetry Collection Core.
Provides W3C TraceContext compliant distributed tracing, span lifecycle management,
and correlated metric recording across application services and cloud workers.
"""

import time
import secrets
from datetime import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from factory.core.database import get_db_session
from factory.core.logger import logger
from factory.models.schema import TelemetryMetricRecord


def generate_trace_id() -> str:
    """Generate W3C 128-bit hex trace ID (32 hex characters)."""
    return secrets.token_hex(16)


def generate_span_id() -> str:
    """Generate W3C 64-bit hex span ID (16 hex characters)."""
    return secrets.token_hex(8)


class Span(BaseModel):
    name: str
    trace_id: str
    span_id: str = Field(default_factory=generate_span_id)
    parent_span_id: Optional[str] = None
    service_name: str = "ai-software-factory"
    start_time: float = Field(default_factory=time.time)
    end_time: Optional[float] = None
    duration_ms: Optional[float] = None
    status: str = "OK"  # OK, ERROR
    attributes: Dict[str, Any] = Field(default_factory=dict)
    events: List[Dict[str, Any]] = Field(default_factory=list)

    def set_attribute(self, key: str, value: Any):
        self.attributes[key] = value

    def record_exception(self, exc: Exception):
        self.attributes["error.message"] = str(exc)
        self.status = "ERROR"

    def to_w3c_traceparent(self) -> str:
        """Serialize to standard W3C traceparent header format."""
        return f"00-{self.trace_id}-{self.span_id}-01"

    def finish(self, status: str = "OK", error_message: Optional[str] = None):
        self.end_time = time.time()
        self.duration_ms = round((self.end_time - self.start_time) * 1000.0, 2)
        self.status = status
        if error_message:
            self.attributes["error.message"] = error_message
        return self


class TelemetryCollector:
    """In-memory trace buffer and database metric persistence engine."""

    _active_spans: Dict[str, Span] = {}
    _completed_spans: List[Span] = []
    _metric_buffer: List[TelemetryMetricRecord] = []

    @classmethod
    def start_span(
        cls,
        name: str,
        trace_id: Optional[str] = None,
        parent_span_id: Optional[str] = None,
        service_name: str = "ai-software-factory",
        attributes: Optional[Dict[str, Any]] = None,
    ) -> Span:
        t_id = trace_id or generate_trace_id()
        s_id = generate_span_id()
        span = Span(
            name=name,
            trace_id=t_id,
            span_id=s_id,
            parent_span_id=parent_span_id,
            service_name=service_name,
            attributes=attributes or {},
        )
        cls._active_spans[s_id] = span
        return span

    @classmethod
    def end_span(cls, span_id: str, status: str = "OK", error: Optional[str] = None) -> Optional[Span]:
        span = cls._active_spans.pop(span_id, None)
        if span:
            span.finish(status=status, error_message=error)
            cls._completed_spans.append(span)
            if len(cls._completed_spans) > 1000:
                cls._completed_spans.pop(0)
        return span

    @classmethod
    def get_traces_for_project(cls, project_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        matched = [
            s.model_dump()
            for s in cls._completed_spans
            if s.attributes.get("project_id") == project_id
        ]
        return matched[-limit:]

    @classmethod
    def record_metric(
        cls,
        project_id: str,
        metric_name: str,
        value: float,
        unit: str = "count",
        dimensions: Optional[Dict[str, Any]] = None,
    ) -> TelemetryMetricRecord:
        """Buffer a metric record for atomic batch flush."""
        record = TelemetryMetricRecord(
            project_id=project_id,
            metric_name=metric_name,
            metric_value=float(value),
            unit=unit,
            dimensions=dimensions or {},
            timestamp=datetime.utcnow(),
        )
        cls._metric_buffer.append(record)
        return record

    @classmethod
    async def flush_to_db(cls, session: Optional[AsyncSession] = None) -> int:
        """Flush all buffered telemetry metric records to the database."""
        if not cls._metric_buffer:
            return 0

        to_flush = list(cls._metric_buffer)
        cls._metric_buffer.clear()

        if session:
            for rec in to_flush:
                session.add(rec)
            await session.commit()
            return len(to_flush)
        else:
            async with get_db_session() as s:
                for rec in to_flush:
                    s.add(rec)
                await s.commit()
            return len(to_flush)
