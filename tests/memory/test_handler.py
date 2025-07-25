from axon.memory import JSONFileMemoryStore, MemoryRepository
from memory.memory_handler import MemoryHandler


def test_update_preserves_fields(tmp_path):
    store = JSONFileMemoryStore(str(tmp_path / "h.json"))
    handler = MemoryHandler()
    handler.repo = MemoryRepository(store)

    handler.add_fact("t1", "r1", "hello", identity="bob", tags=["a", "b"])

    handler.update_fact("t1", "r1", "bye")
    rec = store.get("r1")
    assert rec.content == "bye"
    assert rec.tags == ["a", "b"]
    assert rec.metadata == {"identity": "bob"}
