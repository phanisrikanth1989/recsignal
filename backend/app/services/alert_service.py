from __future__ import annotations

import logging
from sqlalchemy.orm import Session

from app.models.alert import Alert
from app.models.alert_rule import AlertRule
from app.models.metrics_latest import MetricsLatest
from app.models.mount_metric import MountMetric
from app.schemas.agent import AgentMetricsPayload
from app.utils.datetime_utils import utc_now

logger = logging.getLogger(__name__)


def _build_alert_key(host_id: int, metric_name: str, severity: str, mount_path: str | None = None) -> str:
    key = f"{host_id}:{metric_name}:{severity}"
    if mount_path:
        key += f":{mount_path}"
    return key


def _check_threshold(value: float, operator: str, threshold: float) -> bool:
    if operator == ">":
        return value > threshold
    if operator == ">=":
        return value >= threshold
    if operator == "<":
        return value < threshold
    if operator == "<=":
        return value <= threshold
    return False


def _open_alert(
    db: Session,
    host_id: int,
    metric_name: str,
    metric_value: float,
    severity: str,
    mount_path: str | None = None,
) -> Alert | None:
    """Create alert if no open alert for this key exists."""
    alert_key = _build_alert_key(host_id, metric_name, severity, mount_path)
    existing = (
        db.query(Alert)
        .filter(Alert.alert_key == alert_key, Alert.status == "OPEN")
        .first()
    )
    if existing:
        return None  # already open, don't duplicate

    mp_display = f" on {mount_path}" if mount_path else ""
    msg = f"{metric_name} is {metric_value:.1f}% ({severity}){mp_display}"

    alert = Alert(
        host_id=host_id,
        alert_key=alert_key,
        metric_name=metric_name,
        mount_path=mount_path,
        severity=severity,
        message=msg,
        status="OPEN",
        triggered_at=utc_now(),
    )
    db.add(alert)
    db.flush()
    logger.warning("Alert opened: %s", msg)
    return alert


def _resolve_alerts(db: Session, host_id: int, metric_name: str, mount_path: str | None = None) -> int:
    """Resolve all open alerts matching this host + metric + mount."""
    now = utc_now()
    query = db.query(Alert).filter(
        Alert.host_id == host_id,
        Alert.metric_name == metric_name,
        Alert.status == "OPEN",
    )
    if mount_path:
        query = query.filter(Alert.mount_path == mount_path)
    else:
        query = query.filter(Alert.mount_path.is_(None))

    open_alerts = query.all()
    count = 0
    for a in open_alerts:
        a.status = "RESOLVED"
        a.resolved_at = now
        a.updated_at = now
        count += 1
    if count:
        db.flush()
        logger.info("Resolved %d alert(s) for host_id=%s metric=%s", count, host_id, metric_name)
    return count


def evaluate_alerts(db: Session, host_id: int, payload: AgentMetricsPayload) -> list[Alert]:
    """Evaluate all active rules against the incoming metrics. Returns newly created alerts."""
    rules = db.query(AlertRule).filter(AlertRule.is_active == 1).all()
    new_alerts: list[Alert] = []

    # Map metric names to payload values
    metric_values = {
        "cpu_percent": payload.cpu_percent,
        "memory_percent": payload.memory_percent,
        "disk_percent_total": payload.disk_percent_total,
    }

    for rule in rules:
        # Handle mount-level rules separately
        if rule.metric_name == "mount_used_percent":
            for m in payload.mounts:
                if _check_threshold(m.used_percent, rule.operator, float(rule.threshold_value)):
                    alert = _open_alert(db, host_id, rule.metric_name, m.used_percent, rule.severity, m.mount_path)
                    if alert:
                        new_alerts.append(alert)
                else:
                    _resolve_alerts(db, host_id, rule.metric_name, m.mount_path)
            continue

        value = metric_values.get(rule.metric_name)
        if value is None:
            continue

        if _check_threshold(value, rule.operator, float(rule.threshold_value)):
            alert = _open_alert(db, host_id, rule.metric_name, value, rule.severity)
            if alert:
                new_alerts.append(alert)
        else:
            _resolve_alerts(db, host_id, rule.metric_name)

    return new_alerts


def get_open_alerts_for_host(db: Session, host_id: int) -> list[Alert]:
    return (
        db.query(Alert)
        .filter(Alert.host_id == host_id, Alert.status == "OPEN")
        .order_by(Alert.triggered_at.desc())
        .all()
    )


def get_all_alerts(db: Session, status: str | None = None, limit: int = 200) -> list[Alert]:
    q = db.query(Alert)
    if status:
        q = q.filter(Alert.status == status)
    return q.order_by(Alert.created_at.desc()).limit(limit).all()


def count_active_alerts(db: Session) -> int:
    return db.query(Alert).filter(Alert.status == "OPEN").count()
