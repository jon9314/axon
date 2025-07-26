import sys
from pathlib import Path

# ruff: noqa: E402

root_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(root_dir / "axon"))  # NOTE: ensure package import  # noqa: E402

import pytest
from utils import health as health_mod

service_status = health_mod.service_status


def pytest_collection_modifyitems(config, items):
    skip_db = pytest.mark.skip(reason="DB service unavailable")
    for item in items:
        markers = {m.name for m in item.iter_markers()}
        if "needs_postgres" in markers and not service_status.postgres:
            item.add_marker(skip_db)
        if "needs_qdrant" in markers and not service_status.qdrant:
            item.add_marker(skip_db)
