from __future__ import annotations

import logging
from pathlib import Path

import pytest
from pydantic import ValidationError

from axon.plugins.loader import PluginLoader
from axon.plugins.permissions import Permission


def make_plugin(
    tmp_path: Path, name: str, perms: list[str] | None = None, schema: dict[str, str] | None = None
) -> None:
    py = tmp_path / f"{name}.py"
    py.write_text(
        """
from pydantic import BaseModel
from axon.plugins.base import Plugin
from axon.plugins.permissions import Permission

class TestPlugin(Plugin):
    def load(self, config: BaseModel | None) -> None:
        self.config = config

    def describe(self) -> dict[str, str]:
        return {"name": self.manifest['name']}

    def execute(self, data):
        if Permission.FS_WRITE in self.permissions:
            self.check_permission(Permission.FS_WRITE)
        return "ok"

PLUGIN_CLASS = TestPlugin
"""
    )
    manifest = {
        "name": name,
        "version": "1.0",
        "description": name,
        "permissions": perms or [],
    }
    if schema:
        manifest["config_schema"] = schema  # type: ignore[assignment]
    (tmp_path / f"{name}.yaml").write_text(yaml(manifest))


def yaml(data: dict) -> str:
    import yaml as _yaml

    return _yaml.safe_dump(data)


def test_manifest_required(tmp_path: Path):
    (tmp_path / "foo.py").write_text("# empty")
    loader = PluginLoader(plugin_dir=tmp_path)
    with pytest.raises(FileNotFoundError):
        loader.discover()


def test_permission_denied(tmp_path: Path, caplog: pytest.LogCaptureFixture):
    make_plugin(tmp_path, "p", ["fs.write"])
    caplog.set_level(logging.INFO)
    loader = PluginLoader(plugin_dir=tmp_path, deny={Permission.FS_WRITE})
    loader.discover()
    assert "permission-stripped" in caplog.text
    assert loader.execute("p", {}) == "ok"
    with pytest.raises(PermissionError):
        loader.plugins["p"].check_permission(Permission.FS_WRITE)


def test_plugin_execute_logged(tmp_path: Path, caplog: pytest.LogCaptureFixture):
    make_plugin(tmp_path, "p")
    loader = PluginLoader(plugin_dir=tmp_path)
    loader.discover()
    caplog.set_level(logging.INFO)
    loader.execute("p", {})
    assert any(r.action == "execute" for r in caplog.records)  # type: ignore[attr-defined]


def test_config_schema_validation(tmp_path: Path):
    make_plugin(tmp_path, "p", schema={"count": "int"})
    loader = PluginLoader(plugin_dir=tmp_path)
    with pytest.raises(ValidationError):
        loader.discover(configs={"p": {"count": "bad"}})
