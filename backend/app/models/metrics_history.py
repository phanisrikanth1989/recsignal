from __future__ import annotations

from datetime import datetime
from sqlalchemy import Integer, Numeric, DateTime, ForeignKey, Index, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class MetricsHistory(Base):
    __tablename__ = "metrics_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    host_id: Mapped[int] = mapped_column(Integer, ForeignKey("hosts.id"), nullable=False)
    cpu_percent: Mapped[float | None] = mapped_column(Numeric(5, 2))
    memory_percent: Mapped[float | None] = mapped_column(Numeric(5, 2))
    disk_percent_total: Mapped[float | None] = mapped_column(Numeric(5, 2))
    load_avg_1m: Mapped[float | None] = mapped_column(Numeric(8, 4))
    collected_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    __table_args__ = (
        Index("idx_mh_host_time", "host_id", collected_at.desc()),
    )
