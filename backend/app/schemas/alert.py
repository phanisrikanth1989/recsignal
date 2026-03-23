from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel


class AlertListItem(BaseModel):
    id: int
    host_id: int
    hostname: str | None = None
    metric_name: str
    mount_path: str | None = None
    severity: str
    message: str | None = None
    status: str
    triggered_at: datetime | None = None
    resolved_at: datetime | None = None

    model_config = {"from_attributes": True}
