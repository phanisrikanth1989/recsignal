from __future__ import annotations

from datetime import datetime
from sqlalchemy import Integer, Numeric, String, DateTime, ForeignKey, Index, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ProcessSnapshot(Base):
    __tablename__ = "recsignal_process_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    host_id: Mapped[int] = mapped_column(Integer, ForeignKey("recsignal_hosts.id"), nullable=False)
    pid: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    username: Mapped[str | None] = mapped_column(String(128))
    cpu_percent: Mapped[float | None] = mapped_column(Numeric(6, 1))
    memory_percent: Mapped[float | None] = mapped_column(Numeric(6, 1))
    status: Mapped[str | None] = mapped_column(String(32))
    collected_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    __table_args__ = (
        Index("recsignal_idx_ps_host_time", "host_id", collected_at.desc()),
    )
