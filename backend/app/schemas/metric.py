from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel


class MetricSnapshot(BaseModel):
    cpu_percent: float | None = None
    memory_percent: float | None = None
    disk_percent_total: float | None = None
    load_avg_1m: float | None = None
    collected_at: datetime | None = None

    model_config = {"from_attributes": True}


class MetricHistoryItem(BaseModel):
    id: int
    cpu_percent: float | None = None
    memory_percent: float | None = None
    disk_percent_total: float | None = None
    load_avg_1m: float | None = None
    collected_at: datetime | None = None

    model_config = {"from_attributes": True}
