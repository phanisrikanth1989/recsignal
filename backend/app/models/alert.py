from __future__ import annotations

from datetime import datetime
from sqlalchemy import Integer, Numeric, String, DateTime, ForeignKey, Index, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    host_id: Mapped[int] = mapped_column(Integer, ForeignKey("hosts.id"), nullable=False)
    alert_key: Mapped[str] = mapped_column(String(512), nullable=False)
    metric_name: Mapped[str] = mapped_column(String(64), nullable=False)
    mount_path: Mapped[str | None] = mapped_column(String(512))
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    message: Mapped[str | None] = mapped_column(String(1000))
    status: Mapped[str] = mapped_column(String(20), default="OPEN")
    triggered_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime)
    email_sent: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("idx_alerts_host_time", "host_id", created_at.desc()),
        Index("idx_alerts_key", "alert_key"),
        Index("idx_alerts_status", "status"),
    )
