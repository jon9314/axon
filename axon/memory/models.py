from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class BaseRecord(BaseModel):
    """Base attributes for memory records."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    tags: list[str] = Field(default_factory=list)
    scope: Optional[str] = None
    locked: bool = False
    metadata: Optional[dict[str, Any]] = None


class MemoryRecord(BaseRecord):
    content: str


class ReminderRecord(BaseRecord):
    content: str
    due_at: datetime


class ProfileRecord(BaseRecord):
    fields: dict[str, Any]
