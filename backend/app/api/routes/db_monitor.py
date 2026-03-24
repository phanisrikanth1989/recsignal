from __future__ import annotations

import logging
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import verify_api_key
from app.core.websocket_manager import manager
from app.schemas.db_monitor import (
    DbAgentMetricsPayload,
    DbAgentMetricsResponse,
    DbInstanceListItem,
    DbInstanceDetail,
    DbMonitorSummary,
    DbDashboardDetails,
    DbSessionItem,
    SlowQueryItem,
    TablespaceItem,
)
from app.services.db_monitor_service import (
    get_or_create_db_instance,
    compute_db_status,
    upsert_tablespace_metrics,
    upsert_session_snapshots,
    upsert_performance_metrics,
    upsert_slow_queries,
    get_all_db_instances,
    get_db_instance_detail,
    get_db_sessions,
    get_db_monitor_summary,
    get_db_dashboard_details,
)

logger = logging.getLogger(__name__)
router = APIRouter()


# ---------------------------------------------------------------------------
# Agent ingest endpoint
# ---------------------------------------------------------------------------

@router.post("/api/db-monitor/metrics", response_model=DbAgentMetricsResponse)
async def ingest_db_metrics(
    payload: DbAgentMetricsPayload,
    db: Session = Depends(get_db),
    _api_key: str = Depends(verify_api_key),
):
    """Receive DB metrics from an Oracle agent / collector."""
    instance = get_or_create_db_instance(db, payload)

    ts_rows = upsert_tablespace_metrics(db, instance.id, payload)
    upsert_session_snapshots(db, instance.id, payload)
    perf = upsert_performance_metrics(db, instance.id, payload)
    upsert_slow_queries(db, instance.id, payload)

    # Compute status
    status = compute_db_status(ts_rows, perf)
    instance.status = status
    db.commit()

    logger.info(
        "Ingested DB metrics for %s (id=%s, status=%s, tablespaces=%d)",
        instance.instance_name, instance.id, status, len(ts_rows),
    )

    # Broadcast to WebSocket clients
    instance_data = _build_db_instance_broadcast(instance, perf, ts_rows, status)
    summary_data = _serialize_db_summary(get_db_monitor_summary(db))

    await manager.broadcast("db-monitor-summary", summary_data)
    await manager.broadcast("db-instances", instance_data)
    await manager.broadcast(f"db-instance:{instance.id}", instance_data)

    return DbAgentMetricsResponse(success=True, message="DB metrics received", db_instance_id=instance.id)


def _build_db_instance_broadcast(instance, perf, tablespaces, status: str) -> dict:
    """Build a lightweight dict for WebSocket broadcast."""
    return {
        "id": instance.id,
        "instance_name": instance.instance_name,
        "db_type": instance.db_type,
        "host": instance.host,
        "port": instance.port,
        "service_name": instance.service_name,
        "environment": instance.environment,
        "status": status,
        "is_active": instance.is_active,
        "last_seen_at": instance.last_seen_at.isoformat() if instance.last_seen_at else None,
        "performance": {
            "buffer_cache_hit_ratio": perf.buffer_cache_hit_ratio if perf else None,
            "library_cache_hit_ratio": perf.library_cache_hit_ratio if perf else None,
            "active_sessions": perf.active_sessions if perf else None,
            "total_sessions": perf.total_sessions if perf else None,
            "max_sessions": perf.max_sessions if perf else None,
            "sga_total_mb": perf.sga_total_mb if perf else None,
            "pga_total_mb": perf.pga_total_mb if perf else None,
            "execute_count": perf.execute_count if perf else None,
            "physical_reads": perf.physical_reads if perf else None,
            "physical_writes": perf.physical_writes if perf else None,
            "db_uptime_seconds": perf.db_uptime_seconds if perf else None,
        } if perf else None,
        "tablespace_count": len(tablespaces),
        "tablespace_warnings": sum(1 for ts in tablespaces if ts.used_percent and ts.used_percent > 85),
    }


def _serialize_db_summary(summary) -> dict:
    """Convert DB monitor summary to a JSON-safe dict."""
    return {
        "total_instances": summary.total_instances,
        "up_instances": summary.up_instances,
        "down_instances": summary.down_instances,
        "degraded_instances": summary.degraded_instances,
        "total_active_sessions": summary.total_active_sessions,
        "total_tablespace_warnings": summary.total_tablespace_warnings,
    }


# ---------------------------------------------------------------------------
# Dashboard / List endpoints
# ---------------------------------------------------------------------------

@router.get("/api/db-monitor/summary", response_model=DbMonitorSummary)
def db_monitor_summary(db: Session = Depends(get_db)):
    """Summary stats for the DB Monitor dashboard tab."""
    return get_db_monitor_summary(db)


@router.get("/api/db-monitor/dashboard-details", response_model=DbDashboardDetails)
def db_dashboard_details(db: Session = Depends(get_db)):
    """Aggregate dashboard widgets: tablespace warnings, top slow queries, blocking sessions."""
    return get_db_dashboard_details(db)


@router.get("/api/db-monitor/instances", response_model=list[DbInstanceListItem])
def list_db_instances(db: Session = Depends(get_db)):
    """List all registered DB instances."""
    return get_all_db_instances(db)


@router.get("/api/db-monitor/instances/{instance_id}", response_model=DbInstanceDetail)
def db_instance_detail(instance_id: int, db: Session = Depends(get_db)):
    """Full detail view of a DB instance including tablespaces, performance, sessions, and slow queries."""
    detail = get_db_instance_detail(db, instance_id)
    if not detail:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="DB instance not found")
    return detail


@router.get("/api/db-monitor/instances/{instance_id}/sessions", response_model=list[DbSessionItem])
def db_instance_sessions(
    instance_id: int,
    status: str | None = None,
    db: Session = Depends(get_db),
):
    """Get session snapshots for a DB instance."""
    return get_db_sessions(db, instance_id, status_filter=status)


@router.get("/api/db-monitor/instances/{instance_id}/tablespaces", response_model=list[TablespaceItem])
def db_instance_tablespaces(instance_id: int, db: Session = Depends(get_db)):
    """Get tablespace metrics for a DB instance."""
    from app.models.tablespace_metric import TablespaceMetric
    return (
        db.query(TablespaceMetric)
        .filter(TablespaceMetric.db_instance_id == instance_id)
        .order_by(TablespaceMetric.used_percent.desc())
        .all()
    )


@router.get("/api/db-monitor/instances/{instance_id}/slow-queries", response_model=list[SlowQueryItem])
def db_instance_slow_queries(instance_id: int, limit: int = 20, db: Session = Depends(get_db)):
    """Get top slow queries for a DB instance."""
    from app.models.db_slow_query import DbSlowQuery
    return (
        db.query(DbSlowQuery)
        .filter(DbSlowQuery.db_instance_id == instance_id)
        .order_by(DbSlowQuery.elapsed_seconds.desc())
        .limit(limit)
        .all()
    )
