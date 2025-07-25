import agent.llm_router as llm_router
from agent.llm_router import LLMRouter
from agent.plugin_loader import load_plugins


def test_llm_router_tool_call(monkeypatch):
    load_plugins()
    captured = {}

    class DummyAssistant:
        def __init__(self, function_list, llm, generate_cfg=None):
            captured["function_list"] = function_list
            captured["llm"] = llm
            captured["generate_cfg"] = generate_cfg

        def run_nonstream(self, messages):
            captured["messages"] = messages
            return [
                {
                    "role": "assistant",
                    "content": "",
                    "tool_calls": [{"name": "echo", "arguments": '{"text": "hi"}'}],
                },
                {
                    "role": "tool",
                    "name": "echo",
                    "content": "hi",
                },
            ]

    monkeypatch.setattr(llm_router, "Assistant", DummyAssistant)
    monkeypatch.setattr(llm_router, "TOOL_REGISTRY", {"echo": object()})

    router = LLMRouter()
    result = router.get_response("please echo hi", model="local")

    assert result == "hi"
    assert captured["function_list"] == ["echo"]
    assert any(m.get("role") == "user" for m in captured["messages"])
