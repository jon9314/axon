# axon/memory/vector_store.py

from qdrant_client import QdrantClient, models
import uuid

class VectorStore:
    """
    Handles interactions with the Qdrant vector database for storing
    and searching semantic memories.
    """
    def __init__(self, host: str, port: int):
        """
        Initializes the VectorStore and connects to the Qdrant client.
        """
        try:
            self.client = QdrantClient(host=host, port=port)
            print("Successfully connected to Qdrant.")
        except Exception as e:
            print(f"Error connecting to Qdrant: {e}")
            self.client = None

    def add_memory(self, collection_name: str, text_content: str, vector: list[float]):
        """
        Adds a new memory (text and its vector representation) to a Qdrant collection.
        """
        if not self.client:
            print("No Qdrant client connection.")
            return

        # Ensure the collection exists before adding data.
        # This operation is idempotent, so it's safe to call every time.
        self.client.recreate_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(size=len(vector), distance=models.Distance.COSINE),
            on_disk_payload=True # Recommended for performance
        )

        # Use a unique ID for each memory point
        point_id = str(uuid.uuid4())

        self.client.upsert(
            collection_name=collection_name,
            points=[
                models.PointStruct(
                    id=point_id,
                    vector=vector,
                    payload={"text": text_content}
                )
            ],
            wait=True
        )
        print(f"Added memory to collection '{collection_name}'")

    def search_memory(self, collection_name: str, query_vector: list[float], limit: int = 5):
        """
        Searches for similar memories in a Qdrant collection using a query vector.
        """
        if not self.client:
            print("No Qdrant client connection.")
            return []

        try:
            search_result = self.client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=limit
            )
            print(f"Searched collection '{collection_name}' and found {len(search_result)} results.")
            return search_result
        except Exception as e:
            # This can happen if the collection doesn't exist yet.
            print(f"Could not search collection '{collection_name}': {e}")
            return []