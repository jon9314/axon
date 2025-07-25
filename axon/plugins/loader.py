from __future__ import annotations

import importlib.util
import logging
import traceback
from collections.abc import Mapping
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from time import monotonic
from typing import Any

from pydantic import BaseModel, create_model

from axon.obs.records import ErrorRecord, PluginCallRecord
from axon.obs.tracer import current_run

from .base import Plugin
from .manifest import Manifest, load_manifest
from .permissions import Permission

logger = logging.getLogger(__name__)


class AuditLog:
    """Structured audit logger for plugin actions."""

    def __init__(self, plugin: str, action: str, redacted: bool = False) -> None:
        self.plugin = plugin
        self.action = action
        self.redacted = redacted
        self.start = 0.0

    def __enter__(self) -> None:
        self.start = monotonic()

    def __exit__(self, exc_type, exc, tb) -> None:
        duration = monotonic() - self.start
        logger.info(
            "plugin-%s",
            self.action,
            extra={
                "plugin": self.plugin,
                "success": exc is None,
                "duration": duration,
            },
        )


class PluginLoader:
    """Discover, validate and safely execute plugins."""

    def __init__(
        self,
        plugin_dir: str | Path = "plugins",
        *,
        deny: set[Permission] | None = None,
        dry_run: bool = False,
    ) -> None:
        self.plugin_dir = Path(plugin_dir)
        self.deny = deny or set()
        self.dry_run = dry_run
        self.plugins: dict[str, Plugin] = {}
        self.manifests: dict[str, Manifest] = {}

    def discover(self, configs: Mapping[str, Mapping[str, Any]] | None = None) -> None:
        configs = configs or {}
        for py_file in self.plugin_dir.glob("*.py"):
            if py_file.name.startswith("__"):
                continue
            yaml_path = py_file.with_suffix(".yaml")
            toml_path = py_file.with_suffix(".toml")
            if yaml_path.exists():
                manifest_path = yaml_path
            elif toml_path.exists():
                manifest_path = toml_path
            else:
                raise FileNotFoundError(f"Missing manifest for plugin {py_file.stem}")
            manifest = load_manifest(manifest_path)
            self.manifests[manifest.name] = manifest
            if self.deny:
                removed = [p for p in manifest.permissions if p in self.deny]
                if removed:
                    manifest.permissions = [p for p in manifest.permissions if p not in self.deny]
                    logger.info(
                        "permission-stripped", extra={"plugin": manifest.name, "removed": removed}
                    )
            module_name, cls_name = manifest.entrypoint.split(":")
            module_file = self.plugin_dir / f"{module_name}.py"
            spec = importlib.util.spec_from_file_location(module_name, module_file)
            if not spec or not spec.loader:
                raise ImportError(f"Cannot load module {module_name}")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            plugin_cls = getattr(module, cls_name)
            if not issubclass(plugin_cls, Plugin):
                raise TypeError(f"{manifest.entrypoint} is not a Plugin")
            plugin = plugin_cls(manifest, dry_run=self.dry_run)
            schema = manifest.config_schema
            cfg_model: type[BaseModel] | None = None
            if schema:
                type_map = {"int": int, "str": str, "bool": bool, "float": float}
                fields = {k: (type_map[v], ...) for k, v in schema.items()}
                cfg_model = create_model(f"Cfg_{manifest.name}", **fields)  # type: ignore[call-overload]
            cfg_data = configs.get(manifest.name)
            cfg = cfg_model(**cfg_data) if cfg_model and cfg_data is not None else None
            plugin.load(cfg)
            self.plugins[manifest.name] = plugin
            logger.info("plugin-loaded", extra={"plugin": manifest.name})

    def execute(
        self, name: str, data: Mapping[str, Any], *, timeout: float | None = None, retries: int = 0
    ) -> Any:
        plugin = self.plugins[name]

        def call() -> Any:
            model = plugin.input_model(**data) if isinstance(data, Mapping) else data
            result = plugin.execute(model)
            return (
                plugin.output_model.model_validate(result)
                if isinstance(result, Mapping)
                else result
            )

        attempt = 0
        result: Any | None = None
        err: Exception | None = None
        rec = PluginCallRecord(plugin=name, started_at=datetime.utcnow())
        while True:
            try:
                with AuditLog(name, "execute"):
                    if timeout is None:
                        result = call()
                    else:
                        with ThreadPoolExecutor(max_workers=1) as ex:
                            future = ex.submit(call)
                            result = future.result(timeout=timeout)
                rec.success = True
                break
            except Exception as exc:
                attempt += 1
                err = exc
                if attempt > retries:
                    rec.success = False
                    rec.error = ErrorRecord(
                        type=type(exc).__name__, message=str(exc), traceback=traceback.format_exc()
                    )
                    break
        rec.ended_at = datetime.utcnow()
        rec.duration_ms = (rec.ended_at - rec.started_at).total_seconds() * 1000
        rec.truncated_input = str(data)[:200]
        if result is not None:
            rec.truncated_output = str(result)[:200]
        run = current_run()
        if run:
            run.plugin_calls.append(rec)
        if err and attempt > retries:
            raise err
        return result

    def shutdown_all(self) -> None:
        for name, plugin in self.plugins.items():
            with AuditLog(name, "shutdown"):
                plugin.shutdown()
