from __future__ import annotations

from datetime import datetime
from sqlalchemy import String, Integer, Float, DateTime, Text, Index, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class BusinessTransaction(Base):
    __tablename__ = "recsignal_business_transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    host_id: Mapped[int | None] = mapped_column(Integer, index=True)
    app_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    endpoint: Mapped[str] = mapped_column(String(512), nullable=False)
    method: Mapped[str] = mapped_column(String(10), nullable=False)
    status_code: Mapped[int] = mapped_column(Integer, nullable=False)
    response_time_ms: Mapped[float] = mapped_column(Float, nullable=False)
    is_error: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text)
    trace_id: Mapped[str | None] = mapped_column(String(64), index=True)
    user_id: Mapped[str | None] = mapped_column(String(255))
    collected_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    __table_args__ = (
        Index("ix_bt_app_collected", "app_name", "collected_at"),
    )
