from typer.testing import CliRunner
import importlib
import main


def test_voice_shell_timeout(monkeypatch):
    calls = []

    def dummy_voice_shell(*, timeout=None, model_path=None, wakeword="axon"):
        calls.append(timeout)

    module = importlib.import_module("plugins.voice_shell")
    monkeypatch.setattr(module, "voice_shell", dummy_voice_shell)
    runner = CliRunner()
    result = runner.invoke(main.app, ["voice-shell", "--timeout", "5"])
    assert result.exit_code == 0
    assert calls == [5.0]
