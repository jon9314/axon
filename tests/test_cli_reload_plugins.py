from typer.testing import CliRunner
import main


def test_reload_plugins(monkeypatch):
    calls = []

    def dummy_load(hot_reload=False):
        calls.append(hot_reload)

    monkeypatch.setattr(main, "load_plugins", dummy_load)
    runner = CliRunner()
    result = runner.invoke(main.app, ["plugins", "reload"])
    assert result.exit_code == 0
    assert calls == [True]
