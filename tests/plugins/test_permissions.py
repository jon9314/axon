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
from pydantic import BaseModel
from axon.plugins.base import Plugin
from axon.plugins.permissions import Permission

class WritePlugin(Plugin):
    def load(self, config: BaseModel | None) -> None:
        pass

    def describe(self):
        return {"name": self.manifest['name']}

    def execute(self, data):
        self.check_permission(Permission.FS_WRITE)
        return "wrote"

PLUGIN_CLASS = WritePlugin
"""
    )
    (tmp_path / "writer.yaml").write_text(
        """
name: writer
version: "1.0"
description: writer
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
        loader.execute("writer", {})
    assert any(getattr(r, "success", True) is False for r in caplog.records)
