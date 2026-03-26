from __future__ import annotations

from datetime import datetime
from sqlalchemy import String, Integer, Float, DateTime, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class DiagnosticSnapshot(Base):
    """Code-level profiling snapshots captured on request."""
    __tablename__ = "recsignal_diagnostic_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    host_id: Mapped[int | None] = mapped_column(Integer, index=True)
    app_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    snapshot_type: Mapped[str] = mapped_column(String(50), nullable=False)  # cpu_profile, memory_profile, thread_dump
    duration_seconds: Mapped[float | None] = mapped_column(Float)
    top_functions: Mapped[str | None] = mapped_column(Text)  # JSON array of {function, file, line, cumtime, calls}
    memory_summary: Mapped[str | None] = mapped_column(Text)  # JSON: {rss_mb, vms_mb, top_allocations: [...]}
    thread_dump: Mapped[str | None] = mapped_column(Text)  # JSON array of {thread_id, name, state, stack: [...]}
    triggered_by: Mapped[str | None] = mapped_column(String(255))  # user or "auto"
    collected_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
