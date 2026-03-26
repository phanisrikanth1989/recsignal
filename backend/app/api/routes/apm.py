from __future__ import annotations

import logging
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import verify_api_key
from app.services.host_service import get_or_create_host
from app.services import bt_service, tracing_service, baseline_service, log_service, diagnostic_service
from app.schemas.apm import (
    # Business Transactions
    BtAgentPayload, BtAgentResponse, BusinessTransactionItem, BtSummary,
    # Tracing
    TraceAgentPayload, TraceAgentResponse, TraceListItem, TraceDetail, SpanItem,
    # Baselines & Anomalies
    BaselineItem, AnomalyItem, AnomalySummary,
    # Logs
    LogAgentPayload, LogAgentResponse, LogItem, LogSearchResult, LogSummary,
    # Topology
    TopologyGraph, ServiceNodeItem, ServiceDependencyItem,
    # Diagnostics
    DiagnosticPayload, DiagnosticResponse, DiagnosticSnapshotItem,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/apm")


# ═══════════════════════════════════════════════════════════════════
# BUSINESS TRANSACTIONS
# ═══════════════════════════════════════════════════════════════════

@router.post("/transactions/ingest", response_model=BtAgentResponse)
def ingest_transactions(
    payload: BtAgentPayload,
    db: Session = Depends(get_db),
    _api_key: str = Depends(verify_api_key),
):
    """Ingest business transactions from an agent."""
    host = get_or_create_host(db, payload.hostname)
    tx_dicts = [t.model_dump() for t in payload.transactions]
    count = bt_service.insert_transactions(db, host.id, tx_dicts)
    db.commit()
    logger.info("Ingested %d transactions for host %s", count, payload.hostname)

    return BtAgentResponse(success=True, message="Transactions received", count=count)


@router.get("/transactions", response_model=list[BusinessTransactionItem])
def list_transactions(
    app_name: str | None = None,
    limit: int = Query(200, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    return bt_service.get_transactions(db, app_name=app_name, limit=limit, offset=offset)


@router.get("/transactions/summary", response_model=list[BtSummary])
def transaction_summary(db: Session = Depends(get_db)):
    return bt_service.get_bt_summary(db)


@router.get("/transactions/apps", response_model=list[str])
def list_app_names(db: Session = Depends(get_db)):
    return bt_service.get_app_names(db)


# ═══════════════════════════════════════════════════════════════════
# DISTRIBUTED TRACING
# ═══════════════════════════════════════════════════════════════════

@router.post("/traces/ingest", response_model=TraceAgentResponse)
def ingest_traces(
    payload: TraceAgentPayload,
    db: Session = Depends(get_db),
    _api_key: str = Depends(verify_api_key),
):
    """Ingest traces and spans from an agent."""
    count = 0
    for trace_payload in payload.traces:
        td = trace_payload.model_dump()
        tracing_service.insert_trace(db, td)
        count += 1
    db.commit()
    logger.info("Ingested %d traces for host %s", count, payload.hostname)

    return TraceAgentResponse(success=True, message="Traces received", count=count)


@router.get("/traces", response_model=list[TraceListItem])
def list_traces(
    service: str | None = None,
    has_error: bool | None = None,
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    return tracing_service.get_traces(db, service=service, has_error=has_error, limit=limit)


@router.get("/traces/{trace_id}")
def trace_detail(trace_id: str, db: Session = Depends(get_db)):
    result = tracing_service.get_trace_detail(db, trace_id)
    if not result:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Trace not found")
    trace = result["trace"]
    spans = result["spans"]
    return TraceDetail(
        id=trace.id,
        trace_id=trace.trace_id,
        root_service=trace.root_service,
        root_endpoint=trace.root_endpoint,
        root_method=trace.root_method,
        status_code=trace.status_code,
        total_duration_ms=trace.total_duration_ms,
        span_count=trace.span_count,
        has_error=trace.has_error,
        started_at=trace.started_at,
        spans=[SpanItem.model_validate(s) for s in spans],
    )


@router.get("/services", response_model=list[str])
def list_services(db: Session = Depends(get_db)):
    return tracing_service.get_services(db)


# ═══════════════════════════════════════════════════════════════════
# SERVICE TOPOLOGY / FLOWMAP
# ═══════════════════════════════════════════════════════════════════

@router.get("/topology", response_model=TopologyGraph)
def get_topology(db: Session = Depends(get_db)):
    result = tracing_service.get_topology(db)
    return TopologyGraph(
        nodes=[ServiceNodeItem.model_validate(n) for n in result["nodes"]],
        edges=[ServiceDependencyItem.model_validate(e) for e in result["edges"]],
    )


# ═══════════════════════════════════════════════════════════════════
# BASELINES & ANOMALY DETECTION
# ═══════════════════════════════════════════════════════════════════

@router.post("/baselines/compute/{host_id}", response_model=list[BaselineItem])
def compute_baselines(host_id: int, db: Session = Depends(get_db)):
    """Recompute baselines for a host."""
    baselines = baseline_service.compute_baselines(db, host_id)
    db.commit()
    return [BaselineItem.model_validate(b) for b in baselines]


@router.get("/baselines/{host_id}", response_model=list[BaselineItem])
def get_baselines(host_id: int, db: Session = Depends(get_db)):
    return baseline_service.get_baselines(db, host_id)


@router.get("/anomalies", response_model=list[AnomalyItem])
def list_anomalies(
    host_id: int | None = None,
    status: str | None = None,
    limit: int = Query(200, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    return baseline_service.get_anomalies(db, host_id=host_id, status=status, limit=limit)


@router.get("/anomalies/summary", response_model=AnomalySummary)
def anomaly_summary(db: Session = Depends(get_db)):
    return baseline_service.get_anomaly_summary(db)


# ═══════════════════════════════════════════════════════════════════
# LOG ANALYTICS
# ═══════════════════════════════════════════════════════════════════

@router.post("/logs/ingest", response_model=LogAgentResponse)
def ingest_logs(
    payload: LogAgentPayload,
    db: Session = Depends(get_db),
    _api_key: str = Depends(verify_api_key),
):
    """Ingest logs from an agent."""
    host = get_or_create_host(db, payload.hostname)
    log_dicts = [lg.model_dump() for lg in payload.logs]
    count = log_service.insert_logs(db, host.id, host.hostname, log_dicts)
    db.commit()
    logger.info("Ingested %d logs for host %s", count, payload.hostname)

    return LogAgentResponse(success=True, message="Logs received", count=count)


@router.get("/logs", response_model=LogSearchResult)
def search_logs(
    query: str | None = None,
    host_id: int | None = None,
    level: str | None = None,
    source: str | None = None,
    limit: int = Query(200, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    return log_service.search_logs(
        db, query=query, host_id=host_id, level=level, source=source, limit=limit, offset=offset,
    )


@router.get("/logs/summary", response_model=LogSummary)
def log_summary(db: Session = Depends(get_db)):
    return log_service.get_log_summary(db)


@router.get("/logs/sources", response_model=list[str])
def log_sources(db: Session = Depends(get_db)):
    return log_service.get_log_sources(db)


# ═══════════════════════════════════════════════════════════════════
# CODE-LEVEL DIAGNOSTICS
# ═══════════════════════════════════════════════════════════════════

@router.post("/diagnostics/ingest", response_model=DiagnosticResponse)
def ingest_diagnostic(
    payload: DiagnosticPayload,
    db: Session = Depends(get_db),
    _api_key: str = Depends(verify_api_key),
):
    """Ingest a diagnostic snapshot (CPU profile, memory profile, thread dump)."""
    host = get_or_create_host(db, payload.hostname)
    data = payload.model_dump()
    snapshot = diagnostic_service.insert_diagnostic(db, host.id, data)
    db.commit()
    logger.info("Ingested %s diagnostic for %s", payload.snapshot_type, payload.hostname)

    return DiagnosticResponse(success=True, message="Snapshot received", snapshot_id=snapshot.id)


@router.get("/diagnostics", response_model=list[DiagnosticSnapshotItem])
def list_diagnostics(
    app_name: str | None = None,
    snapshot_type: str | None = None,
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    return diagnostic_service.get_diagnostics(db, app_name=app_name, snapshot_type=snapshot_type, limit=limit)


@router.get("/diagnostics/{snapshot_id}", response_model=DiagnosticSnapshotItem)
def diagnostic_detail(snapshot_id: int, db: Session = Depends(get_db)):
    snap = diagnostic_service.get_diagnostic_by_id(db, snapshot_id)
    if not snap:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Snapshot not found")
    return snap
