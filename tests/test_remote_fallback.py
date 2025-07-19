from agent.fallback_prompt import suggest_model, generate_prompt
from agent.llm_router import LLMRouter
import json


def test_suggest_model():
    model, reason = suggest_model("Please summarize this text")
    assert model.startswith("claude")
    assert "summarization" in reason.lower()


def test_llm_router_cloud_prompt_on_long_input():
    router = LLMRouter(server_url="http://invalid")
    long_msg = "x" * 500
    result = router.get_response(long_msg, model="local")
    data = json.loads(result)
    assert data["type"] == "cloud_prompt"
    assert "prompt" in data
