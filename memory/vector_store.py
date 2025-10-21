# axon/memory/vector_store.py

import logging
import uuid
from typing import Any

from axon.utils.health import service_status

try:
    from qdrant_client import QdrantClient, models

    HAS_QDRANT = True
except ImportError:  # NOTE: vector features optional
    from types import SimpleNamespace

    HAS_QDRANT = False
    QdrantClient = Any  # type: ignore
    models = SimpleNamespace(
        ScoredPoint=object,
        PayloadSchemaType=SimpleNamespace(KEYWORD=object),
        Distance=SimpleNamespace(COSINE=object),
        VectorParams=object,
        FieldCondition=object,
        Filter=object,
        MatchValue=object,
        PointStruct=object,
    )


class VectorStore:
    """
    Handles interactions with the Qdrant vector database for storing
    and searching semantic memories.
    """

    def __init__(self, host: str, port: int):
        """Initialise the vector store connection."""
        self.client: QdrantClient | None = None
        if not service_status.qdrant:
            logging.info("qdrant-disabled")
            return
        if not HAS_QDRANT:
            raise RuntimeError("qdrant-client not installed; install axon[vector]")
        try:
            self.client = QdrantClient(host=host, port=port)
            logging.info("qdrant-connected")
        except Exception as e:  # pragma: no cover - network
            logging.error("qdrant-error", extra={"error": str(e)})
            service_status.qdrant = False

    def add_memory(
        self,
        collection_name: str,
        text_content: str,
        vector: list[float],
        identity: str | None = None,
    ) -> None:
        """
        Adds a new memory (text and its vector representation) to a Qdrant collection.
        """
        if not self.client:
            logging.error("qdrant-missing")
            return

        # Create the collection on first insert without wiping existing data.
        try:
            self.client.get_collection(collection_name)
        except Exception:
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(
                    size=len(vector),
                    distance=models.Distance.COSINE,
                ),
                on_disk_payload=True,
            )

        # Ensure there is an index on the identity payload field for filtering
        try:
            self.client.create_payload_index(
                collection_name,
                field_name="identity",
                field_schema=models.PayloadSchemaType.KEYWORD,
            )
        except Exception:
            pass

        # Use a unique ID for each memory point
        point_id = str(uuid.uuid4())

        self.client.upsert(
            collection_name=collection_name,
            points=[
                models.PointStruct(
                    id=point_id,
                    vector=vector,
                    payload={"text": text_content, "identity": identity},
                )
            ],
            wait=True,
        )
        logging.info("memory-added", extra={"collection": collection_name})

    def search_memory(
        self,
        collection_name: str,
        query_vector: list[float],
        limit: int = 5,
        identity: str | None = None,
    ) -> list[models.ScoredPoint]:
        """
        Searches for similar memories in a Qdrant collection using a query vector.
        """
        if not self.client:
            logging.error("qdrant-missing")
            return []

        query_filter = None
        if identity:
            query_filter = models.Filter(
                must=[
                    models.FieldCondition(
                        key="identity",
                        match=models.MatchValue(value=identity),
                    )
                ]
            )

        try:
            search_result = self.client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=limit,
                query_filter=query_filter,
            )
            logging.info(
                "memory-search",
                extra={"collection": collection_name, "results": len(search_result)},
            )
            return search_result
        except Exception as e:
            logging.error(
                "memory-search-failed", extra={"error": str(e), "collection": collection_name}
            )
            return []

    def hybrid_search(
        self,
        collection_name: str,
        query_vector: list[float],
        llm_confidence: float,
        limit: int = 5,
        identity: str | None = None,
        vector_weight: float = 0.7,
        confidence_weight: float = 0.3,
        diversity_boost: bool = True,
    ) -> list[models.ScoredPoint]:
        """Return search results with improved hybrid scoring.

        Combines vector similarity with LLM confidence using configurable weights
        and optional diversity boosting.

        Args:
            collection_name: Name of the Qdrant collection
            query_vector: Query embedding vector
            llm_confidence: Confidence score from LLM (0.0 to 1.0)
            limit: Maximum number of results
            identity: Optional identity filter
            vector_weight: Weight for vector similarity (default 0.7)
            confidence_weight: Weight for LLM confidence (default 0.3)
            diversity_boost: Apply diversity penalty to very similar results

        Returns:
            List of scored points with hybrid scores
        """
        # Fetch more results than needed if diversity boosting is enabled
        fetch_limit = limit * 2 if diversity_boost else limit

        results = self.search_memory(
            collection_name,
            query_vector,
            limit=fetch_limit,
            identity=identity,
        )

        if not results:
            return []

        # Normalize weights to sum to 1.0
        total_weight = vector_weight + confidence_weight
        norm_vector_weight = vector_weight / total_weight
        norm_confidence_weight = confidence_weight / total_weight

        # Apply hybrid scoring
        scored_results = []
        seen_scores: list[float] = []

        for r in results:
            if not hasattr(r, "score"):
                continue

            # Base hybrid score
            vector_score = r.score
            hybrid_score = (norm_vector_weight * vector_score) + (
                norm_confidence_weight * llm_confidence
            )

            # Apply diversity boost if enabled
            if diversity_boost and seen_scores:
                # Penalize results very similar to already-selected ones
                max_similarity = max(seen_scores)
                if vector_score > 0.95 * max_similarity:
                    # Slight penalty for very similar results
                    hybrid_score *= 0.95

            r.score = hybrid_score
            scored_results.append(r)
            seen_scores.append(vector_score)

        # Sort by hybrid score and return top results
        scored_results.sort(key=lambda x: x.score, reverse=True)
        return scored_results[:limit]
