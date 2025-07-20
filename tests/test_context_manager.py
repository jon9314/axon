from agent.context_manager import ContextManager, ChatMessage

class DummyMemory:
    def __init__(self):
        self.add_calls = []
    def add_fact(self, thread_id, key, value, identity=None):
        self.add_calls.append((thread_id, key, value, identity))
    def update_fact(self, *a, **k):
        pass
    def delete_fact(self, *a, **k):
        return False
    def set_lock(self, *a, **k):
        return False

class DummyGoalTracker:
    def __init__(self):
        self.detect_calls = []
    def detect_and_add_goal(self, thread_id, text, identity=None):
        self.detect_calls.append((thread_id, text, identity))


def test_chat_history_records_identity(monkeypatch):
    monkeypatch.setattr("agent.context_manager.MemoryHandler", lambda db_uri=None: DummyMemory())
    tracker = DummyGoalTracker()
    cm = ContextManager(thread_id="t1", identity="alice", goal_tracker=tracker)
    cm.add_chat_message("hello")
    cm.add_chat_message("hi", identity="bob")
    assert cm.chat_history == [ChatMessage("alice", "hello"), ChatMessage("bob", "hi")]
    assert tracker.detect_calls[-1] == ("t1", "hi", "bob")
