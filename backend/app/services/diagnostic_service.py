from __future__ import annotations

import logging
from sqlalchemy.orm import Session

from app.models.diagnostic import DiagnosticSnapshot
from app.models.host import Host
from sqlalchemy import desc

logger = logging.getLogger(__name__)


def insert_diagnostic(db: Session, host_id: int | None, data: dict) -> DiagnosticSnapshot:
    snapshot = DiagnosticSnapshot(
        host_id=host_id,
        app_name=data["app_name"],
        snapshot_type=data["snapshot_type"],
        duration_seconds=data.get("duration_seconds"),
        top_functions=data.get("top_functions"),
        memory_summary=data.get("memory_summary"),
        thread_dump=data.get("thread_dump"),
        triggered_by=data.get("triggered_by"),
        collected_at=data["collected_at"],
    )
    db.add(snapshot)
    db.flush()
    return snapshot


def get_diagnostics(
    db: Session,
    app_name: str | None = None,
    snapshot_type: str | None = None,
    limit: int = 50,
) -> list[DiagnosticSnapshot]:
    q = db.query(DiagnosticSnapshot)
    if app_name:
        q = q.filter(DiagnosticSnapshot.app_name == app_name)
    if snapshot_type:
        q = q.filter(DiagnosticSnapshot.snapshot_type == snapshot_type)
    return q.order_by(desc(DiagnosticSnapshot.collected_at)).limit(limit).all()


def get_diagnostic_by_id(db: Session, snapshot_id: int) -> DiagnosticSnapshot | None:
    return db.query(DiagnosticSnapshot).filter(DiagnosticSnapshot.id == snapshot_id).first()
