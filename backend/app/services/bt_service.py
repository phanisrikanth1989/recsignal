from __future__ import annotations

import logging
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.models.business_transaction import BusinessTransaction
from app.models.host import Host

logger = logging.getLogger(__name__)


def insert_transactions(
    db: Session, host_id: int | None, transactions: list[dict],
) -> int:
    """Insert a batch of business transaction records."""
    objs = []
    for t in transactions:
        objs.append(BusinessTransaction(
            host_id=host_id,
            app_name=t["app_name"],
            endpoint=t["endpoint"],
            method=t["method"],
            status_code=t["status_code"],
            response_time_ms=t["response_time_ms"],
            is_error=t.get("is_error", 0),
            error_message=t.get("error_message"),
            trace_id=t.get("trace_id"),
            user_id=t.get("user_id"),
            collected_at=t["collected_at"],
        ))
    db.add_all(objs)
    db.flush()
    return len(objs)


def get_transactions(
    db: Session,
    app_name: str | None = None,
    limit: int = 200,
    offset: int = 0,
) -> list[BusinessTransaction]:
    q = db.query(BusinessTransaction)
    if app_name:
        q = q.filter(BusinessTransaction.app_name == app_name)
    return q.order_by(desc(BusinessTransaction.collected_at)).offset(offset).limit(limit).all()


def get_bt_summary(db: Session) -> list[dict]:
    """Aggregate business transaction stats per app."""
    rows = (
        db.query(
            BusinessTransaction.app_name,
            func.count().label("total_requests"),
            func.avg(BusinessTransaction.response_time_ms).label("avg_response_time_ms"),
            func.sum(BusinessTransaction.is_error).label("error_count"),
        )
        .group_by(BusinessTransaction.app_name)
        .all()
    )
    results = []
    for r in rows:
        total = r.total_requests or 1
        error_count = int(r.error_count or 0)
        results.append({
            "app_name": r.app_name,
            "total_requests": total,
            "avg_response_time_ms": round(float(r.avg_response_time_ms or 0), 2),
            "error_count": error_count,
            "error_rate": round(error_count / total * 100, 2),
            "p95_response_time_ms": None,  # computed separately if needed
        })
    return results


def get_app_names(db: Session) -> list[str]:
    rows = db.query(BusinessTransaction.app_name).distinct().all()
    return [r[0] for r in rows]
