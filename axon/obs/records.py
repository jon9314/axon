from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any

from pydantic import BaseModel, SecretStr


class ErrorRecord(BaseModel):
    type: str
    message: str
    traceback: str


class PluginCallRecord(BaseModel):
    plugin: str
    started_at: datetime
    ended_at: datetime | None = None
    duration_ms: float | None = None
    truncated_input: Any | None = None
    truncated_output: Any | None = None
    success: bool = True
    error: ErrorRecord | None = None


class RunRecord(BaseModel):
    id: str
    started_at: datetime
    ended_at: datetime | None = None
    mode: str | None = None
    cycle: int | None = None
    model: str | None = None
    input_preview: str | None = None
    output_preview: str | None = None
    tokens_in: int | None = None
    tokens_out: int | None = None
    plugin_calls: list[PluginCallRecord] = []
    error: ErrorRecord | None = None

    def to_json(self) -> str:
        data = self.model_dump(mode="json")
        if os.getenv("LOG_REDACT_SECRETS") == "1":
            data = _redact(data)
        return json.dumps(data)


def _redact(obj: Any) -> Any:
    if isinstance(obj, dict):
        redacted: dict[str, Any] = {}
        for k, v in obj.items():
            if isinstance(v, str) and _looks_secret(k):
                redacted[k] = "REDACTED"
            else:
                redacted[k] = _redact(v)
        return redacted
    if isinstance(obj, list):
        return [_redact(v) for v in obj]
    if isinstance(obj, SecretStr):
        return "REDACTED"
    if isinstance(obj, str) and set(obj) == {"*"}:
        return "REDACTED"
    return obj


def _looks_secret(key: str) -> bool:
    key = key.lower()
    return any(part in key for part in ["token", "secret", "key", "password"])
