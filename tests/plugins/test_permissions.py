from __future__ import annotations

import logging
from pathlib import Path

import pytest

from axon.plugins.loader import PluginLoader
from axon.plugins.permissions import Permission


def make_writer(tmp_path: Path) -> None:
    py = tmp_path / "writer.py"
    py.write_text(
        """
from pathlib import Path
from pydantic import BaseModel
from axon.plugins.base import Plugin
from axon.plugins.permissions import Permission

class In(BaseModel):
    text: str = "hi"

class Out(BaseModel):
    text: str

class WritePlugin(Plugin[In, Out]):
    input_model = In
    output_model = Out

    def load(self, config: BaseModel | None) -> None:
        pass

    def describe(self):
        return {"name": self.manifest.name}

    def execute(self, data: In) -> Out:
        self.require(Permission.FS_WRITE)
        Path("w.out").write_text(data.text)
        return Out(text="wrote")

PLUGIN_CLASS = WritePlugin
"""
    )
    (tmp_path / "writer.yaml").write_text(
        """
name: writer
version: "1.0"
description: writer
entrypoint: writer:WritePlugin
permissions:
  - fs.write
"""
    )


def test_permission_enforced(tmp_path: Path, caplog: pytest.LogCaptureFixture):
    make_writer(tmp_path)
    loader = PluginLoader(plugin_dir=tmp_path, deny={Permission.FS_WRITE})
    loader.discover()
    caplog.set_level(logging.INFO)
    with pytest.raises(PermissionError):
        loader.execute("writer", {"text": "x"})
    assert any(r.levelno <= logging.ERROR for r in caplog.records)
