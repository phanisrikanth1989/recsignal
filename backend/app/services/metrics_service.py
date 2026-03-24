from __future__ import annotations

import logging
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.metrics_latest import MetricsLatest
from app.models.metrics_history import MetricsHistory
from app.models.mount_metric import MountMetric
from app.models.process_snapshot import ProcessSnapshot
from app.schemas.agent import AgentMetricsPayload
from app.utils.datetime_utils import utc_now

logger = logging.getLogger(__name__)

# In-memory tracker: last history write time per host_id
_last_history_write: dict[int, datetime] = {}


def upsert_latest_metrics(db: Session, host_id: int, payload: AgentMetricsPayload, status: str = "healthy") -> MetricsLatest:
    """Insert or update the latest metrics row for a host."""
    now = utc_now()
    latest = db.query(MetricsLatest).filter(MetricsLatest.host_id == host_id).first()
    if latest:
        latest.cpu_percent = payload.cpu_percent
        latest.memory_percent = payload.memory_percent
        latest.swap_percent = payload.swap_percent
        latest.disk_percent_total = payload.disk_percent_total
        latest.load_avg_1m = payload.load_avg_1m
        latest.disk_read_bytes_sec = payload.disk_read_bytes_sec
        latest.disk_write_bytes_sec = payload.disk_write_bytes_sec
        latest.disk_read_iops = payload.disk_read_iops
        latest.disk_write_iops = payload.disk_write_iops
        latest.net_bytes_sent_sec = payload.net_bytes_sent_sec
        latest.net_bytes_recv_sec = payload.net_bytes_recv_sec
        latest.open_fds = payload.open_fds
        latest.max_fds = payload.max_fds
        latest.process_count = payload.process_count
        latest.zombie_count = payload.zombie_count
        latest.boot_time = payload.boot_time
        latest.status = status
        latest.last_heartbeat_at = now
        latest.collected_at = payload.collected_at
        latest.updated_at = now
    else:
        latest = MetricsLatest(
            host_id=host_id,
            cpu_percent=payload.cpu_percent,
            memory_percent=payload.memory_percent,
            swap_percent=payload.swap_percent,
            disk_percent_total=payload.disk_percent_total,
            load_avg_1m=payload.load_avg_1m,
            disk_read_bytes_sec=payload.disk_read_bytes_sec,
            disk_write_bytes_sec=payload.disk_write_bytes_sec,
            disk_read_iops=payload.disk_read_iops,
            disk_write_iops=payload.disk_write_iops,
            net_bytes_sent_sec=payload.net_bytes_sent_sec,
            net_bytes_recv_sec=payload.net_bytes_recv_sec,
            open_fds=payload.open_fds,
            max_fds=payload.max_fds,
            process_count=payload.process_count,
            zombie_count=payload.zombie_count,
            boot_time=payload.boot_time,
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
        swap_percent=payload.swap_percent,
        disk_percent_total=payload.disk_percent_total,
        load_avg_1m=payload.load_avg_1m,
        disk_read_bytes_sec=payload.disk_read_bytes_sec,
        disk_write_bytes_sec=payload.disk_write_bytes_sec,
        disk_read_iops=payload.disk_read_iops,
        disk_write_iops=payload.disk_write_iops,
        net_bytes_sent_sec=payload.net_bytes_sent_sec,
        net_bytes_recv_sec=payload.net_bytes_recv_sec,
        open_fds=payload.open_fds,
        max_fds=payload.max_fds,
        process_count=payload.process_count,
        zombie_count=payload.zombie_count,
        boot_time=payload.boot_time,
        collected_at=payload.collected_at,
    )
    db.add(row)
    db.flush()
    return row


def insert_history_if_due(
    db: Session, host_id: int, payload: AgentMetricsPayload, interval_seconds: int = 300
) -> MetricsHistory | None:
    """Write to metrics_history only if enough time has passed since last write.

    With live 10-second ingestion, we downsample history writes to avoid
    database bloat. Default: one history row every 5 minutes.
    """
    now = utc_now()
    last_write = _last_history_write.get(host_id)
    if last_write is not None:
        elapsed = (now - last_write).total_seconds()
        if elapsed < interval_seconds:
            return None  # Skip — not due yet
    row = insert_history(db, host_id, payload)
    _last_history_write[host_id] = now
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
            inode_total=m.inode_total,
            inode_used=m.inode_used,
            inode_percent=m.inode_percent,
            collected_at=payload.collected_at,
        )
        db.add(row)
        rows.append(row)
    db.flush()
    return rows


def insert_process_snapshots(db: Session, host_id: int, payload: AgentMetricsPayload) -> int:
    """Replace the latest process snapshot for a host."""
    if not payload.processes:
        return 0
    # Delete previous snapshot
    db.query(ProcessSnapshot).filter(ProcessSnapshot.host_id == host_id).delete()
    for p in payload.processes:
        db.add(ProcessSnapshot(
            host_id=host_id,
            pid=p.pid,
            name=p.name,
            username=p.username,
            cpu_percent=p.cpu_percent,
            memory_percent=p.memory_percent,
            status=p.status,
            collected_at=payload.collected_at,
        ))
    db.flush()
    return len(payload.processes)


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
