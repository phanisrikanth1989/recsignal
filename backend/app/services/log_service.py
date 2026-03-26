from __future__ import annotations

import logging
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, or_

from app.models.log_entry import LogEntry
from app.models.host import Host

logger = logging.getLogger(__name__)


def insert_logs(db: Session, host_id: int, hostname: str, logs: list[dict]) -> int:
    """Insert a batch of log entries."""
    objs = []
    for log in logs:
        objs.append(LogEntry(
            host_id=host_id,
            hostname=hostname,
            source=log["source"],
            level=log["level"].upper(),
            message=log["message"],
            trace_id=log.get("trace_id"),
            logged_at=log["logged_at"],
        ))
    db.add_all(objs)
    db.flush()
    return len(objs)


def search_logs(
    db: Session,
    query: str | None = None,
    host_id: int | None = None,
    level: str | None = None,
    source: str | None = None,
    limit: int = 200,
    offset: int = 0,
) -> dict:
    """Search logs with optional filters."""
    q = db.query(LogEntry)

    if host_id:
        q = q.filter(LogEntry.host_id == host_id)
    if level:
        q = q.filter(LogEntry.level == level.upper())
    if source:
        q = q.filter(LogEntry.source == source)
    if query:
        q = q.filter(LogEntry.message.ilike(f"%{query}%"))

    total = q.count()
    logs = q.order_by(desc(LogEntry.logged_at)).offset(offset).limit(limit).all()

    return {"total": total, "logs": logs}


def get_log_summary(db: Session) -> dict:
    total = db.query(func.count(LogEntry.id)).scalar() or 0
    error_count = db.query(func.count(LogEntry.id)).filter(LogEntry.level == "ERROR").scalar() or 0
    warn_count = db.query(func.count(LogEntry.id)).filter(LogEntry.level == "WARN").scalar() or 0
    info_count = db.query(func.count(LogEntry.id)).filter(LogEntry.level == "INFO").scalar() or 0
    return {
        "total_logs": total,
        "error_count": error_count,
        "warn_count": warn_count,
        "info_count": info_count,
    }


def get_log_sources(db: Session) -> list[str]:
    rows = db.query(LogEntry.source).distinct().all()
    return [r[0] for r in rows]
