from __future__ import annotations

from datetime import datetime
from sqlalchemy import String, Integer, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class DbInstance(Base):
    __tablename__ = "recsignal_db_instances"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    instance_name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    db_type: Mapped[str] = mapped_column(String(32), nullable=False, default="oracle")  # oracle, postgresql, mysql
    host: Mapped[str | None] = mapped_column(String(255))
    port: Mapped[int | None] = mapped_column(Integer)
    service_name: Mapped[str | None] = mapped_column(String(255))  # Oracle SID / service name
    environment: Mapped[str | None] = mapped_column(String(64))
    support_group: Mapped[str | None] = mapped_column(String(128))
    status: Mapped[str] = mapped_column(String(20), default="unknown")  # up, down, degraded, unknown
    is_active: Mapped[int] = mapped_column(Integer, default=1)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
