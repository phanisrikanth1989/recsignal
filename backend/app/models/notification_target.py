from __future__ import annotations

from datetime import datetime
from sqlalchemy import Integer, String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class NotificationTarget(Base):
    __tablename__ = "recsignal_notification_targets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    support_group: Mapped[str] = mapped_column(String(128), nullable=False)
    email_to: Mapped[str] = mapped_column(String(512), nullable=False)
    is_active: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
