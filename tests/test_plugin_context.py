from agent.plugin_context import PluginContext, context
from axon.plugins.loader import PluginLoader


class DummyMemory:
    def __init__(self):
        self.add_calls = []

    def add_fact(self, thread_id, key, value, identity=None, domain=None, tags=None):
        self.add_calls.append((thread_id, key, value, identity))


class DummyGoals:
    def __init__(self):
        self.calls = []

    def add_goal(self, thread_id, text, identity=None, priority=0, deadline=None):
        self.calls.append((thread_id, text, identity, priority, deadline))


def test_context_helpers():
    mem = DummyMemory()
    goals = DummyGoals()
    ctx = PluginContext(memory_handler=mem, goal_tracker=goals, thread_id="t1", identity="bob")
    ctx.add_fact("k", "v")
    ctx.add_goal("do it", priority=2)
    assert mem.add_calls == [("t1", "k", "v", "bob")]
    assert goals.calls == [("t1", "do it", "bob", 2, None)]


def test_demo_plugin(monkeypatch):
    mem = DummyMemory()
    goals = DummyGoals()
    monkeypatch.setattr(context, "memory_handler", mem)
    monkeypatch.setattr(context, "goal_tracker", goals)
    loader = PluginLoader()
    loader.discover()
    result = loader.execute("remember_goal", {"key": "topic", "value": "fact", "goal": "goal text"})
    assert result == "ok"
    assert mem.add_calls
    assert goals.calls
