from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel


class MountPayload(BaseModel):
    mount_path: str
    total_gb: float
    used_gb: float
    used_percent: float
    inode_total: int | None = None
    inode_used: int | None = None
    inode_percent: float | None = None


class ProcessPayload(BaseModel):
    pid: int
    name: str
    username: str = ""
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    status: str = "unknown"


class AgentMetricsPayload(BaseModel):
    hostname: str
    ip_address: str | None = None
    environment: str | None = "prod"
    cpu_percent: float
    memory_percent: float
    swap_percent: float | None = None
    disk_percent_total: float
    load_avg_1m: float
    disk_read_bytes_sec: float | None = None
    disk_write_bytes_sec: float | None = None
    disk_read_iops: float | None = None
    disk_write_iops: float | None = None
    net_bytes_sent_sec: float | None = None
    net_bytes_recv_sec: float | None = None
    open_fds: int | None = None
    max_fds: int | None = None
    process_count: int | None = None
    zombie_count: int | None = None
    boot_time: datetime | None = None
    processes: list[ProcessPayload] = []
    mounts: list[MountPayload] = []
    collected_at: datetime


class AgentMetricsResponse(BaseModel):
    success: bool = True
    message: str = "Metrics received"
    host_id: int | None = None
