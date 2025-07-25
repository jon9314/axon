from types import SimpleNamespace

import pytest

from axon.utils.health import service_status
from memory.vector_store import HAS_QDRANT, VectorStore

pytestmark = pytest.mark.skipif(
    not service_status.qdrant,
    reason="Qdrant service unavailable; skipping vector-db tests",
)

if HAS_QDRANT:
    from qdrant_client.http import models
else:  # pragma: no cover - optional qdrant
    models = SimpleNamespace(PayloadSchemaType=SimpleNamespace(KEYWORD=object))


class DummyQdrantClient:
    def __init__(self):
        self.collections = {}
        self.indices = []

    def create_collection(self, collection_name, vectors_config, on_disk_payload=True):
        self.collections.setdefault(collection_name, [])

    def get_collection(self, collection_name):
        if collection_name not in self.collections:
            raise ValueError("Collection not found")
        return self.collections[collection_name]

    def recreate_collection(self, collection_name, vectors_config, on_disk_payload=True):
        # Compatibility shim for older tests
        self.collections[collection_name] = []

    def create_payload_index(
        self,
        collection_name,
        field_name,
        field_schema=models.PayloadSchemaType.KEYWORD,
        **kwargs,
    ):
        self.indices.append((collection_name, field_name))

    def upsert(self, collection_name, points, wait=True):
        self.collections.setdefault(collection_name, []).extend(points)

    def search(self, collection_name, query_vector, limit=5, query_filter=None, **kwargs):
        points = self.collections.get(collection_name, [])
        results = []
        for p in points:
            if query_filter and query_filter.must:
                cond = query_filter.must[0]
                if p.payload.get(cond.key) != cond.match.value:
                    continue
            results.append(SimpleNamespace(id=p.id, payload=p.payload, score=1.0))
        return results[:limit]


def make_store(dummy):
    store = VectorStore(host="ignore", port=0)
    store.client = dummy
    return store


def test_search_filters_by_identity():
    if not HAS_QDRANT:
        pytest.skip("qdrant-client missing")
    dummy = DummyQdrantClient()
    store = make_store(dummy)
    store.add_memory("col", "a1", [0.1], identity="alice")
    store.add_memory("col", "b1", [0.1], identity="bob")

    alice = store.search_memory("col", [0.1], identity="alice")
    bob = store.search_memory("col", [0.1], identity="bob")
    assert len(alice) == 1
    assert alice[0].payload["identity"] == "alice"
    assert len(bob) == 1
    assert bob[0].payload["identity"] == "bob"


def test_hybrid_search_scores_adjusted():
    if not HAS_QDRANT:
        pytest.skip("qdrant-client missing")
    dummy = DummyQdrantClient()
    store = make_store(dummy)
    store.add_memory("col", "a1", [0.1], identity="alice")
    results = store.hybrid_search("col", [0.1], llm_confidence=0.8, identity="alice")
    assert results[0].payload["identity"] == "alice"
    assert results[0].score == 0.5 * 1.0 + 0.5 * 0.8
