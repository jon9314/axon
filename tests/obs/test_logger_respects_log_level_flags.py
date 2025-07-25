import logging

from typer.testing import CliRunner

import main


def test_logger_respects_log_level_flags(monkeypatch, caplog):
    def dummy_load():
        logging.info("loaded")

    monkeypatch.setattr(main.plugin_loader, "discover", dummy_load)
    runner = CliRunner()
    caplog.set_level(logging.INFO)
    runner.invoke(main.app, ["--log-level", "WARNING", "plugins", "reload"])
    assert not any(r.message == "loaded" for r in caplog.records)
