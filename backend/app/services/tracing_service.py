from __future__ import annotations

import json
import logging
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.trace import Trace, Span
from app.models.service_topology import ServiceNode, ServiceDependency
from app.utils.datetime_utils import utc_now

logger = logging.getLogger(__name__)


def insert_trace(db: Session, trace_data: dict) -> Trace:
    """Insert a trace and its spans, update topology."""
    trace = Trace(
        trace_id=trace_data["trace_id"],
        root_service=trace_data["root_service"],
        root_endpoint=trace_data.get("root_endpoint"),
        root_method=trace_data.get("root_method"),
        status_code=trace_data.get("status_code"),
        total_duration_ms=trace_data["total_duration_ms"],
        span_count=len(trace_data.get("spans", [])),
        has_error=trace_data.get("has_error", 0),
        started_at=trace_data["started_at"],
    )
    db.add(trace)
    db.flush()

    # Insert spans
    services_seen = set()
    spans_by_id = {}
    span_objects = []
    for s in trace_data.get("spans", []):
        span = Span(
            trace_id=trace_data["trace_id"],
            span_id=s["span_id"],
            parent_span_id=s.get("parent_span_id"),
            service_name=s["service_name"],
            operation_name=s["operation_name"],
            span_kind=s.get("span_kind", "internal"),
            status=s.get("status", "ok"),
            duration_ms=s["duration_ms"],
            started_at=s["started_at"],
            attributes=s.get("attributes"),
            events=s.get("events"),
        )
        db.add(span)
        span_objects.append(span)
        spans_by_id[s["span_id"]] = s
        services_seen.add(s["service_name"])

    # Update service topology from spans
    _update_topology(db, span_objects, spans_by_id)

    db.flush()
    return trace


def _update_topology(db: Session, spans: list[Span], spans_by_id: dict):
    """Update service nodes and edges from span data."""
    now = utc_now()
    services = set()
    edges: dict[tuple[str, str], list[float]] = {}

    for span in spans:
        services.add(span.service_name)
        if span.parent_span_id and span.parent_span_id in spans_by_id:
            parent = spans_by_id[span.parent_span_id]
            parent_svc = parent["service_name"]
            if parent_svc != span.service_name:
                key = (parent_svc, span.service_name)
                edges.setdefault(key, []).append(span.duration_ms)

    # Upsert service nodes
    for svc_name in services:
        node = db.query(ServiceNode).filter(ServiceNode.service_name == svc_name).first()
        if not node:
            node = ServiceNode(service_name=svc_name, last_seen_at=now)
            db.add(node)
        else:
            node.last_seen_at = now

    # Upsert dependency edges
    for (src, tgt), durations in edges.items():
        dep = (
            db.query(ServiceDependency)
            .filter(ServiceDependency.source_service == src, ServiceDependency.target_service == tgt)
            .first()
        )
        avg_dur = sum(durations) / len(durations)
        if not dep:
            dep = ServiceDependency(
                source_service=src,
                target_service=tgt,
                call_count=len(durations),
                avg_duration_ms=avg_dur,
                last_seen_at=now,
            )
            db.add(dep)
        else:
            dep.call_count += len(durations)
            dep.avg_duration_ms = avg_dur
            dep.last_seen_at = now


def get_traces(
    db: Session,
    service: str | None = None,
    has_error: bool | None = None,
    limit: int = 100,
) -> list[Trace]:
    q = db.query(Trace)
    if service:
        q = q.filter(Trace.root_service == service)
    if has_error is not None:
        q = q.filter(Trace.has_error == (1 if has_error else 0))
    return q.order_by(desc(Trace.started_at)).limit(limit).all()


def get_trace_detail(db: Session, trace_id: str) -> dict | None:
    trace = db.query(Trace).filter(Trace.trace_id == trace_id).first()
    if not trace:
        return None
    spans = db.query(Span).filter(Span.trace_id == trace_id).order_by(Span.started_at).all()
    return {"trace": trace, "spans": spans}


def get_topology(db: Session) -> dict:
    nodes = db.query(ServiceNode).all()
    edges = db.query(ServiceDependency).all()
    return {"nodes": nodes, "edges": edges}


def get_services(db: Session) -> list[str]:
    rows = db.query(ServiceNode.service_name).distinct().all()
    return [r[0] for r in rows]
