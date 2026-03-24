from __future__ import annotations

from datetime import datetime
from sqlalchemy import Integer, Numeric, String, DateTime, ForeignKey, func, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class DbSlowQuery(Base):
    __tablename__ = "recsignal_db_slow_queries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    db_instance_id: Mapped[int] = mapped_column(Integer, ForeignKey("recsignal_db_instances.id"), nullable=False)
    sql_id: Mapped[str | None] = mapped_column(String(64))
    sql_text: Mapped[str | None] = mapped_column(Text)
    username: Mapped[str | None] = mapped_column(String(128))
    elapsed_seconds: Mapped[float | None] = mapped_column(Numeric(14, 2))
    cpu_seconds: Mapped[float | None] = mapped_column(Numeric(14, 2))
    buffer_gets: Mapped[int | None] = mapped_column(Integer)
    disk_reads: Mapped[int | None] = mapped_column(Integer)
    rows_processed: Mapped[int | None] = mapped_column(Integer)
    executions: Mapped[int | None] = mapped_column(Integer)
    plan_hash_value: Mapped[str | None] = mapped_column(String(64))
    collected_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
