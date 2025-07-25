import json

from agent.fallback_prompt import suggest_model
from agent.llm_router import LLMRouter


def test_suggest_model():
    model, reason = suggest_model("Please summarize this text")
    assert model.startswith("claude")
    assert "summariz" in reason.lower()


def test_suggest_model_analysis():
    model, reason = suggest_model("Analyze this data")
    assert model == "gpt-4o"
    assert "analy" in reason.lower()


def test_llm_router_cloud_prompt_on_long_input():
    router = LLMRouter()
    long_msg = "x" * 500
    result = router.get_response(long_msg, model="local")
    data = json.loads(result)
    assert data["type"] == "cloud_prompt"
    assert "prompt" in data
    assert "reason" in data


def test_llm_router_keyword_triggers_fallback():
    router = LLMRouter()
    result = router.get_response("Please analyze this", model="local")
    data = json.loads(result)
    assert data["model"] == "gpt-4o"
