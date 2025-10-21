"""Plugin demonstrating permission enforcement for file system writes."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel

from axon.plugins.base import Plugin
from axon.plugins.permissions import Permission


class FileWriteInput(BaseModel):
    """Input for file write operation."""

    path: str
    content: str


class FileWriteOutput(BaseModel):
    """Output from file write operation."""

    success: bool
    message: str
    bytes_written: int


class FileWriterPlugin(Plugin[FileWriteInput, FileWriteOutput]):
    """Plugin for writing files with permission enforcement."""

    input_model = FileWriteInput
    output_model = FileWriteOutput

    def load(self, config: BaseModel | None) -> None:
        """Initialize plugin."""
        # Verify we have write permission
        if Permission.FS_WRITE not in self.permissions:
            raise PermissionError("FileWriterPlugin requires FS_WRITE permission")

    def describe(self) -> dict[str, str]:
        """Return plugin description."""
        return {
            "name": self.manifest.name,
            "description": self.manifest.description,
            "permissions_required": "fs.write",
        }

    def execute(self, data: FileWriteInput) -> FileWriteOutput:
        """Write content to a file with permission check."""
        # Enforce permission at runtime
        self.require(Permission.FS_WRITE)

        try:
            file_path = Path(data.path)

            # Security check: ensure path is within allowed directory
            if file_path.is_absolute():
                # In production, you'd want to validate against allowed directories
                pass

            # Write the file
            bytes_written = file_path.write_text(data.content)

            return FileWriteOutput(
                success=True, message=f"Successfully wrote to {data.path}", bytes_written=bytes_written
            )
        except PermissionError as e:
            return FileWriteOutput(
                success=False, message=f"Permission denied: {e}", bytes_written=0
            )
        except Exception as e:
            return FileWriteOutput(success=False, message=f"Error: {e}", bytes_written=0)


PLUGIN_CLASS = FileWriterPlugin
