from __future__ import annotations

from datetime import datetime
from sqlalchemy import String, Integer, DateTime, Index, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ServiceDependency(Base):
    """Edges in the service topology graph, derived from trace data."""
    __tablename__ = "recsignal_service_dependencies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_service: Mapped[str] = mapped_column(String(255), nullable=False)
    target_service: Mapped[str] = mapped_column(String(255), nullable=False)
    call_count: Mapped[int] = mapped_column(Integer, default=0)
    error_count: Mapped[int] = mapped_column(Integer, default=0)
    avg_duration_ms: Mapped[float | None] = mapped_column(nullable=True)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("ix_svc_dep_pair", "source_service", "target_service", unique=True),
    )


class ServiceNode(Base):
    """Nodes in the service topology graph."""
    __tablename__ = "recsignal_service_nodes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    service_name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    service_type: Mapped[str] = mapped_column(String(50), default="service")  # service, database, queue, external
    host_id: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20), default="healthy")  # healthy, warning, critical
    avg_response_time_ms: Mapped[float | None] = mapped_column(nullable=True)
    request_rate: Mapped[float | None] = mapped_column(nullable=True)  # requests per minute
    error_rate: Mapped[float | None] = mapped_column(nullable=True)  # percentage
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
