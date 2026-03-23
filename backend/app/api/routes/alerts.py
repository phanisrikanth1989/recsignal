from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.host import Host
from app.schemas.alert import AlertListItem
from app.services.alert_service import get_all_alerts

router = APIRouter()


@router.get("/api/alerts", response_model=list[AlertListItem])
def list_alerts(
    status: str | None = Query(None, description="Filter by OPEN or RESOLVED"),
    limit: int = Query(200, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    alerts = get_all_alerts(db, status=status, limit=limit)
    result = []
    for a in alerts:
        host = db.query(Host).filter(Host.id == a.host_id).first()
        result.append(
            AlertListItem(
                id=a.id,
                host_id=a.host_id,
                hostname=host.hostname if host else None,
                metric_name=a.metric_name,
                mount_path=a.mount_path,
                severity=a.severity,
                message=a.message,
                status=a.status,
                triggered_at=a.triggered_at,
                resolved_at=a.resolved_at,
            )
        )
    return result
