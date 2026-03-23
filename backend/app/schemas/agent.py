from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel


class MountPayload(BaseModel):
    mount_path: str
    total_gb: float
    used_gb: float
    used_percent: float


class AgentMetricsPayload(BaseModel):
    hostname: str
    ip_address: str | None = None
    environment: str | None = "prod"
    cpu_percent: float
    memory_percent: float
    disk_percent_total: float
    load_avg_1m: float
    mounts: list[MountPayload] = []
    collected_at: datetime


class AgentMetricsResponse(BaseModel):
    success: bool = True
    message: str = "Metrics received"
    host_id: int | None = None
