import socket
from dataclasses import dataclass
from urllib.parse import urlparse


@dataclass
class ServiceStatus:
    """Track availability of optional services."""

    postgres: bool = True
    qdrant: bool = True
    redis: bool = True


service_status = ServiceStatus()


def check_service(url: str, timeout: float = 2) -> bool:
    """Return True if ``url`` is reachable within ``timeout`` seconds."""
    parsed = urlparse(url if "://" in url else f"//{url}")
    host = parsed.hostname or parsed.path or url
    port = parsed.port

    if port is None and ":" in host:
        try:
            host, port_part = host.rsplit(":", 1)
            port = int(port_part)
        except ValueError:
            pass

    if port is None:
        if parsed.scheme.startswith("postgres"):
            port = 5432
        elif parsed.scheme.startswith("qdrant"):
            port = 6333
        elif parsed.scheme == "redis":
            port = 6379
        else:
            port = 0

    if (port == 0 or port is None) and parsed.scheme == "redis":
        port = 6379

    if port == 0 or port is None:
        raise ValueError("Port required for service check")

    try:
        with socket.create_connection((host, port), timeout=timeout):
            success = True
    except OSError:
        success = False

    if port == 5432 or parsed.scheme.startswith("postgres"):
        service_status.postgres = success
    elif port == 6333 or parsed.scheme.startswith("qdrant"):
        service_status.qdrant = success
    elif port == 6379 or parsed.scheme == "redis":
        service_status.redis = success

    return success
