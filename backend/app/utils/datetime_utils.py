from __future__ import annotations

from datetime import datetime, timedelta, timezone


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def is_stale(last_seen: datetime | None, threshold_minutes: int = 20) -> bool:
    if last_seen is None:
        return True
    return utc_now() - last_seen > timedelta(minutes=threshold_minutes)
