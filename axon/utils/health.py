import socket
from dataclasses import dataclass
from urllib.parse import urlparse

# NOTE: default ports used when URL omits one
_DEFAULT_PORTS = {
    "postgres": 5432,
    "postgresql": 5432,
    "qdrant": 6333,
    "redis": 6379,
    "mqtt": 1883,
}


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

    scheme = parsed.scheme.lower()
    if port is None:
        port = _DEFAULT_PORTS.get(scheme)

    if port in (0, None):
        raise ValueError("Port required for service check")

    assert port is not None  # NOTE: validated above

    try:
        with socket.create_connection((host, port), timeout=timeout):
            success = True
    except OSError:
        success = False

    if scheme.startswith("postgres") or port == _DEFAULT_PORTS["postgres"]:
        service_status.postgres = success
    elif scheme.startswith("qdrant") or port == _DEFAULT_PORTS["qdrant"]:
        service_status.qdrant = success
    elif scheme == "redis" or port == _DEFAULT_PORTS["redis"]:
        service_status.redis = success

    return success
