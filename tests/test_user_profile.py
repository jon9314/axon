from axon.memory import JSONFileMemoryStore, MemoryRepository
from memory.user_profile import UserProfileManager


def test_profile_manager_round_trip(tmp_path):
    repo = MemoryRepository(JSONFileMemoryStore(str(tmp_path / "mem.json")))
    mgr = UserProfileManager(repository=repo, prefs_path=str(tmp_path / "none.yaml"))
    mgr.set_profile("jon", persona="partner", tone="informal", email="a@example.com")
    profile = mgr.get_profile("jon")
    assert profile["persona"] == "partner"
    assert profile["tone"] == "informal"
    assert profile["email"] == "a@example.com"


def test_load_from_yaml(tmp_path):
    sample = tmp_path / "prefs.yaml"
    sample.write_text("user1:\n  persona: friend\n  tone: happy\n")
    repo = MemoryRepository(JSONFileMemoryStore(str(tmp_path / "m.json")))
    mgr = UserProfileManager(repository=repo, prefs_path=str(sample))
    profile = mgr.get_profile("user1")
    assert profile["persona"] == "friend"
    assert profile["tone"] == "happy"
