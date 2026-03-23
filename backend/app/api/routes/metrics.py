from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.metric import MetricSnapshot, MetricHistoryItem
from app.services.host_service import get_host_by_id
from app.services.metrics_service import get_latest_metrics, get_history

router = APIRouter()


@router.get("/api/hosts/{host_id}/metrics/latest", response_model=MetricSnapshot)
def host_latest_metrics(host_id: int, db: Session = Depends(get_db)):
    host = get_host_by_id(db, host_id)
    if not host:
        raise HTTPException(status_code=404, detail="Host not found")
    latest = get_latest_metrics(db, host_id)
    if not latest:
        return MetricSnapshot()
    return MetricSnapshot(
        cpu_percent=float(latest.cpu_percent) if latest.cpu_percent is not None else None,
        memory_percent=float(latest.memory_percent) if latest.memory_percent is not None else None,
        disk_percent_total=float(latest.disk_percent_total) if latest.disk_percent_total is not None else None,
        load_avg_1m=float(latest.load_avg_1m) if latest.load_avg_1m is not None else None,
        collected_at=latest.collected_at,
    )


@router.get("/api/hosts/{host_id}/metrics/history", response_model=list[MetricHistoryItem])
def host_metrics_history(host_id: int, limit: int = 96, db: Session = Depends(get_db)):
    host = get_host_by_id(db, host_id)
    if not host:
        raise HTTPException(status_code=404, detail="Host not found")
    rows = get_history(db, host_id, limit=limit)
    return [
        MetricHistoryItem(
            id=r.id,
            cpu_percent=float(r.cpu_percent) if r.cpu_percent is not None else None,
            memory_percent=float(r.memory_percent) if r.memory_percent is not None else None,
            disk_percent_total=float(r.disk_percent_total) if r.disk_percent_total is not None else None,
            load_avg_1m=float(r.load_avg_1m) if r.load_avg_1m is not None else None,
            collected_at=r.collected_at,
        )
        for r in rows
    ]
