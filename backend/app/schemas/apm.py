from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel


# ── Business Transactions ─────────────────────────────────────────

class BusinessTransactionPayload(BaseModel):
    app_name: str
    endpoint: str
    method: str
    status_code: int
    response_time_ms: float
    is_error: int = 0
    error_message: str | None = None
    trace_id: str | None = None
    user_id: str | None = None
    collected_at: datetime


class BusinessTransactionItem(BaseModel):
    id: int
    host_id: int | None
    app_name: str
    endpoint: str
    method: str
    status_code: int
    response_time_ms: float
    is_error: int
    error_message: str | None
    trace_id: str | None
    collected_at: datetime

    class Config:
        from_attributes = True


class BtSummary(BaseModel):
    app_name: str
    total_requests: int
    avg_response_time_ms: float
    error_count: int
    error_rate: float
    p95_response_time_ms: float | None = None


class BtAgentPayload(BaseModel):
    """Batch of business transactions from an agent."""
    hostname: str
    transactions: list[BusinessTransactionPayload]


class BtAgentResponse(BaseModel):
    success: bool
    message: str
    count: int


# ── Distributed Tracing ──────────────────────────────────────────

class SpanPayload(BaseModel):
    span_id: str
    parent_span_id: str | None = None
    service_name: str
    operation_name: str
    span_kind: str = "internal"
    status: str = "ok"
    duration_ms: float
    started_at: datetime
    attributes: str | None = None  # JSON string
    events: str | None = None  # JSON string


class TracePayload(BaseModel):
    trace_id: str
    root_service: str
    root_endpoint: str | None = None
    root_method: str | None = None
    status_code: int | None = None
    total_duration_ms: float
    has_error: int = 0
    started_at: datetime
    spans: list[SpanPayload]


class SpanItem(BaseModel):
    id: int
    trace_id: str
    span_id: str
    parent_span_id: str | None
    service_name: str
    operation_name: str
    span_kind: str
    status: str
    duration_ms: float
    started_at: datetime
    attributes: str | None
    events: str | None

    class Config:
        from_attributes = True


class TraceListItem(BaseModel):
    id: int
    trace_id: str
    root_service: str
    root_endpoint: str | None
    root_method: str | None
    status_code: int | None
    total_duration_ms: float
    span_count: int
    has_error: int
    started_at: datetime

    class Config:
        from_attributes = True


class TraceDetail(TraceListItem):
    spans: list[SpanItem]


class TraceAgentPayload(BaseModel):
    """Batch of traces from an agent."""
    hostname: str
    traces: list[TracePayload]


class TraceAgentResponse(BaseModel):
    success: bool
    message: str
    count: int


# ── Baselines & Anomalies ────────────────────────────────────────

class BaselineItem(BaseModel):
    id: int
    host_id: int
    metric_name: str
    mean: float
    stddev: float
    min_val: float
    max_val: float
    sample_count: int
    window_hours: int
    computed_at: datetime

    class Config:
        from_attributes = True


class AnomalyItem(BaseModel):
    id: int
    host_id: int
    hostname: str | None = None
    metric_name: str
    observed_value: float
    baseline_mean: float
    baseline_stddev: float
    deviation_sigma: float
    severity: str
    status: str
    detected_at: datetime
    resolved_at: datetime | None

    class Config:
        from_attributes = True


class AnomalySummary(BaseModel):
    total_anomalies: int
    open_anomalies: int
    warning_count: int
    critical_count: int


# ── Log Analytics ─────────────────────────────────────────────────

class LogPayload(BaseModel):
    source: str
    level: str
    message: str
    trace_id: str | None = None
    logged_at: datetime


class LogAgentPayload(BaseModel):
    hostname: str
    logs: list[LogPayload]


class LogAgentResponse(BaseModel):
    success: bool
    message: str
    count: int


class LogItem(BaseModel):
    id: int
    host_id: int
    hostname: str
    source: str
    level: str
    message: str
    trace_id: str | None
    logged_at: datetime

    class Config:
        from_attributes = True


class LogSearchResult(BaseModel):
    total: int
    logs: list[LogItem]


class LogSummary(BaseModel):
    total_logs: int
    error_count: int
    warn_count: int
    info_count: int


# ── Service Topology ─────────────────────────────────────────────

class ServiceNodeItem(BaseModel):
    id: int
    service_name: str
    service_type: str
    host_id: int | None
    status: str
    avg_response_time_ms: float | None
    request_rate: float | None
    error_rate: float | None
    last_seen_at: datetime | None

    class Config:
        from_attributes = True


class ServiceDependencyItem(BaseModel):
    id: int
    source_service: str
    target_service: str
    call_count: int
    error_count: int
    avg_duration_ms: float | None
    last_seen_at: datetime

    class Config:
        from_attributes = True


class TopologyGraph(BaseModel):
    nodes: list[ServiceNodeItem]
    edges: list[ServiceDependencyItem]


# ── Code-Level Diagnostics ───────────────────────────────────────

class DiagnosticSnapshotItem(BaseModel):
    id: int
    host_id: int | None
    app_name: str
    snapshot_type: str
    duration_seconds: float | None
    top_functions: str | None  # JSON
    memory_summary: str | None  # JSON
    thread_dump: str | None  # JSON
    triggered_by: str | None
    collected_at: datetime

    class Config:
        from_attributes = True


class DiagnosticPayload(BaseModel):
    hostname: str
    app_name: str
    snapshot_type: str
    duration_seconds: float | None = None
    top_functions: str | None = None
    memory_summary: str | None = None
    thread_dump: str | None = None
    triggered_by: str | None = None
    collected_at: datetime


class DiagnosticResponse(BaseModel):
    success: bool
    message: str
    snapshot_id: int
