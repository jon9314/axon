from pathlib import Path

import pytest

from axon.obs.tracer import run_tracer
from axon.plugins.loader import PluginLoader
from tests.plugins.test_loader import make_plugin


def test_error_is_captured_in_record(tmp_path: Path):
    make_plugin(tmp_path, "p")
    loader = PluginLoader(plugin_dir=tmp_path)
    loader.discover()

    with pytest.raises(KeyError):
        with run_tracer("test") as rec:
            loader.execute("missing", {})

    assert rec.error is not None
