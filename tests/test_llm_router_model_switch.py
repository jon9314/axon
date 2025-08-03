from agent.llm_router import LLMRouter


def test_llm_router_recreates_assistant_for_new_model(monkeypatch):
    created_models = []

    class DummyAssistant:
        def __init__(self, *, function_list, llm, generate_cfg):
            created_models.append(llm["model"])

        def run_nonstream(self, messages):
            return [{"content": "ok"}]

    monkeypatch.setattr("agent.llm_router.Assistant", DummyAssistant)

    router = LLMRouter()
    router.get_response("hi", model="model-a")
    # Reusing same model should not create a new assistant
    router.get_response("hi", model="model-a")
    # Switching model should recreate assistant
    router.get_response("hi", model="model-b")

    assert created_models == ["model-a", "model-b"]
