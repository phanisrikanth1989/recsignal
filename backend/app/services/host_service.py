from __future__ import annotations

import logging
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.host import Host
from app.utils.datetime_utils import utc_now

logger = logging.getLogger(__name__)


def get_or_create_host(
    db: Session,
    hostname: str,
    ip_address: str | None = None,
    environment: str | None = None,
) -> Host:
    """Find existing host by hostname or register a new one."""
    host = db.query(Host).filter(Host.hostname == hostname).first()
    if host:
        host.ip_address = ip_address or host.ip_address
        host.environment = environment or host.environment
        host.last_seen_at = utc_now()
        host.updated_at = utc_now()
        db.flush()
        return host

    host = Host(
        hostname=hostname,
        ip_address=ip_address,
        environment=environment,
        last_seen_at=utc_now(),
        is_active=1,
    )
    db.add(host)
    db.flush()
    logger.info("Registered new host: %s (id=%s)", hostname, host.id)
    return host


def get_all_hosts(db: Session) -> list[Host]:
    return db.query(Host).filter(Host.is_active == 1).order_by(Host.hostname).all()


def get_host_by_id(db: Session, host_id: int) -> Host | None:
    return db.query(Host).filter(Host.id == host_id).first()
