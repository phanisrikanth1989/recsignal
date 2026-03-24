from __future__ import annotations

from datetime import datetime
from sqlalchemy import Integer, Numeric, String, DateTime, ForeignKey, func, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class DbSessionSnapshot(Base):
    __tablename__ = "recsignal_db_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    db_instance_id: Mapped[int] = mapped_column(Integer, ForeignKey("recsignal_db_instances.id"), nullable=False)
    sid: Mapped[int | None] = mapped_column(Integer)
    serial_no: Mapped[int | None] = mapped_column(Integer)
    username: Mapped[str | None] = mapped_column(String(128))
    program: Mapped[str | None] = mapped_column(String(255))
    machine: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str | None] = mapped_column(String(20))  # ACTIVE, INACTIVE
    sql_id: Mapped[str | None] = mapped_column(String(64))
    sql_text: Mapped[str | None] = mapped_column(Text)
    wait_class: Mapped[str | None] = mapped_column(String(64))
    wait_event: Mapped[str | None] = mapped_column(String(128))
    seconds_in_wait: Mapped[float | None] = mapped_column(Numeric(12, 2))
    blocking_session: Mapped[int | None] = mapped_column(Integer)
    logon_time: Mapped[datetime | None] = mapped_column(DateTime)
    elapsed_seconds: Mapped[float | None] = mapped_column(Numeric(12, 2))
    collected_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
