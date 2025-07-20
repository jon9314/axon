from typer.testing import CliRunner
import main


def test_remember_command(monkeypatch):
    calls = []

    class DummyCM:
        def __init__(self, thread_id="cli_thread", identity="cli_user", goal_tracker=None):
            pass
        def add_fact(self, key, value):
            calls.append((key, value))

    monkeypatch.setattr(main, "ContextManager", DummyCM)
    runner = CliRunner()
    result = runner.invoke(main.app, ["remember", "foo", "bar"])
    assert result.exit_code == 0
    assert calls == [("foo", "bar")]

