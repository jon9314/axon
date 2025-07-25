import agent.llm_router as llm_router
from agent.llm_router import LLMRouter
from agent.response_shaper import ResponseShaper


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


def test_formal_expansions():
    shaper = ResponseShaper()
    result = shaper.shape("I'm happy you're here", tone="formal")
    assert "I am" in result
    assert "you are" in result


def test_max_length_truncates():
    shaper = ResponseShaper(max_length=5)
    result = shaper.shape("hello world")
    assert result == "hello"


def test_router_profile_styles(monkeypatch):
    monkeypatch.setattr(llm_router, "Assistant", DummyAssistant)
    monkeypatch.setattr(llm_router, "TOOL_REGISTRY", {})
    router = LLMRouter()
    neutral = router.get_response("hi", model="local", persona="assistant", tone="neutral")
    informal = router.get_response("hi", model="local", persona="partner", tone="informal")
    assert neutral != informal
    assert informal.startswith("Hey there,")
    assert "I'm" in informal
