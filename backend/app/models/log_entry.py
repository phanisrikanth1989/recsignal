from __future__ import annotations

from datetime import datetime
from sqlalchemy import String, Integer, DateTime, Text, Index, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class LogEntry(Base):
    __tablename__ = "recsignal_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    host_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    hostname: Mapped[str] = mapped_column(String(255), nullable=False)
    source: Mapped[str] = mapped_column(String(255), nullable=False)  # file path or app name
    level: Mapped[str] = mapped_column(String(20), nullable=False, index=True)  # INFO, WARN, ERROR, FATAL, DEBUG
    message: Mapped[str] = mapped_column(Text, nullable=False)
    trace_id: Mapped[str | None] = mapped_column(String(64), index=True)
    logged_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    __table_args__ = (
        Index("ix_log_host_logged", "host_id", "logged_at"),
        Index("ix_log_level_logged", "level", "logged_at"),
    )
