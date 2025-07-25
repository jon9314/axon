from unittest.mock import MagicMock

from typer.testing import CliRunner

import main


def test_mcp_tools_cli(monkeypatch, tmp_path):
    cfg = tmp_path / "servers.yaml"
    cfg.write_text(
        """
- name: echo
  transport: http
  url: http://testserver
"""
    )

    runner = CliRunner()

    class DummyResp:
        status_code = 200

    monkeypatch.setattr("agent.mcp_router.requests.get", MagicMock(return_value=DummyResp()))

    result = runner.invoke(main.app, ["mcp-tools", "--config", str(cfg)])
    assert result.exit_code == 0
    assert "echo" in result.stdout
