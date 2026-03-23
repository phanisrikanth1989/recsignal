from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel
from typing import Generic, TypeVar

T = TypeVar("T")


class ResponseWrapper(BaseModel, Generic[T]):
    success: bool = True
    data: T | None = None
    message: str = "ok"


class TimestampMixin(BaseModel):
    created_at: datetime | None = None
    updated_at: datetime | None = None
