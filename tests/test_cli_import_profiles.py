from typer.testing import CliRunner

import main


def test_import_profiles(monkeypatch, tmp_path):
    sample = tmp_path / "prefs.yaml"
    sample.write_text("u:\n  persona: x\n")
    calls = []
    monkeypatch.setattr(main.profile_manager, "load_from_yaml", lambda path: calls.append(path))
    runner = CliRunner()
    result = runner.invoke(main.app, ["import-profiles", "--path", str(sample)])
    assert result.exit_code == 0
    assert calls == [str(sample)]
