from typer.testing import CliRunner

import main


def test_reload_plugins(monkeypatch):
    calls = []

    def dummy_load():
        calls.append(True)

    monkeypatch.setattr(main.plugin_loader, "discover", lambda: dummy_load())
    runner = CliRunner()
    result = runner.invoke(main.app, ["plugins", "reload"])
    assert result.exit_code == 0
    assert calls == [True]
