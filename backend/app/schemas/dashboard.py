from __future__ import annotations

from pydantic import BaseModel


class DashboardSummary(BaseModel):
    total_hosts: int = 0
    healthy_hosts: int = 0
    warning_hosts: int = 0
    critical_hosts: int = 0
    stale_hosts: int = 0
    active_alerts: int = 0
