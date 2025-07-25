import json
from datetime import datetime

from pydantic import SecretStr

from axon.obs.records import PluginCallRecord, RunRecord


def test_secrets_are_redacted(monkeypatch):
    monkeypatch.setenv("LOG_REDACT_SECRETS", "1")
    call = PluginCallRecord(
        plugin="p",
        started_at=datetime.utcnow(),
        ended_at=datetime.utcnow(),
        duration_ms=1.0,
        truncated_input={"api_key": "secret"},
        truncated_output=SecretStr("token123"),
    )
    rec = RunRecord(id="1", started_at=datetime.utcnow(), plugin_calls=[call])
    data = json.loads(rec.to_json())
    assert data["plugin_calls"][0]["truncated_input"]["api_key"] == "REDACTED"
    assert data["plugin_calls"][0]["truncated_output"] == "REDACTED"
