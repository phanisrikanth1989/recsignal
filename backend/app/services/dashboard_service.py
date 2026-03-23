from __future__ import annotations

import logging
from sqlalchemy.orm import Session

from app.models.host import Host
from app.models.metrics_latest import MetricsLatest
from app.models.alert import Alert
from app.schemas.dashboard import DashboardSummary
from app.core.config import get_settings
from app.utils.datetime_utils import is_stale

logger = logging.getLogger(__name__)


def get_dashboard_summary(db: Session) -> DashboardSummary:
    """Compute dashboard summary counts."""
    settings = get_settings()
    hosts = db.query(Host).filter(Host.is_active == 1).all()

    total = len(hosts)
    healthy = 0
    warning = 0
    critical = 0
    stale = 0

    for host in hosts:
        latest = db.query(MetricsLatest).filter(MetricsLatest.host_id == host.id).first()
        if not latest or is_stale(latest.last_heartbeat_at, settings.STALE_THRESHOLD_MINUTES):
            stale += 1
            continue
        if latest.status == "critical":
            critical += 1
        elif latest.status == "warning":
            warning += 1
        else:
            healthy += 1

    active_alerts = db.query(Alert).filter(Alert.status == "OPEN").count()

    return DashboardSummary(
        total_hosts=total,
        healthy_hosts=healthy,
        warning_hosts=warning,
        critical_hosts=critical,
        stale_hosts=stale,
        active_alerts=active_alerts,
    )
