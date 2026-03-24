from __future__ import annotations

from datetime import datetime
from sqlalchemy import Integer, Numeric, String, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class TablespaceMetric(Base):
    __tablename__ = "recsignal_tablespace_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    db_instance_id: Mapped[int] = mapped_column(Integer, ForeignKey("recsignal_db_instances.id"), nullable=False)
    tablespace_name: Mapped[str] = mapped_column(String(128), nullable=False)
    total_mb: Mapped[float | None] = mapped_column(Numeric(14, 2))
    used_mb: Mapped[float | None] = mapped_column(Numeric(14, 2))
    free_mb: Mapped[float | None] = mapped_column(Numeric(14, 2))
    used_percent: Mapped[float | None] = mapped_column(Numeric(5, 2))
    autoextensible: Mapped[str | None] = mapped_column(String(3))  # YES / NO
    max_mb: Mapped[float | None] = mapped_column(Numeric(14, 2))
    status: Mapped[str | None] = mapped_column(String(20))  # ONLINE, OFFLINE, READ ONLY
    collected_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
