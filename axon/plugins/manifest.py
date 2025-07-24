from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, ValidationError

from .permissions import Permission


class Manifest(BaseModel):
    """Plugin manifest data."""

    name: str
    version: str
    description: str
    entrypoint: str
    permissions: list[Permission] = []
    config_schema: dict[str, str] | None = None


def load_manifest(path: Path) -> Manifest:
    """Load and validate a plugin manifest."""

    if not path.exists():
        raise FileNotFoundError(f"Missing manifest: {path}")

    if path.suffix == ".yaml":
        raw: Any = yaml.safe_load(path.read_text())
    elif path.suffix == ".toml":
        raw = tomllib.loads(path.read_text())
    else:  # pragma: no cover - unsupported ext
        raise ValueError(f"Unsupported manifest format: {path.suffix}")

    try:
        return Manifest.model_validate(raw or {})
    except ValidationError as exc:
        raise ValueError(f"Invalid manifest {path}: {exc}") from exc
