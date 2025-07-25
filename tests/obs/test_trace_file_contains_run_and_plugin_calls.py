from __future__ import annotations

import json
from pathlib import Path

from axon.obs.tracer import run_tracer
from axon.plugins.loader import PluginLoader
from tests.plugins.test_loader import make_plugin


def test_trace_file_contains_run_and_plugin_calls(tmp_path: Path) -> None:
    trace = tmp_path / "trace.jsonl"
    make_plugin(tmp_path, "p")
    loader = PluginLoader(plugin_dir=tmp_path)
    loader.discover()
    with run_tracer("test", cycle=1) as rec:
        loader.execute("p", {"text": "hi"})
    trace.write_text(rec.to_json() + "\n")

    data = [json.loads(line) for line in trace.read_text().splitlines()]
    assert len(data) == 1
    assert data[0]["plugin_calls"][0]["plugin"] == "p"
