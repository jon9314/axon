import socket
from urllib.parse import urlparse


class ServiceStatus:
    """Track availability of optional services."""

    postgres: bool = True
    qdrant: bool = True
    redis: bool = True


service_status = ServiceStatus()


def check_service(url: str, timeout: float = 2) -> bool:
    """Return True if ``url`` is reachable within ``timeout`` seconds."""
    parsed = urlparse(url)
    host = parsed.hostname or url
    port = parsed.port
    if port is None:
        if parsed.scheme.startswith("postgres"):
            port = 5432
        elif parsed.scheme == "redis":
            port = 6379
        elif parsed.scheme == "http":
            port = 80
        elif parsed.scheme == "https":
            port = 443
        else:
            port = 0
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False
