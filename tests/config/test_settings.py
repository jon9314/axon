from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from axon.config.settings import (
    get_settings,
    reload_settings,
    schema_json,
    validate_or_die,
)


def write_yaml(path: Path, data: dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f)


def test_env_override(monkeypatch, tmp_path):
    example = tmp_path / "example.yaml"
    local = tmp_path / "local.yaml"
    write_yaml(example, {"database": {"postgres_uri": "example"}})
    write_yaml(local, {"database": {"postgres_uri": "local"}})
    monkeypatch.setenv("AXON_DATABASE__POSTGRES_URI", "env")
    reload_settings(example_file=example, local_file=local)
    assert get_settings().database.postgres_uri == "env"


def test_missing_required_field(tmp_path):
    example = tmp_path / "example.yaml"
    write_yaml(example, {})
    reload_settings(example_file=example, local_file=None)
    with pytest.raises(SystemExit):
        validate_or_die()


def test_invalid_enum_value(tmp_path):
    example = tmp_path / "example.yaml"
    write_yaml(
        example,
        {"database": {"postgres_uri": "x"}, "app": {"log_level": "bogus"}},
    )
    reload_settings(example_file=example, local_file=None)
    with pytest.raises(SystemExit):
        validate_or_die()


def test_secret_redacted(tmp_path):
    example = tmp_path / "example.yaml"
    write_yaml(
        example,
        {
            "database": {"postgres_uri": "x"},
            "app": {"api_token": "secret"},
        },
    )
    reload_settings(example_file=example, local_file=None)
    dumped = get_settings().pretty_dump(mask_secrets=True)
    assert "secret" not in dumped
    assert "***" in dumped


def test_reload_settings(monkeypatch, tmp_path):
    example1 = tmp_path / "ex1.yaml"
    example2 = tmp_path / "ex2.yaml"
    write_yaml(example1, {"database": {"postgres_uri": "a"}})
    write_yaml(example2, {"database": {"postgres_uri": "b"}})
    reload_settings(example_file=example1, local_file=None)
    orig = get_settings()
    assert orig.database.postgres_uri == "a"
    reload_settings(example_file=example2, local_file=None)
    new = get_settings()
    assert new.database.postgres_uri == "b"
    assert new is not orig


def test_schema_generation():
    data = json.loads(schema_json())
    assert "properties" in data
