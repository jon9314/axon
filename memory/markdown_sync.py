"""Sync markdown notes with Qdrant vector store for semantic search.

This module provides bidirectional sync between markdown backup files
and the Qdrant vector database, enabling semantic search over notes.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class MarkdownQdrantSync:
    """Sync markdown notes with Qdrant vector store."""

    def __init__(
        self,
        markdown_dir: str = "data/markdown_notes",
        vector_store: Any | None = None,
        embedding_model: Any | None = None,
    ) -> None:
        """Initialize markdown-Qdrant sync.

        Args:
            markdown_dir: Directory containing markdown notes
            vector_store: VectorStore instance for Qdrant operations
            embedding_model: Model for generating embeddings
        """
        self.markdown_dir = Path(markdown_dir)
        self.markdown_dir.mkdir(parents=True, exist_ok=True)
        self.vector_store = vector_store
        self.embedding_model = embedding_model
        self.collection_name = "markdown_notes"

    def _generate_embedding(self, text: str) -> list[float]:
        """Generate embedding for text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        if self.embedding_model:
            # Use provided embedding model
            return self.embedding_model.encode(text)

        # Simple placeholder: use hash-based embedding
        # In production, use a proper model like sentence-transformers
        import hashlib

        hash_bytes = hashlib.sha256(text.encode()).digest()
        # Convert to 384-dim vector (typical for sentence embeddings)
        embedding = []
        for i in range(0, min(len(hash_bytes), 48), 1):
            # Each byte becomes 8 dimensions
            byte_val = hash_bytes[i] / 255.0
            embedding.extend([byte_val] * 8)

        # Pad to 384 dimensions
        while len(embedding) < 384:
            embedding.append(0.0)

        return embedding[:384]

    def sync_markdown_to_qdrant(
        self, note_name: str | None = None, force: bool = False
    ) -> int:
        """Sync markdown notes to Qdrant.

        Args:
            note_name: Specific note to sync, or None for all
            force: Force re-sync even if already synced

        Returns:
            Number of notes synced
        """
        if not self.vector_store:
            logger.warning("No vector store configured, skipping sync")
            return 0

        notes_to_sync = []

        if note_name:
            # Sync specific note
            note_path = self.markdown_dir / f"{note_name}.md"
            if note_path.exists():
                notes_to_sync.append(note_path)
        else:
            # Sync all notes
            notes_to_sync = list(self.markdown_dir.glob("*.md"))

        synced_count = 0
        for note_path in notes_to_sync:
            try:
                content = note_path.read_text(encoding="utf-8")
                note_id = note_path.stem

                # Generate embedding
                embedding = self._generate_embedding(content)

                # Add to Qdrant
                self.vector_store.add_memory(
                    collection_name=self.collection_name,
                    text_content=content,
                    vector=embedding,
                    identity=note_id,
                )

                synced_count += 1
                logger.info("synced-markdown-to-qdrant", extra={"note": note_id})

            except Exception as e:
                logger.error(
                    "markdown-sync-error", extra={"note": note_path.name, "error": str(e)}
                )

        return synced_count

    def sync_qdrant_to_markdown(self, identity: str | None = None) -> int:
        """Sync Qdrant vectors back to markdown files.

        Args:
            identity: Specific identity to sync, or None for all

        Returns:
            Number of notes exported
        """
        if not self.vector_store:
            logger.warning("No vector store configured, skipping export")
            return 0

        try:
            # Search for all vectors in collection
            # This is a simplified approach - in production you'd page through results
            results = self.vector_store.search_memory(
                collection_name=self.collection_name,
                query_vector=[0.0] * 384,  # Dummy vector to get all
                limit=1000,
                identity=identity,
            )

            exported_count = 0
            for result in results:
                if hasattr(result, "payload"):
                    note_id = result.payload.get("identity")
                    content = result.payload.get("text")

                    if note_id and content:
                        note_path = self.markdown_dir / f"{note_id}.md"
                        note_path.write_text(content, encoding="utf-8")
                        exported_count += 1
                        logger.info("exported-qdrant-to-markdown", extra={"note": note_id})

            return exported_count

        except Exception as e:
            logger.error("markdown-export-error", extra={"error": str(e)})
            return 0

    def search_notes(self, query: str, limit: int = 5) -> list[dict]:
        """Search notes semantically.

        Args:
            query: Search query
            limit: Maximum results

        Returns:
            List of matching notes with scores
        """
        if not self.vector_store:
            return []

        # Generate query embedding
        query_embedding = self._generate_embedding(query)

        # Search Qdrant
        results = self.vector_store.search_memory(
            collection_name=self.collection_name, query_vector=query_embedding, limit=limit
        )

        matches = []
        for result in results:
            if hasattr(result, "payload") and hasattr(result, "score"):
                matches.append(
                    {
                        "note_id": result.payload.get("identity"),
                        "content": result.payload.get("text"),
                        "score": result.score,
                    }
                )

        return matches

    def get_sync_status(self) -> dict:
        """Get sync status information.

        Returns:
            Dictionary with sync statistics
        """
        markdown_count = len(list(self.markdown_dir.glob("*.md")))

        qdrant_count = 0
        if self.vector_store:
            try:
                # Attempt to get collection info
                _ = self.vector_store.search_memory(
                    collection_name=self.collection_name, query_vector=[0.0] * 384, limit=1
                )
                # This is approximate - real impl would query collection stats
                qdrant_count = len(
                    self.vector_store.search_memory(
                        collection_name=self.collection_name, query_vector=[0.0] * 384, limit=10000
                    )
                )
            except Exception:
                qdrant_count = 0

        return {
            "markdown_notes": markdown_count,
            "qdrant_vectors": qdrant_count,
            "in_sync": markdown_count == qdrant_count,
        }

    def auto_sync(self) -> dict:
        """Automatically sync in both directions.

        Returns:
            Dictionary with sync results
        """
        to_qdrant = self.sync_markdown_to_qdrant()
        to_markdown = self.sync_qdrant_to_markdown()

        return {"synced_to_qdrant": to_qdrant, "exported_to_markdown": to_markdown}
