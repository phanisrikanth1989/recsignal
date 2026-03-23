from __future__ import annotations

import logging
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.metrics_latest import MetricsLatest
from app.models.metrics_history import MetricsHistory
from app.models.mount_metric import MountMetric
from app.schemas.agent import AgentMetricsPayload
from app.utils.datetime_utils import utc_now

logger = logging.getLogger(__name__)


def upsert_latest_metrics(db: Session, host_id: int, payload: AgentMetricsPayload, status: str = "healthy") -> MetricsLatest:
    """Insert or update the latest metrics row for a host."""
    now = utc_now()
    latest = db.query(MetricsLatest).filter(MetricsLatest.host_id == host_id).first()
    if latest:
        latest.cpu_percent = payload.cpu_percent
        latest.memory_percent = payload.memory_percent
        latest.disk_percent_total = payload.disk_percent_total
        latest.load_avg_1m = payload.load_avg_1m
        latest.status = status
        latest.last_heartbeat_at = now
        latest.collected_at = payload.collected_at
        latest.updated_at = now
    else:
        latest = MetricsLatest(
            host_id=host_id,
            cpu_percent=payload.cpu_percent,
            memory_percent=payload.memory_percent,
            disk_percent_total=payload.disk_percent_total,
            load_avg_1m=payload.load_avg_1m,
            status=status,
            last_heartbeat_at=now,
            collected_at=payload.collected_at,
        )
        db.add(latest)
    db.flush()
    return latest


def insert_history(db: Session, host_id: int, payload: AgentMetricsPayload) -> MetricsHistory:
    """Append a row to metrics_history."""
    row = MetricsHistory(
        host_id=host_id,
        cpu_percent=payload.cpu_percent,
        memory_percent=payload.memory_percent,
        disk_percent_total=payload.disk_percent_total,
        load_avg_1m=payload.load_avg_1m,
        collected_at=payload.collected_at,
    )
    db.add(row)
    db.flush()
    return row


def insert_mount_metrics(db: Session, host_id: int, payload: AgentMetricsPayload) -> list[MountMetric]:
    """Insert mount-level metrics."""
    rows = []
    for m in payload.mounts:
        row = MountMetric(
            host_id=host_id,
            mount_path=m.mount_path,
            total_gb=m.total_gb,
            used_gb=m.used_gb,
            used_percent=m.used_percent,
            collected_at=payload.collected_at,
        )
        db.add(row)
        rows.append(row)
    db.flush()
    return rows


def get_latest_metrics(db: Session, host_id: int) -> MetricsLatest | None:
    return db.query(MetricsLatest).filter(MetricsLatest.host_id == host_id).first()


def get_history(db: Session, host_id: int, limit: int = 96) -> list[MetricsHistory]:
    """Get recent metric history (default 96 = 24h at 15-min intervals)."""
    return (
        db.query(MetricsHistory)
        .filter(MetricsHistory.host_id == host_id)
        .order_by(MetricsHistory.collected_at.desc())
        .limit(limit)
        .all()
    )


def get_latest_mounts(db: Session, host_id: int) -> list[MountMetric]:
    """Get the most recent mount metrics for a host."""
    # Subquery to find the latest collected_at for this host
    latest_time = (
        db.query(MountMetric.collected_at)
        .filter(MountMetric.host_id == host_id)
        .order_by(MountMetric.collected_at.desc())
        .limit(1)
        .scalar()
    )
    if not latest_time:
        return []
    return (
        db.query(MountMetric)
        .filter(MountMetric.host_id == host_id, MountMetric.collected_at == latest_time)
        .all()
    )
