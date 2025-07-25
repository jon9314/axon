# axon/memory/vector_store.py

import logging
import uuid

from qdrant_client import QdrantClient, models


class VectorStore:
    """
    Handles interactions with the Qdrant vector database for storing
    and searching semantic memories.
    """

    def __init__(self, host: str, port: int):
        """
        Initializes the VectorStore and connects to the Qdrant client.
        """
        self.client: QdrantClient | None
        try:
            self.client = QdrantClient(host=host, port=port)
            logging.info("qdrant-connected")
        except Exception as e:
            logging.error("qdrant-error", extra={"error": str(e)})
            self.client = None

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
    ) -> list[models.ScoredPoint]:
        """Return search results weighted by an LLM confidence score."""
        results = self.search_memory(
            collection_name,
            query_vector,
            limit=limit,
            identity=identity,
        )
        for r in results:
            if hasattr(r, "score"):
                r.score = 0.5 * r.score + 0.5 * llm_confidence
        return results
