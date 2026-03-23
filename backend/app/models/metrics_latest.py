from __future__ import annotations

from datetime import datetime
from sqlalchemy import Integer, Numeric, String, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class MetricsLatest(Base):
    __tablename__ = "recsignal_metrics_latest"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    host_id: Mapped[int] = mapped_column(Integer, ForeignKey("recsignal_hosts.id"), unique=True, nullable=False)
    cpu_percent: Mapped[float | None] = mapped_column(Numeric(5, 2))
    memory_percent: Mapped[float | None] = mapped_column(Numeric(5, 2))
    swap_percent: Mapped[float | None] = mapped_column(Numeric(5, 2))
    disk_percent_total: Mapped[float | None] = mapped_column(Numeric(5, 2))
    load_avg_1m: Mapped[float | None] = mapped_column(Numeric(8, 4))
    disk_read_bytes_sec: Mapped[float | None] = mapped_column(Numeric(14, 2))
    disk_write_bytes_sec: Mapped[float | None] = mapped_column(Numeric(14, 2))
    disk_read_iops: Mapped[float | None] = mapped_column(Numeric(10, 2))
    disk_write_iops: Mapped[float | None] = mapped_column(Numeric(10, 2))
    net_bytes_sent_sec: Mapped[float | None] = mapped_column(Numeric(14, 2))
    net_bytes_recv_sec: Mapped[float | None] = mapped_column(Numeric(14, 2))
    open_fds: Mapped[int | None] = mapped_column(Integer)
    max_fds: Mapped[int | None] = mapped_column(Integer)
    process_count: Mapped[int | None] = mapped_column(Integer)
    zombie_count: Mapped[int | None] = mapped_column(Integer)
    boot_time: Mapped[datetime | None] = mapped_column(DateTime)
    status: Mapped[str] = mapped_column(String(20), default="unknown")
    last_heartbeat_at: Mapped[datetime | None] = mapped_column(DateTime)
    collected_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
