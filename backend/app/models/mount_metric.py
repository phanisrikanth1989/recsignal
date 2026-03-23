from __future__ import annotations

from datetime import datetime
from sqlalchemy import Integer, Numeric, String, DateTime, ForeignKey, Index, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class MountMetric(Base):
    __tablename__ = "recsignal_mount_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    host_id: Mapped[int] = mapped_column(Integer, ForeignKey("recsignal_hosts.id"), nullable=False)
    mount_path: Mapped[str] = mapped_column(String(512), nullable=False)
    total_gb: Mapped[float | None] = mapped_column(Numeric(14, 2))
    used_gb: Mapped[float | None] = mapped_column(Numeric(14, 2))
    used_percent: Mapped[float | None] = mapped_column(Numeric(5, 2))
    inode_total: Mapped[int | None] = mapped_column(Integer)
    inode_used: Mapped[int | None] = mapped_column(Integer)
    inode_percent: Mapped[float | None] = mapped_column(Numeric(5, 2))
    collected_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    __table_args__ = (
        Index("recsignal_idx_mm_host_time", "host_id", collected_at.desc()),
    )
