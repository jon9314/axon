from agent.pasteback_handler import PastebackHandler
from agent.llm_router import LLMRouter
import json

class DummyMemory:
    def __init__(self):
        self.calls = []
    def add_fact(self, thread_id, key, value, identity=None):
        self.calls.append((thread_id, key, value, identity))


def test_store_adds_two_facts():
    mem = DummyMemory()
    handler = PastebackHandler(mem)
    handler.store('t1', 'prompt text', 'reply text', model='gpt-4o')
    assert len(mem.calls) == 2
    first_key = mem.calls[0][1]
    second_key = mem.calls[1][1]
    assert first_key.startswith('cloud_prompt_')
    assert second_key.startswith('cloud_response_')
    assert mem.calls[0][0] == 't1'
    assert mem.calls[0][2] == 'prompt text'
    assert mem.calls[1][2] == 'reply text'
    assert mem.calls[0][3] == 'gpt-4o'
    assert mem.calls[1][3] == 'gpt-4o'


def test_full_copy_paste_cycle():
    mem = DummyMemory()
    handler = PastebackHandler(mem)
    router = LLMRouter()
    prompt_json = json.loads(router.get_response('Please summarize these notes', model='local'))
    handler.store('t2', prompt_json['prompt'], 'result text', model=prompt_json['model'])
    assert len(mem.calls) == 2

