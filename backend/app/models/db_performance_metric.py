from __future__ import annotations

from datetime import datetime
from sqlalchemy import Integer, Numeric, String, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class DbPerformanceMetric(Base):
    __tablename__ = "recsignal_db_performance"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    db_instance_id: Mapped[int] = mapped_column(Integer, ForeignKey("recsignal_db_instances.id"), nullable=False)
    buffer_cache_hit_ratio: Mapped[float | None] = mapped_column(Numeric(5, 2))
    library_cache_hit_ratio: Mapped[float | None] = mapped_column(Numeric(5, 2))
    parse_count_total: Mapped[int | None] = mapped_column(Integer)
    hard_parse_count: Mapped[int | None] = mapped_column(Integer)
    execute_count: Mapped[int | None] = mapped_column(Integer)
    user_commits: Mapped[int | None] = mapped_column(Integer)
    user_rollbacks: Mapped[int | None] = mapped_column(Integer)
    physical_reads: Mapped[int | None] = mapped_column(Integer)
    physical_writes: Mapped[int | None] = mapped_column(Integer)
    redo_size: Mapped[int | None] = mapped_column(Integer)
    sga_total_mb: Mapped[float | None] = mapped_column(Numeric(14, 2))
    pga_total_mb: Mapped[float | None] = mapped_column(Numeric(14, 2))
    active_sessions: Mapped[int | None] = mapped_column(Integer)
    inactive_sessions: Mapped[int | None] = mapped_column(Integer)
    total_sessions: Mapped[int | None] = mapped_column(Integer)
    max_sessions: Mapped[int | None] = mapped_column(Integer)
    db_uptime_seconds: Mapped[int | None] = mapped_column(Integer)
    collected_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
