from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict

from .manifest import Manifest
from .permissions import Permission, guard

InputT = TypeVar("InputT", bound=BaseModel)
OutputT = TypeVar("OutputT", bound=BaseModel)


class _AnyModel(BaseModel):
    model_config = ConfigDict(extra="allow")


class Plugin(ABC, Generic[InputT, OutputT]):
    """Base class for Axon plugins."""

    input_model: type[BaseModel] = _AnyModel
    output_model: type[BaseModel] = _AnyModel

    def __init__(self, manifest: Manifest, *, dry_run: bool = False) -> None:
        self.manifest = manifest
        self.permissions: set[Permission] = set(manifest.permissions)
        self.dry_run = dry_run

    def require(self, perm: Permission) -> None:
        """Check permission via the guard."""
        guard(perm, self.permissions, dry_run=self.dry_run)

    @abstractmethod
    def load(self, config: BaseModel | None) -> None:
        """Initialize plugin with optional validated configuration."""

    @abstractmethod
    def describe(self) -> Mapping[str, str]:
        """Return plugin description and capabilities."""

    @abstractmethod
    def execute(self, data: InputT) -> OutputT:
        """Execute the plugin action."""

    def shutdown(self) -> None:  # pragma: no cover - default no-op
        """Clean up resources when unloading."""
        return
