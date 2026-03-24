from __future__ import annotations

import asyncio
import logging
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import verify_api_key
from app.core.websocket_manager import manager
from app.schemas.agent import AgentMetricsPayload, AgentMetricsResponse
from app.services.host_service import get_or_create_host
from app.services.metrics_service import (
    upsert_latest_metrics, insert_history_if_due, insert_mount_metrics, insert_process_snapshots,
)
from app.services.alert_service import evaluate_alerts, get_open_alerts_for_host
from app.services.notification_service import send_alert_email
from app.services.dashboard_service import get_dashboard_summary
from app.utils.status import compute_host_status
from app.utils.datetime_utils import is_stale
from app.core.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter()


def _build_host_broadcast(host, payload: AgentMetricsPayload, status: str) -> dict:
    """Build a lightweight dict for WebSocket broadcast."""
    return {
        "id": host.id,
        "hostname": host.hostname,
        "ip_address": host.ip_address,
        "environment": host.environment,
        "status": status,
        "cpu_percent": payload.cpu_percent,
        "memory_percent": payload.memory_percent,
        "swap_percent": payload.swap_percent,
        "disk_percent_total": payload.disk_percent_total,
        "load_avg_1m": payload.load_avg_1m,
        "disk_read_bytes_sec": payload.disk_read_bytes_sec,
        "disk_write_bytes_sec": payload.disk_write_bytes_sec,
        "disk_read_iops": payload.disk_read_iops,
        "disk_write_iops": payload.disk_write_iops,
        "net_bytes_sent_sec": payload.net_bytes_sent_sec,
        "net_bytes_recv_sec": payload.net_bytes_recv_sec,
        "open_fds": payload.open_fds,
        "max_fds": payload.max_fds,
        "process_count": payload.process_count,
        "zombie_count": payload.zombie_count,
        "last_heartbeat_at": payload.collected_at.isoformat() if payload.collected_at else None,
    }


@router.post("/api/agent/metrics", response_model=AgentMetricsResponse)
async def ingest_metrics(
    payload: AgentMetricsPayload,
    db: Session = Depends(get_db),
    _api_key: str = Depends(verify_api_key),
):
    """Receive metrics from a Unix agent (live — every 10s)."""
    settings = get_settings()

    # 1. Register / update host
    host = get_or_create_host(db, payload.hostname, payload.ip_address, payload.environment)

    # 2. Evaluate alerts to determine status
    new_alerts = evaluate_alerts(db, host.id, payload)
    open_alerts = get_open_alerts_for_host(db, host.id)
    host_stale = is_stale(host.last_seen_at, settings.STALE_THRESHOLD_MINUTES)
    status = compute_host_status(
        [{"severity": a.severity} for a in open_alerts],
        host_stale,
    )

    # 3. Store metrics (latest always, history only every HISTORY_INTERVAL_SECONDS)
    upsert_latest_metrics(db, host.id, payload, status=status)
    insert_history_if_due(db, host.id, payload, settings.HISTORY_INTERVAL_SECONDS)
    insert_mount_metrics(db, host.id, payload)
    insert_process_snapshots(db, host.id, payload)

    # 4. Send emails for new alerts
    for alert in new_alerts:
        send_alert_email(db, alert, host)

    db.commit()
    logger.info("Ingested metrics for host %s (id=%s, status=%s)", host.hostname, host.id, status)

    # 5. Broadcast to WebSocket clients
    host_data = _build_host_broadcast(host, payload, status)
    dashboard_data = _serialize_dashboard(get_dashboard_summary(db))
    alert_data = [
        {
            "id": a.id,
            "host_id": a.host_id,
            "metric_name": a.metric_name,
            "mount_path": a.mount_path,
            "severity": a.severity,
            "message": a.message,
            "status": a.status,
            "triggered_at": a.triggered_at.isoformat() if a.triggered_at else None,
            "resolved_at": a.resolved_at.isoformat() if a.resolved_at else None,
        }
        for a in new_alerts
    ]

    await manager.broadcast("dashboard", dashboard_data)
    await manager.broadcast("hosts", host_data)
    await manager.broadcast(f"host:{host.id}", host_data)
    if alert_data:
        await manager.broadcast("alerts", {"new_alerts": alert_data})

    return AgentMetricsResponse(success=True, message="Metrics received", host_id=host.id)


def _serialize_dashboard(summary) -> dict:
    """Convert dashboard summary to a JSON-safe dict."""
    return {
        "total_hosts": summary.total_hosts,
        "healthy_hosts": summary.healthy_hosts,
        "warning_hosts": summary.warning_hosts,
        "critical_hosts": summary.critical_hosts,
        "stale_hosts": summary.stale_hosts,
        "active_alerts": summary.active_alerts,
    }
