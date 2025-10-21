"""Tests for plugin permission enforcement."""

import pytest

from axon.plugins.base import Plugin
from axon.plugins.loader import PluginLoader
from axon.plugins.manifest import Manifest
from axon.plugins.permissions import Permission


class TestPermissionEnforcement:
    """Test permission enforcement in plugins."""

    def test_plugin_requires_permission(self):
        """Plugin should enforce required permissions."""
        manifest = Manifest(
            name="test_plugin",
            version="1.0",
            description="Test",
            entrypoint="test:TestPlugin",
            permissions=[Permission.FS_READ],
        )

        # Create a simple plugin class
        from pydantic import BaseModel

        class DummyPlugin(Plugin):
            def load(self, config: BaseModel | None) -> None:
                pass

            def describe(self):
                return {}

            def execute(self, data):
                # This should work - permission granted
                self.require(Permission.FS_READ)
                return {"status": "ok"}

        plugin = DummyPlugin(manifest)
        result = plugin.execute({})
        assert result["status"] == "ok"

    def test_plugin_missing_permission_raises_error(self):
        """Plugin should raise error when permission not granted."""
        manifest = Manifest(
            name="test_plugin",
            version="1.0",
            description="Test",
            entrypoint="test:TestPlugin",
            permissions=[],  # No permissions granted
        )

        from pydantic import BaseModel

        class DummyPlugin(Plugin):
            def load(self, config: BaseModel | None) -> None:
                pass

            def describe(self):
                return {}

            def execute(self, data):
                # This should fail - permission not granted
                self.require(Permission.FS_WRITE)
                return {"status": "ok"}

        plugin = DummyPlugin(manifest)

        with pytest.raises(PermissionError) as exc_info:
            plugin.execute({})

        assert "not granted" in str(exc_info.value)

    def test_loader_strips_denied_permissions(self, tmp_path):
        """Loader should strip permissions from deny list."""
        # Create a test plugin file
        plugin_file = tmp_path / "test_perm.py"
        plugin_file.write_text(
            """
from pydantic import BaseModel
from axon.plugins.base import Plugin

class TestPermPlugin(Plugin):
    def load(self, config: BaseModel | None) -> None:
        pass
    def describe(self):
        return {}
    def execute(self, data):
        return {"ok": True}

PLUGIN_CLASS = TestPermPlugin
"""
        )

        # Create manifest
        manifest_file = tmp_path / "test_perm.yaml"
        manifest_file.write_text(
            """
name: test_perm
version: "1.0"
description: Test permission stripping
entrypoint: test_perm:TestPermPlugin
permissions:
  - fs.write
  - net.http
"""
        )

        # Create loader with deny list
        loader = PluginLoader(plugin_dir=tmp_path, deny={Permission.FS_WRITE})
        loader.discover()

        # Check that FS_WRITE was stripped
        manifest = loader.manifests["test_perm"]
        assert Permission.FS_WRITE not in manifest.permissions
        assert Permission.NET_HTTP in manifest.permissions

    def test_dry_run_mode(self):
        """Dry run mode should log but not fail on permission checks."""
        manifest = Manifest(
            name="test_plugin",
            version="1.0",
            description="Test",
            entrypoint="test:TestPlugin",
            permissions=[Permission.FS_READ],
        )

        from pydantic import BaseModel

        class DummyPlugin(Plugin):
            def load(self, config: BaseModel | None) -> None:
                pass

            def describe(self):
                return {}

            def execute(self, data):
                self.require(Permission.FS_READ)
                return {"status": "ok"}

        # Dry run should still work
        plugin = DummyPlugin(manifest, dry_run=True)
        result = plugin.execute({})
        assert result["status"] == "ok"

    def test_file_writer_plugin_permissions(self, tmp_path):
        """File writer plugin should enforce FS_WRITE permission."""
        # Test the actual file_writer plugin
        manifest = Manifest(
            name="file_writer",
            version="1.0",
            description="File writer",
            entrypoint="file_writer:FileWriterPlugin",
            permissions=[Permission.FS_WRITE],
        )

        # Import the actual plugin
        import sys
        from pathlib import Path

        plugin_path = Path(__file__).parent.parent / "plugins"
        sys.path.insert(0, str(plugin_path))

        try:
            from file_writer import FileWriterPlugin

            plugin = FileWriterPlugin(manifest)
            plugin.load(None)

            # Create test input
            from file_writer import FileWriteInput

            test_file = tmp_path / "test_output.txt"
            input_data = FileWriteInput(path=str(test_file), content="Hello, World!")

            # Execute should succeed with permission
            result = plugin.execute(input_data)
            assert result.success is True
            assert test_file.exists()
            assert test_file.read_text() == "Hello, World!"

        finally:
            if str(plugin_path) in sys.path:
                sys.path.remove(str(plugin_path))

    def test_file_writer_without_permission_fails(self, tmp_path):
        """File writer plugin should fail without FS_WRITE permission."""
        # Manifest without FS_WRITE permission
        manifest = Manifest(
            name="file_writer",
            version="1.0",
            description="File writer",
            entrypoint="file_writer:FileWriterPlugin",
            permissions=[],  # No permissions!
        )

        import sys
        from pathlib import Path

        plugin_path = Path(__file__).parent.parent / "plugins"
        sys.path.insert(0, str(plugin_path))

        try:
            from file_writer import FileWriterPlugin

            # Loading should fail due to missing permission
            with pytest.raises(PermissionError):
                plugin = FileWriterPlugin(manifest)
                plugin.load(None)

        finally:
            if str(plugin_path) in sys.path:
                sys.path.remove(str(plugin_path))

    def test_all_permission_types_exist(self):
        """All expected permission types should be defined."""
        assert hasattr(Permission, "FS_READ")
        assert hasattr(Permission, "FS_WRITE")
        assert hasattr(Permission, "NET_HTTP")
        assert hasattr(Permission, "PROCESS_SPAWN")

        # Verify they are enums with correct values
        assert Permission.FS_READ.value == "fs.read"
        assert Permission.FS_WRITE.value == "fs.write"
        assert Permission.NET_HTTP.value == "net.http"
        assert Permission.PROCESS_SPAWN.value == "process.spawn"
