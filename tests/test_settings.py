from pathlib import Path

import pytest
import yaml

from axon.config.settings import ConfigError, Settings


def write_yaml(path: Path, data: dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f)


def test_missing_required_field(tmp_path):
    example = tmp_path / "example.yaml"
    write_yaml(example, {"database": {}})
    with pytest.raises(ConfigError):
        Settings.load(example_file=example, local_file=None)


def test_env_override(tmp_path, monkeypatch):
    example = tmp_path / "example.yaml"
    write_yaml(example, {"database": {"postgres_uri": "file"}})
    local = tmp_path / "settings.yaml"
    write_yaml(local, {"database": {"postgres_uri": "local"}})
    monkeypatch.setenv("AXON__DATABASE__POSTGRES_URI", "env")
    settings = Settings.load(example_file=example, local_file=local)
    assert settings.database.postgres_uri == "env"


def test_redacted_summary(tmp_path, capsys):
    example = tmp_path / "example.yaml"
    write_yaml(example, {"database": {"postgres_uri": "x"}, "app": {"api_token": "secret"}})
    Settings.load(example_file=example, local_file=None)
    out = capsys.readouterr().out
    assert "secret" not in out
    assert "***" in out


def test_dump_example(tmp_path):
    out = tmp_path / "out.yaml"
    Settings.dump_example(out)
    data = yaml.safe_load(out.read_text())
    assert isinstance(data, dict)
    assert "database" in data
