from __future__ import annotations

import importlib.util
import logging
from collections.abc import Iterable, Mapping
from pathlib import Path
from time import monotonic
from typing import Any

import yaml
from pydantic import BaseModel, ValidationError, create_model

from .base import Plugin
from .permissions import Permission

logger = logging.getLogger(__name__)


class ManifestModel(BaseModel):
    name: str
    version: str
    description: str
    permissions: list[Permission] = []
    config_schema: dict[str, str] | None = None


class AuditLog:
    """Simple structured audit logger."""

    def __init__(self, plugin: str, action: str):
        self.plugin = plugin
        self.action = action
        self.start = 0.0

    def __enter__(self) -> None:
        self.start = monotonic()

    def __exit__(self, exc_type, exc, tb) -> None:
        duration = monotonic() - self.start
        logger.info(
            "plugin-action",
            extra={
                "plugin": self.plugin,
                "action": self.action,
                "success": exc is None,
                "duration": duration,
            },
        )


class PluginLoader:
    """Load and manage plugins."""

    def __init__(
        self,
        plugin_dir: str | Path = "plugins",
        deny: Iterable[Permission] | None = None,
        dry_run: bool = False,
    ) -> None:
        self.plugin_dir = Path(plugin_dir)
        self.deny = set(deny or [])
        self.dry_run = dry_run
        self.plugins: dict[str, Plugin] = {}
        self.manifests: dict[str, ManifestModel] = {}

    def _load_manifest(self, path: Path) -> ManifestModel:
        if not path.exists():
            raise FileNotFoundError(f"Missing manifest for plugin {path.stem}")
        data = yaml.safe_load(path.read_text()) or {}
        try:
            manifest = ManifestModel.model_validate(data)
        except ValidationError as exc:  # pragma: no cover - validation
            raise ValueError(f"Invalid manifest {path}: {exc}") from exc
        return manifest

    def discover(self, configs: Mapping[str, Mapping[str, Any]] | None = None) -> None:
        configs = configs or {}
        for py_file in self.plugin_dir.glob("*.py"):
            if py_file.name.startswith("__"):
                continue
            name = py_file.stem
            manifest = self._load_manifest(py_file.with_suffix(".yaml"))
            self.manifests[manifest.name] = manifest
            if self.dry_run:
                continue
            if self.deny:
                removed = [p for p in manifest.permissions if p in self.deny]
                if removed:
                    manifest.permissions = [p for p in manifest.permissions if p not in self.deny]
                    logger.info(
                        "permission-stripped",
                        extra={"plugin": name, "removed": removed},
                    )
            spec = importlib.util.spec_from_file_location(f"plugins.{name}", py_file)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
            else:  # pragma: no cover - missing loader
                raise ImportError(f"Cannot load plugin {name}")
            plugin_cls = getattr(module, "PLUGIN_CLASS", None)
            if not plugin_cls or not issubclass(plugin_cls, Plugin):
                raise TypeError(f"Plugin {name} missing PLUGIN_CLASS")
            plugin = plugin_cls(manifest.model_dump())
            schema = manifest.config_schema
            cfg_model: type[BaseModel] | None = None
            if schema:
                type_map = {"int": int, "str": str, "bool": bool, "float": float}
                fields = {k: (type_map[v], ...) for k, v in schema.items()}
                cfg_model = create_model(f"Cfg_{name}", **fields)  # type: ignore[call-overload]
            cfg_data = configs.get(name)
            if cfg_model and cfg_data is not None:
                cfg = cfg_model(**cfg_data)
            else:
                cfg = None
            plugin.load(cfg)
            self.plugins[manifest.name] = plugin
            logger.info("plugin-loaded", extra={"plugin": manifest.name})

    def execute(self, name: str, data: Any) -> Any:
        plugin = self.plugins[name]
        with AuditLog(name, "execute"):
            return plugin.execute(data)

    def shutdown_all(self) -> None:
        for name, plugin in self.plugins.items():
            with AuditLog(name, "shutdown"):
                plugin.shutdown()
