from __future__ import annotations

import logging
import statistics
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.metrics_history import MetricsHistory
from app.models.baseline import MetricBaseline, Anomaly
from app.models.host import Host
from app.utils.datetime_utils import utc_now

logger = logging.getLogger(__name__)

# Metrics to baseline
BASELINE_METRICS = ["cpu_percent", "memory_percent", "swap_percent", "disk_percent_total", "load_avg_1m"]

# Anomaly thresholds in standard deviations
ANOMALY_WARNING_SIGMA = 2.0
ANOMALY_CRITICAL_SIGMA = 3.0
MIN_SAMPLES = 10  # Need at least 10 data points for a meaningful baseline


def compute_baselines(db: Session, host_id: int, window_hours: int = 24) -> list[MetricBaseline]:
    """Compute rolling baselines for a host from metrics_history."""
    now = utc_now()
    cutoff = now - timedelta(hours=window_hours)

    history = (
        db.query(MetricsHistory)
        .filter(MetricsHistory.host_id == host_id, MetricsHistory.collected_at >= cutoff)
        .order_by(MetricsHistory.collected_at)
        .all()
    )

    if len(history) < MIN_SAMPLES:
        logger.debug("Not enough samples for host %s (%d < %d)", host_id, len(history), MIN_SAMPLES)
        return []

    baselines = []
    for metric_name in BASELINE_METRICS:
        values = [getattr(h, metric_name) for h in history if getattr(h, metric_name) is not None]
        if len(values) < MIN_SAMPLES:
            continue

        mean_val = statistics.mean(values)
        stddev_val = statistics.stdev(values) if len(values) > 1 else 0.0

        # Upsert baseline
        existing = (
            db.query(MetricBaseline)
            .filter(MetricBaseline.host_id == host_id, MetricBaseline.metric_name == metric_name)
            .first()
        )
        if existing:
            existing.mean = mean_val
            existing.stddev = stddev_val
            existing.min_val = min(values)
            existing.max_val = max(values)
            existing.sample_count = len(values)
            existing.window_hours = window_hours
            existing.computed_at = now
            baselines.append(existing)
        else:
            bl = MetricBaseline(
                host_id=host_id,
                metric_name=metric_name,
                mean=mean_val,
                stddev=stddev_val,
                min_val=min(values),
                max_val=max(values),
                sample_count=len(values),
                window_hours=window_hours,
                computed_at=now,
            )
            db.add(bl)
            baselines.append(bl)

    db.flush()
    return baselines


def detect_anomalies(db: Session, host_id: int, current_metrics: dict) -> list[Anomaly]:
    """Check current metrics against baselines and create anomalies."""
    now = utc_now()
    new_anomalies = []

    baselines = (
        db.query(MetricBaseline)
        .filter(MetricBaseline.host_id == host_id)
        .all()
    )

    for baseline in baselines:
        value = current_metrics.get(baseline.metric_name)
        if value is None:
            continue

        # Skip if stddev is too low (constant metric)
        if baseline.stddev < 0.1:
            continue

        deviation = abs(value - baseline.mean) / baseline.stddev

        if deviation >= ANOMALY_CRITICAL_SIGMA:
            severity = "critical"
        elif deviation >= ANOMALY_WARNING_SIGMA:
            severity = "warning"
        else:
            # No anomaly — resolve any open ones
            _resolve_anomaly(db, host_id, baseline.metric_name, now)
            continue

        # Check for existing open anomaly
        existing = (
            db.query(Anomaly)
            .filter(
                Anomaly.host_id == host_id,
                Anomaly.metric_name == baseline.metric_name,
                Anomaly.status == "OPEN",
            )
            .first()
        )
        if existing:
            existing.observed_value = value
            existing.deviation_sigma = round(deviation, 2)
            existing.severity = severity
        else:
            anomaly = Anomaly(
                host_id=host_id,
                metric_name=baseline.metric_name,
                observed_value=value,
                baseline_mean=baseline.mean,
                baseline_stddev=baseline.stddev,
                deviation_sigma=round(deviation, 2),
                severity=severity,
                status="OPEN",
                detected_at=now,
            )
            db.add(anomaly)
            new_anomalies.append(anomaly)

    db.flush()
    return new_anomalies


def _resolve_anomaly(db: Session, host_id: int, metric_name: str, now: datetime):
    existing = (
        db.query(Anomaly)
        .filter(
            Anomaly.host_id == host_id,
            Anomaly.metric_name == metric_name,
            Anomaly.status == "OPEN",
        )
        .first()
    )
    if existing:
        existing.status = "RESOLVED"
        existing.resolved_at = now


def get_baselines(db: Session, host_id: int) -> list[MetricBaseline]:
    return db.query(MetricBaseline).filter(MetricBaseline.host_id == host_id).all()


def get_anomalies(
    db: Session,
    host_id: int | None = None,
    status: str | None = None,
    limit: int = 200,
) -> list[dict]:
    q = db.query(Anomaly, Host.hostname).outerjoin(Host, Anomaly.host_id == Host.id)
    if host_id:
        q = q.filter(Anomaly.host_id == host_id)
    if status:
        q = q.filter(Anomaly.status == status)
    rows = q.order_by(desc(Anomaly.detected_at)).limit(limit).all()
    results = []
    for anomaly, hostname in rows:
        results.append({
            "id": anomaly.id,
            "host_id": anomaly.host_id,
            "hostname": hostname,
            "metric_name": anomaly.metric_name,
            "observed_value": anomaly.observed_value,
            "baseline_mean": anomaly.baseline_mean,
            "baseline_stddev": anomaly.baseline_stddev,
            "deviation_sigma": anomaly.deviation_sigma,
            "severity": anomaly.severity,
            "status": anomaly.status,
            "detected_at": anomaly.detected_at,
            "resolved_at": anomaly.resolved_at,
        })
    return results


def get_anomaly_summary(db: Session) -> dict:
    from sqlalchemy import func
    total = db.query(func.count(Anomaly.id)).scalar() or 0
    open_count = db.query(func.count(Anomaly.id)).filter(Anomaly.status == "OPEN").scalar() or 0
    warning = db.query(func.count(Anomaly.id)).filter(Anomaly.status == "OPEN", Anomaly.severity == "warning").scalar() or 0
    critical = db.query(func.count(Anomaly.id)).filter(Anomaly.status == "OPEN", Anomaly.severity == "critical").scalar() or 0
    return {
        "total_anomalies": total,
        "open_anomalies": open_count,
        "warning_count": warning,
        "critical_count": critical,
    }
