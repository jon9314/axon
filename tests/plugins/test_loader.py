from __future__ import annotations

import logging
from pathlib import Path

import pytest

from axon.plugins.loader import PluginLoader
from axon.plugins.permissions import Permission


def yaml(data: dict) -> str:
    import yaml as _yaml

    return _yaml.safe_dump(data)


def make_plugin(
    tmp_path: Path, name: str, *, perms: list[str] | None = None, sleep: float | None = None
) -> None:
    py = tmp_path / f"{name}.py"
    py.write_text(
        f"""
import time
from pathlib import Path
from pydantic import BaseModel
from axon.plugins.base import Plugin
from axon.plugins.permissions import Permission

class InModel(BaseModel):
    text: str = "hi"

class OutModel(BaseModel):
    text: str

class TestPlugin(Plugin[InModel, OutModel]):
    input_model = InModel
    output_model = OutModel

    def load(self, config: BaseModel | None) -> None:
        pass

    def describe(self) -> dict[str, str]:
        return {{"name": self.manifest.name}}

    def execute(self, data: InModel) -> OutModel:
        if {sleep is not None}:
            time.sleep({sleep or 0})
        if {'fs.write' in (perms or [])}:
            self.require(Permission.FS_WRITE)
            if not self.dry_run:
                Path("{name}.out").write_text(data.text)
        return OutModel(text=data.text)

    def shutdown(self) -> None:
        self.closed = True

PLUGIN_CLASS = TestPlugin
"""
    )
    manifest = {
        "name": name,
        "version": "1.0",
        "description": name,
        "entrypoint": f"{name}:TestPlugin",
        "permissions": perms or [],
    }
    (tmp_path / f"{name}.yaml").write_text(yaml(manifest))


def test_manifest_required(tmp_path: Path):
    (tmp_path / "foo.py").write_text("# empty")
    loader = PluginLoader(plugin_dir=tmp_path)
    with pytest.raises(FileNotFoundError):
        loader.discover()


def test_invalid_manifest(tmp_path: Path):
    make_plugin(tmp_path, "p")
    (tmp_path / "p.yaml").write_text("name: p")
    loader = PluginLoader(plugin_dir=tmp_path)
    with pytest.raises(ValueError):
        loader.discover()


def test_permission_denied(tmp_path: Path, caplog: pytest.LogCaptureFixture):
    make_plugin(tmp_path, "p", perms=["fs.write"])
    loader = PluginLoader(plugin_dir=tmp_path, deny={Permission.FS_WRITE})
    loader.discover()
    caplog.set_level(logging.INFO)
    with pytest.raises(PermissionError):
        loader.execute("p", {"text": "x"})
    assert any(r.levelno <= logging.ERROR for r in caplog.records)


def test_timeout_enforced(tmp_path: Path):
    make_plugin(tmp_path, "p", sleep=0.5)
    loader = PluginLoader(plugin_dir=tmp_path)
    loader.discover()
    with pytest.raises(TimeoutError):
        loader.execute("p", {}, timeout=0.1)


def test_dry_run(tmp_path: Path):
    make_plugin(tmp_path, "p", perms=["fs.write"])
    loader = PluginLoader(plugin_dir=tmp_path, dry_run=True)
    loader.discover()
    loader.execute("p", {"text": "x"})
    assert not (tmp_path / "p.out").exists()


def test_audit_log(tmp_path: Path, caplog: pytest.LogCaptureFixture):
    make_plugin(tmp_path, "p")
    loader = PluginLoader(plugin_dir=tmp_path)
    loader.discover()
    caplog.set_level(logging.INFO)
    loader.execute("p", {"text": "hi"})
    assert any("plugin-execute" in r.message or r.msg == "plugin-execute" for r in caplog.records)


def test_shutdown_called(tmp_path: Path):
    make_plugin(tmp_path, "p")
    loader = PluginLoader(plugin_dir=tmp_path)
    loader.discover()
    loader.shutdown_all()
    assert getattr(loader.plugins["p"], "closed", False)
