from datetime import datetime, timedelta

from axon.memory import JSONFileMemoryStore, MemoryRecord, MemoryRepository, ReminderRecord


def test_crud_and_lock(tmp_path):
    path = tmp_path / "mem.json"
    repo = MemoryRepository(JSONFileMemoryStore(str(path)))
    rid = repo.remember_fact("hello", scope="s1")
    rec = repo.store.get(rid)
    assert isinstance(rec, MemoryRecord)
    assert rec.content == "hello"

    repo.store.update(rid, content="bye")
    assert repo.store.get(rid).content == "bye"

    repo.store.lock(rid)
    assert repo.store.get(rid).locked
    try:
        repo.store.update(rid, content="nope")
    except ValueError:
        pass
    else:
        raise AssertionError
    assert not repo.store.delete(rid)


def test_search_tags_scope(tmp_path):
    store = JSONFileMemoryStore(str(tmp_path / "s.json"))
    repo = MemoryRepository(store)
    repo.remember_fact("alpha", tags=["t1"], scope="a")
    repo.remember_fact("beta", tags=["t2"], scope="b")
    results = store.search("a", tags=["t1"], scope="a")
    assert len(results) == 1 and results[0].content == "alpha"


def test_reminder_due(tmp_path):
    store = JSONFileMemoryStore(str(tmp_path / "r.json"))
    repo = MemoryRepository(store)
    due = datetime.utcnow() + timedelta(seconds=1)
    store.put(ReminderRecord(content="hi", due_at=due))
    later = datetime.utcnow() + timedelta(seconds=2)
    res = repo.list_reminders_due(later)
    assert len(res) == 1 and res[0].content == "hi"


def test_disk_persistence(tmp_path):
    path = tmp_path / "p.json"
    repo1 = MemoryRepository(JSONFileMemoryStore(str(path)))
    rid = repo1.remember_fact("persist")

    repo2 = MemoryRepository(JSONFileMemoryStore(str(path)))
    assert repo2.store.get(rid) is not None


def test_unlock(tmp_path):
    store = JSONFileMemoryStore(str(tmp_path / "u.json"))
    repo = MemoryRepository(store)
    rid = repo.remember_fact("lock-me")
    store.lock(rid)
    assert store.get(rid).locked
    store.unlock(rid)
    assert not store.get(rid).locked
