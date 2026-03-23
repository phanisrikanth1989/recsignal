from __future__ import annotations

import logging
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import verify_api_key
from app.schemas.agent import AgentMetricsPayload, AgentMetricsResponse
from app.services.host_service import get_or_create_host
from app.services.metrics_service import upsert_latest_metrics, insert_history, insert_mount_metrics
from app.services.alert_service import evaluate_alerts, get_open_alerts_for_host
from app.services.notification_service import send_alert_email
from app.utils.status import compute_host_status
from app.utils.datetime_utils import is_stale
from app.core.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/api/agent/metrics", response_model=AgentMetricsResponse)
def ingest_metrics(
    payload: AgentMetricsPayload,
    db: Session = Depends(get_db),
    _api_key: str = Depends(verify_api_key),
):
    """Receive metrics from a Unix agent."""
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

    # 3. Store metrics
    upsert_latest_metrics(db, host.id, payload, status=status)
    insert_history(db, host.id, payload)
    insert_mount_metrics(db, host.id, payload)

    # 4. Send emails for new alerts
    for alert in new_alerts:
        send_alert_email(db, alert, host)

    db.commit()
    logger.info("Ingested metrics for host %s (id=%s, status=%s)", host.hostname, host.id, status)

    return AgentMetricsResponse(success=True, message="Metrics received", host_id=host.id)
