from __future__ import annotations

from enum import Enum


class Permission(str, Enum):
    """Enumerates built-in plugin permissions."""

    FS_READ = "fs.read"
    FS_WRITE = "fs.write"
    NET_HTTP = "net.http"
    PROCESS_SPAWN = "process.spawn"
