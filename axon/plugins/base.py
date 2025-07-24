from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel

from .permissions import Permission


class Plugin(ABC):
    """Base class for Axon plugins."""

    def __init__(self, manifest: dict[str, Any]):
        self.manifest = manifest
        perms = manifest.get("permissions", [])
        self.permissions: set[Permission] = {Permission(p) for p in perms}

    def check_permission(self, perm: Permission) -> None:
        if perm not in self.permissions:
            raise PermissionError(f"Permission '{perm}' not granted for {self.manifest['name']}")

    @abstractmethod
    def load(self, config: BaseModel | None) -> None:
        """Initialize plugin with optional validated configuration."""

    @abstractmethod
    def describe(self) -> dict[str, Any]:
        """Return plugin description and capabilities."""

    @abstractmethod
    def execute(self, data: Any) -> Any:
        """Execute the plugin action."""

    def shutdown(self) -> None:
        """Clean up resources when unloading."""
        return
