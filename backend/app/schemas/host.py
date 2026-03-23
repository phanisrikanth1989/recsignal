from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel


class HostListItem(BaseModel):
    id: int
    hostname: str
    ip_address: str | None = None
    environment: str | None = None
    status: str = "unknown"
    cpu_percent: float | None = None
    memory_percent: float | None = None
    disk_percent_total: float | None = None
    last_heartbeat_at: datetime | None = None

    model_config = {"from_attributes": True}


class MountUsage(BaseModel):
    mount_path: str
    total_gb: float | None = None
    used_gb: float | None = None
    used_percent: float | None = None
    collected_at: datetime | None = None

    model_config = {"from_attributes": True}


class HostDetail(BaseModel):
    id: int
    hostname: str
    ip_address: str | None = None
    environment: str | None = None
    support_group: str | None = None
    is_active: int = 1
    last_seen_at: datetime | None = None
    created_at: datetime | None = None

    # Latest metrics
    status: str = "unknown"
    cpu_percent: float | None = None
    memory_percent: float | None = None
    disk_percent_total: float | None = None
    load_avg_1m: float | None = None
    last_heartbeat_at: datetime | None = None
    collected_at: datetime | None = None

    # Related data
    mounts: list[MountUsage] = []
    recent_history: list[dict] = []
    active_alerts: list[dict] = []
