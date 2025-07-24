from __future__ import annotations

import logging
from enum import Enum

logger = logging.getLogger(__name__)


class Permission(str, Enum):
    """Enumerates built-in plugin permissions."""

    FS_READ = "fs.read"
    FS_WRITE = "fs.write"
    NET_HTTP = "net.http"
    PROCESS_SPAWN = "process.spawn"


def guard(permission: Permission, granted: set[Permission], *, dry_run: bool = False) -> None:
    """Assert permission is granted and handle dry-run."""
    if permission not in granted:
        logger.error("permission denied", extra={"permission": permission})
        raise PermissionError(f"Permission '{permission}' not granted")
    if dry_run:
        logger.info("dry-run: %s", permission)
