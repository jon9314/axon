from __future__ import annotations

from abc import ABC, abstractmethod

from .models import BaseRecord


class MemoryStore(ABC):
    """Abstract persistence interface for memory records."""

    @abstractmethod
    def put(self, record: BaseRecord) -> str:
        """Store a record."""

    @abstractmethod
    def get(self, record_id: str) -> BaseRecord | None:
        """Retrieve a record."""

    @abstractmethod
    def update(self, record_id: str, **fields) -> BaseRecord:
        """Update a record."""

    @abstractmethod
    def delete(self, record_id: str) -> bool:
        """Delete a record."""

    @abstractmethod
    def search(
        self,
        query: str,
        tags: list[str] | None = None,
        scope: str | None = None,
        limit: int = 50,
    ) -> list[BaseRecord]:
        """Search for records."""

    @abstractmethod
    def lock(self, record_id: str) -> None:
        """Lock a record from modification."""
