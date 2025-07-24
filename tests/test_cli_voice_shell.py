from typer.testing import CliRunner

import main


def test_voice_shell_timeout(monkeypatch):
    calls = []

    def dummy_execute(name: str, data: dict) -> None:
        calls.append(data["timeout"])

    monkeypatch.setattr(main.plugin_loader, "discover", lambda: None)
    monkeypatch.setattr(main.plugin_loader, "execute", dummy_execute)
    runner = CliRunner()
    result = runner.invoke(main.app, ["voice-shell", "--timeout", "5"])
    assert result.exit_code == 0
    assert calls == [5.0]
