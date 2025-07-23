from agent.response_shaper import ResponseShaper
import agent.llm_router as llm_router
from agent.llm_router import LLMRouter


class DummyAssistant:
    def __init__(self, function_list, llm, generate_cfg=None):
        pass

    def run_nonstream(self, messages):
        return [{"role": "assistant", "content": "I am ready to help you."}]


def test_informal_contractions():
    shaper = ResponseShaper()
    result = shaper.shape("I am fine and you are great", tone="informal")
    assert "I'm" in result
    assert "you're" in result


def test_router_profile_styles(monkeypatch):
    monkeypatch.setattr(llm_router, "Assistant", DummyAssistant)
    monkeypatch.setattr(llm_router, "TOOL_REGISTRY", {})
    router = LLMRouter()
    neutral = router.get_response(
        "hi", model="local", persona="assistant", tone="neutral"
    )
    informal = router.get_response(
        "hi", model="local", persona="partner", tone="informal"
    )
    assert neutral != informal
    assert informal.startswith("Hey there,")
    assert "I'm" in informal
