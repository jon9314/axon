from agent.mcp_handler import MCPHandler
from agent.plugin_loader import load_plugins
from unittest.mock import patch, MagicMock

load_plugins()

@patch('agent.tools.calculator_proxy.requests.get')
def test_handle_message(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {'result': 2}
    mock_get.return_value = mock_resp

    handler = MCPHandler()
    msg = handler.generate_message('calculator', {'command': 'evaluate', 'expr': '1+1'})
    result = handler.handle_message(msg)
    assert result['result'] == 2
