from __future__ import annotations


def compute_host_status(open_alerts: list[dict], is_stale: bool) -> str:
    """Derive host status from open alerts and staleness.

    Priority: critical > warning > stale > healthy
    """
    if is_stale:
        return "stale"
    severities = {a.get("severity") for a in open_alerts}
    if "critical" in severities:
        return "critical"
    if "warning" in severities:
        return "warning"
    return "healthy"
