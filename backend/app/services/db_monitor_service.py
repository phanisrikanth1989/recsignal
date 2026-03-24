from __future__ import annotations

import logging
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.db_instance import DbInstance
from app.models.tablespace_metric import TablespaceMetric
from app.models.db_session_snapshot import DbSessionSnapshot
from app.models.db_performance_metric import DbPerformanceMetric
from app.models.db_slow_query import DbSlowQuery
from app.schemas.db_monitor import (
    DbAgentMetricsPayload,
    DbMonitorSummary,
    DbInstanceDetail,
    DbSessionsSummary,
)
from app.utils.datetime_utils import utc_now

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Instance management
# ---------------------------------------------------------------------------

def get_or_create_db_instance(db: Session, payload: DbAgentMetricsPayload) -> DbInstance:
    """Register or update a DB instance."""
    now = utc_now()
    instance = db.query(DbInstance).filter(DbInstance.instance_name == payload.instance_name).first()
    if instance:
        instance.db_type = payload.db_type
        instance.host = payload.host
        instance.port = payload.port
        instance.service_name = payload.service_name
        instance.environment = payload.environment
        instance.last_seen_at = now
        instance.updated_at = now
    else:
        instance = DbInstance(
            instance_name=payload.instance_name,
            db_type=payload.db_type,
            host=payload.host,
            port=payload.port,
            service_name=payload.service_name,
            environment=payload.environment,
            last_seen_at=now,
            status="up",
        )
        db.add(instance)
        db.flush()
        logger.info("Registered new DB instance: %s (id=%s)", instance.instance_name, instance.id)
    return instance


def compute_db_status(tablespaces: list, performance) -> str:
    """Determine DB instance status from metrics."""
    if not performance:
        return "unknown"
    # Critical if any tablespace > 95%
    for ts in tablespaces:
        if ts.used_percent and ts.used_percent >= 95:
            return "degraded"
    # Warning if buffer cache hit ratio < 85%
    if performance.buffer_cache_hit_ratio and performance.buffer_cache_hit_ratio < 85:
        return "degraded"
    return "up"


# ---------------------------------------------------------------------------
# Metric ingestion
# ---------------------------------------------------------------------------

def upsert_tablespace_metrics(db: Session, db_instance_id: int, payload: DbAgentMetricsPayload) -> list[TablespaceMetric]:
    """Replace tablespace metrics for a DB instance."""
    # Delete previous snapshot
    db.query(TablespaceMetric).filter(TablespaceMetric.db_instance_id == db_instance_id).delete()
    rows = []
    for ts in payload.tablespaces:
        row = TablespaceMetric(
            db_instance_id=db_instance_id,
            tablespace_name=ts.tablespace_name,
            total_mb=ts.total_mb,
            used_mb=ts.used_mb,
            free_mb=ts.free_mb,
            used_percent=ts.used_percent,
            autoextensible=ts.autoextensible,
            max_mb=ts.max_mb,
            status=ts.status,
            collected_at=payload.collected_at,
        )
        db.add(row)
        rows.append(row)
    db.flush()
    return rows


def upsert_session_snapshots(db: Session, db_instance_id: int, payload: DbAgentMetricsPayload) -> int:
    """Replace session snapshots for a DB instance."""
    db.query(DbSessionSnapshot).filter(DbSessionSnapshot.db_instance_id == db_instance_id).delete()
    count = 0
    for s in payload.sessions:
        db.add(DbSessionSnapshot(
            db_instance_id=db_instance_id,
            sid=s.sid,
            serial_no=s.serial_no,
            username=s.username,
            program=s.program,
            machine=s.machine,
            status=s.status,
            sql_id=s.sql_id,
            sql_text=s.sql_text,
            wait_class=s.wait_class,
            wait_event=s.wait_event,
            seconds_in_wait=s.seconds_in_wait,
            blocking_session=s.blocking_session,
            logon_time=s.logon_time,
            elapsed_seconds=s.elapsed_seconds,
            collected_at=payload.collected_at,
        ))
        count += 1
    db.flush()
    return count


def upsert_performance_metrics(db: Session, db_instance_id: int, payload: DbAgentMetricsPayload) -> DbPerformanceMetric | None:
    """Insert or update performance metrics."""
    if not payload.performance:
        return None
    p = payload.performance
    # Delete old, insert new (snapshot approach)
    db.query(DbPerformanceMetric).filter(DbPerformanceMetric.db_instance_id == db_instance_id).delete()
    row = DbPerformanceMetric(
        db_instance_id=db_instance_id,
        buffer_cache_hit_ratio=p.buffer_cache_hit_ratio,
        library_cache_hit_ratio=p.library_cache_hit_ratio,
        parse_count_total=p.parse_count_total,
        hard_parse_count=p.hard_parse_count,
        execute_count=p.execute_count,
        user_commits=p.user_commits,
        user_rollbacks=p.user_rollbacks,
        physical_reads=p.physical_reads,
        physical_writes=p.physical_writes,
        redo_size=p.redo_size,
        sga_total_mb=p.sga_total_mb,
        pga_total_mb=p.pga_total_mb,
        active_sessions=p.active_sessions,
        inactive_sessions=p.inactive_sessions,
        total_sessions=p.total_sessions,
        max_sessions=p.max_sessions,
        db_uptime_seconds=p.db_uptime_seconds,
        collected_at=payload.collected_at,
    )
    db.add(row)
    db.flush()
    return row


def upsert_slow_queries(db: Session, db_instance_id: int, payload: DbAgentMetricsPayload) -> int:
    """Replace slow query snapshots."""
    db.query(DbSlowQuery).filter(DbSlowQuery.db_instance_id == db_instance_id).delete()
    count = 0
    for q in payload.slow_queries:
        db.add(DbSlowQuery(
            db_instance_id=db_instance_id,
            sql_id=q.sql_id,
            sql_text=q.sql_text,
            username=q.username,
            elapsed_seconds=q.elapsed_seconds,
            cpu_seconds=q.cpu_seconds,
            buffer_gets=q.buffer_gets,
            disk_reads=q.disk_reads,
            rows_processed=q.rows_processed,
            executions=q.executions,
            plan_hash_value=q.plan_hash_value,
            collected_at=payload.collected_at,
        ))
        count += 1
    db.flush()
    return count


# ---------------------------------------------------------------------------
# Query helpers
# ---------------------------------------------------------------------------

def get_all_db_instances(db: Session) -> list[DbInstance]:
    return db.query(DbInstance).order_by(DbInstance.instance_name).all()


def get_db_instance_detail(db: Session, instance_id: int) -> DbInstanceDetail | None:
    """Build a full detail view for a DB instance."""
    instance = db.query(DbInstance).filter(DbInstance.id == instance_id).first()
    if not instance:
        return None

    tablespaces = (
        db.query(TablespaceMetric)
        .filter(TablespaceMetric.db_instance_id == instance_id)
        .order_by(TablespaceMetric.used_percent.desc())
        .all()
    )

    performance = (
        db.query(DbPerformanceMetric)
        .filter(DbPerformanceMetric.db_instance_id == instance_id)
        .first()
    )

    sessions = (
        db.query(DbSessionSnapshot)
        .filter(DbSessionSnapshot.db_instance_id == instance_id)
        .all()
    )

    slow_queries = (
        db.query(DbSlowQuery)
        .filter(DbSlowQuery.db_instance_id == instance_id)
        .order_by(DbSlowQuery.elapsed_seconds.desc())
        .limit(20)
        .all()
    )

    # Build sessions summary
    active = sum(1 for s in sessions if s.status == "ACTIVE")
    inactive = sum(1 for s in sessions if s.status == "INACTIVE")
    blocking = sum(1 for s in sessions if s.blocking_session is not None and s.blocking_session > 0)
    long_running = sum(1 for s in sessions if s.elapsed_seconds and s.elapsed_seconds > 60)

    sessions_summary = DbSessionsSummary(
        active=active,
        inactive=inactive,
        total=len(sessions),
        blocking_count=blocking,
        long_running_count=long_running,
    )

    return DbInstanceDetail(
        id=instance.id,
        instance_name=instance.instance_name,
        db_type=instance.db_type,
        host=instance.host,
        port=instance.port,
        service_name=instance.service_name,
        environment=instance.environment,
        support_group=instance.support_group,
        status=instance.status,
        is_active=instance.is_active,
        last_seen_at=instance.last_seen_at,
        created_at=instance.created_at,
        tablespaces=[ts for ts in tablespaces],
        performance=performance,
        sessions_summary=sessions_summary,
        slow_queries=[q for q in slow_queries],
    )


def get_db_sessions(db: Session, instance_id: int, status_filter: str | None = None) -> list[DbSessionSnapshot]:
    """Get session snapshots, optionally filtered by status."""
    query = db.query(DbSessionSnapshot).filter(DbSessionSnapshot.db_instance_id == instance_id)
    if status_filter:
        query = query.filter(DbSessionSnapshot.status == status_filter.upper())
    return query.order_by(DbSessionSnapshot.elapsed_seconds.desc()).all()


def get_db_monitor_summary(db: Session) -> DbMonitorSummary:
    """Build a summary for the DB Monitor dashboard."""
    instances = db.query(DbInstance).filter(DbInstance.is_active == 1).all()
    up = sum(1 for i in instances if i.status == "up")
    down = sum(1 for i in instances if i.status == "down")
    degraded = sum(1 for i in instances if i.status == "degraded")

    # Count tablespace warnings (> 85%)
    ts_warnings = (
        db.query(TablespaceMetric)
        .filter(TablespaceMetric.used_percent > 85)
        .count()
    )

    # Sum active sessions
    total_active = 0
    for inst in instances:
        perf = db.query(DbPerformanceMetric).filter(DbPerformanceMetric.db_instance_id == inst.id).first()
        if perf and perf.active_sessions:
            total_active += perf.active_sessions

    return DbMonitorSummary(
        total_instances=len(instances),
        up_instances=up,
        down_instances=down,
        degraded_instances=degraded,
        total_active_sessions=total_active,
        total_tablespace_warnings=ts_warnings,
    )
