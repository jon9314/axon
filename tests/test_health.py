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


def test_default_ports(monkeypatch):
    created = []

    class Dummy:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            pass

    def fake_conn(addr, timeout=2):
        created.append(addr)
        return Dummy()

    monkeypatch.setattr(health.socket, "create_connection", fake_conn)
    assert health.check_service("mqtt://broker")
    assert created[0] == ("broker", 1883)
