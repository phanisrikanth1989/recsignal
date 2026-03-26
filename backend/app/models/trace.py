from __future__ import annotations

from datetime import datetime
from sqlalchemy import String, Integer, Float, DateTime, Text, Index, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Trace(Base):
    __tablename__ = "recsignal_traces"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    trace_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    root_service: Mapped[str] = mapped_column(String(255), nullable=False)
    root_endpoint: Mapped[str | None] = mapped_column(String(512))
    root_method: Mapped[str | None] = mapped_column(String(10))
    status_code: Mapped[int | None] = mapped_column(Integer)
    total_duration_ms: Mapped[float] = mapped_column(Float, nullable=False)
    span_count: Mapped[int] = mapped_column(Integer, default=1)
    has_error: Mapped[int] = mapped_column(Integer, default=0)
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    __table_args__ = (
        Index("ix_trace_service_started", "root_service", "started_at"),
    )


class Span(Base):
    __tablename__ = "recsignal_spans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    trace_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    span_id: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    parent_span_id: Mapped[str | None] = mapped_column(String(64))
    service_name: Mapped[str] = mapped_column(String(255), nullable=False)
    operation_name: Mapped[str] = mapped_column(String(512), nullable=False)
    span_kind: Mapped[str] = mapped_column(String(20), default="internal")  # server, client, internal, producer, consumer
    status: Mapped[str] = mapped_column(String(20), default="ok")  # ok, error
    duration_ms: Mapped[float] = mapped_column(Float, nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    attributes: Mapped[str | None] = mapped_column(Text)  # JSON string of key-value pairs
    events: Mapped[str | None] = mapped_column(Text)  # JSON string of span events/logs
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    __table_args__ = (
        Index("ix_span_trace_parent", "trace_id", "parent_span_id"),
    )
