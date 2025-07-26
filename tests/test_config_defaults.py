from pathlib import Path

from axon.config.settings import Settings


def test_settings_no_example(monkeypatch):
    monkeypatch.setattr(Path, "exists", lambda self: False)
    Settings()
