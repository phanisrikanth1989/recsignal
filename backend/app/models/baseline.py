from __future__ import annotations

from datetime import datetime
from sqlalchemy import String, Integer, Float, DateTime, Index, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class MetricBaseline(Base):
    """Rolling statistical baselines per host per metric."""
    __tablename__ = "recsignal_metric_baselines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    host_id: Mapped[int] = mapped_column(Integer, nullable=False)
    metric_name: Mapped[str] = mapped_column(String(64), nullable=False)
    mean: Mapped[float] = mapped_column(Float, nullable=False)
    stddev: Mapped[float] = mapped_column(Float, nullable=False)
    min_val: Mapped[float] = mapped_column(Float, nullable=False)
    max_val: Mapped[float] = mapped_column(Float, nullable=False)
    sample_count: Mapped[int] = mapped_column(Integer, nullable=False)
    window_hours: Mapped[int] = mapped_column(Integer, default=24)
    computed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    __table_args__ = (
        Index("ix_baseline_host_metric", "host_id", "metric_name", unique=True),
    )


class Anomaly(Base):
    """Detected anomalies from baseline deviations."""
    __tablename__ = "recsignal_anomalies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    host_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    metric_name: Mapped[str] = mapped_column(String(64), nullable=False)
    observed_value: Mapped[float] = mapped_column(Float, nullable=False)
    baseline_mean: Mapped[float] = mapped_column(Float, nullable=False)
    baseline_stddev: Mapped[float] = mapped_column(Float, nullable=False)
    deviation_sigma: Mapped[float] = mapped_column(Float, nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)  # warning, critical
    status: Mapped[str] = mapped_column(String(20), default="OPEN")  # OPEN, RESOLVED
    detected_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    __table_args__ = (
        Index("ix_anomaly_host_status", "host_id", "status"),
    )
