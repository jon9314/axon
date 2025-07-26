import importlib
import logging

from axon.utils import health


def test_check_service_fail():
    assert not health.check_service("tcp://127.0.0.1:1", timeout=0.1)


def test_backend_startup_warning(monkeypatch, caplog):
    monkeypatch.setattr(health, "check_service", lambda *a, **k: False)
    caplog.set_level(logging.WARNING)
    import backend.main as bm

    importlib.reload(bm)
    assert any("unreachable" in r.message for r in caplog.records)
