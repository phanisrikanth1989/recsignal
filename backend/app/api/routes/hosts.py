from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import get_settings
from app.models.metrics_latest import MetricsLatest
from app.models.process_snapshot import ProcessSnapshot
from app.schemas.host import HostListItem, HostDetail, MountUsage
from app.services.host_service import get_all_hosts, get_host_by_id
from app.services.metrics_service import get_latest_metrics, get_history, get_latest_mounts
from app.services.alert_service import get_open_alerts_for_host
from app.utils.datetime_utils import is_stale

router = APIRouter()


@router.get("/api/hosts", response_model=list[HostListItem])
def list_hosts(db: Session = Depends(get_db)):
    settings = get_settings()
    hosts = get_all_hosts(db)
    result = []
    for h in hosts:
        latest = db.query(MetricsLatest).filter(MetricsLatest.host_id == h.id).first()
        item = HostListItem(
            id=h.id,
            hostname=h.hostname,
            ip_address=h.ip_address,
            environment=h.environment,
            status=latest.status if latest and not is_stale(latest.last_heartbeat_at, settings.STALE_THRESHOLD_MINUTES) else "stale" if latest else "unknown",
            cpu_percent=float(latest.cpu_percent) if latest and latest.cpu_percent is not None else None,
            memory_percent=float(latest.memory_percent) if latest and latest.memory_percent is not None else None,
            disk_percent_total=float(latest.disk_percent_total) if latest and latest.disk_percent_total is not None else None,
            last_heartbeat_at=latest.last_heartbeat_at if latest else None,
        )
        result.append(item)
    return result


@router.get("/api/hosts/{host_id}", response_model=HostDetail)
def host_detail(host_id: int, db: Session = Depends(get_db)):
    host = get_host_by_id(db, host_id)
    if not host:
        raise HTTPException(status_code=404, detail="Host not found")

    latest = get_latest_metrics(db, host_id)
    mounts = get_latest_mounts(db, host_id)
    history = get_history(db, host_id, limit=96)
    open_alerts = get_open_alerts_for_host(db, host_id)

    return HostDetail(
        id=host.id,
        hostname=host.hostname,
        ip_address=host.ip_address,
        environment=host.environment,
        support_group=host.support_group,
        is_active=host.is_active,
        last_seen_at=host.last_seen_at,
        created_at=host.created_at,
        status=latest.status if latest else "unknown",
        cpu_percent=float(latest.cpu_percent) if latest and latest.cpu_percent is not None else None,
        memory_percent=float(latest.memory_percent) if latest and latest.memory_percent is not None else None,
        swap_percent=float(latest.swap_percent) if latest and latest.swap_percent is not None else None,
        disk_percent_total=float(latest.disk_percent_total) if latest and latest.disk_percent_total is not None else None,
        load_avg_1m=float(latest.load_avg_1m) if latest and latest.load_avg_1m is not None else None,
        disk_read_bytes_sec=float(latest.disk_read_bytes_sec) if latest and latest.disk_read_bytes_sec is not None else None,
        disk_write_bytes_sec=float(latest.disk_write_bytes_sec) if latest and latest.disk_write_bytes_sec is not None else None,
        disk_read_iops=float(latest.disk_read_iops) if latest and latest.disk_read_iops is not None else None,
        disk_write_iops=float(latest.disk_write_iops) if latest and latest.disk_write_iops is not None else None,
        net_bytes_sent_sec=float(latest.net_bytes_sent_sec) if latest and latest.net_bytes_sent_sec is not None else None,
        net_bytes_recv_sec=float(latest.net_bytes_recv_sec) if latest and latest.net_bytes_recv_sec is not None else None,
        open_fds=latest.open_fds if latest else None,
        max_fds=latest.max_fds if latest else None,
        process_count=latest.process_count if latest else None,
        zombie_count=latest.zombie_count if latest else None,
        boot_time=latest.boot_time if latest else None,
        last_heartbeat_at=latest.last_heartbeat_at if latest else None,
        collected_at=latest.collected_at if latest else None,
        mounts=[
            MountUsage(
                mount_path=m.mount_path,
                total_gb=float(m.total_gb) if m.total_gb else None,
                used_gb=float(m.used_gb) if m.used_gb else None,
                used_percent=float(m.used_percent) if m.used_percent else None,
                inode_total=m.inode_total,
                inode_used=m.inode_used,
                inode_percent=float(m.inode_percent) if m.inode_percent else None,
                collected_at=m.collected_at,
            )
            for m in mounts
        ],
        recent_history=[
            {
                "id": r.id,
                "cpu_percent": float(r.cpu_percent) if r.cpu_percent is not None else None,
                "memory_percent": float(r.memory_percent) if r.memory_percent is not None else None,
                "disk_percent_total": float(r.disk_percent_total) if r.disk_percent_total is not None else None,
                "load_avg_1m": float(r.load_avg_1m) if r.load_avg_1m is not None else None,
                "collected_at": r.collected_at.isoformat() if r.collected_at else None,
            }
            for r in history
        ],
        active_alerts=[
            {
                "id": a.id,
                "metric_name": a.metric_name,
                "severity": a.severity,
                "message": a.message,
                "triggered_at": a.triggered_at.isoformat() if a.triggered_at else None,
            }
            for a in open_alerts
        ],
    )


@router.get("/api/hosts/{host_id}/processes")
def host_processes(
    host_id: int,
    status_filter: str | None = None,
    db: Session = Depends(get_db),
):
    """Return the latest process snapshot for a host. Optionally filter by status (e.g. ?status_filter=zombie)."""
    host = get_host_by_id(db, host_id)
    if not host:
        raise HTTPException(status_code=404, detail="Host not found")

    query = db.query(ProcessSnapshot).filter(ProcessSnapshot.host_id == host_id)
    if status_filter:
        query = query.filter(ProcessSnapshot.status == status_filter)
    query = query.order_by(ProcessSnapshot.cpu_percent.desc())
    rows = query.all()

    return [
        {
            "pid": r.pid,
            "name": r.name,
            "username": r.username,
            "cpu_percent": float(r.cpu_percent) if r.cpu_percent is not None else 0.0,
            "memory_percent": float(r.memory_percent) if r.memory_percent is not None else 0.0,
            "status": r.status,
            "collected_at": r.collected_at.isoformat() if r.collected_at else None,
        }
        for r in rows
    ]
