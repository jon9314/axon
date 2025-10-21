"""Speaker embedding and recognition for voice-based identity tracking.

This module provides optional speaker recognition capabilities using voice
embeddings to identify users by their speech patterns.
"""

from __future__ import annotations

import hashlib
import logging
from typing import Any, Optional

from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Check for optional dependencies
try:
    import numpy as np

    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    np: Any = None  # type: ignore


class SpeakerProfile(BaseModel):
    """Profile for a speaker with voice embedding."""

    identity: str
    embedding: list[float]
    num_samples: int = 1
    last_updated: Optional[str] = None


class SpeakerEmbeddingManager:
    """Manage speaker profiles and perform voice-based identification.

    This is an optional feature that requires audio processing capabilities.
    When dependencies are not available, it operates in a pass-through mode.
    """

    def __init__(self, embedding_dim: int = 128) -> None:
        """Initialize speaker embedding manager.

        Args:
            embedding_dim: Dimension of speaker embeddings
        """
        self.embedding_dim = embedding_dim
        self.profiles: dict[str, SpeakerProfile] = {}
        self.enabled = HAS_NUMPY

        if not self.enabled:
            logger.warning(
                "Speaker embedding disabled: numpy not available. "
                "Install with: pip install numpy"
            )

    def extract_embedding(self, audio_data: bytes) -> list[float]:
        """Extract speaker embedding from audio data.

        This is a placeholder implementation. In production, you would use
        a proper speaker recognition model like:
        - SpeechBrain
        - pyannote.audio
        - Resemblyzer

        Args:
            audio_data: Raw audio bytes

        Returns:
            Speaker embedding vector
        """
        if not self.enabled:
            # Return dummy embedding
            return [0.0] * self.embedding_dim

        # Placeholder: Generate pseudo-embedding from audio hash
        # In production, use actual speaker recognition model
        audio_hash = hashlib.sha256(audio_data).digest()
        embedding = []
        for i in range(0, min(len(audio_hash), self.embedding_dim), 4):
            # Convert 4 bytes to float
            bytes_chunk = audio_hash[i : i + 4]
            value = int.from_bytes(bytes_chunk, byteorder="big") / (2**32)
            embedding.append(value)

        # Pad if necessary
        while len(embedding) < self.embedding_dim:
            embedding.append(0.0)

        # Normalize
        if self.enabled and np:
            embedding_array = np.array(embedding)
            norm = np.linalg.norm(embedding_array)
            if norm > 0:
                embedding_array = embedding_array / norm
            embedding = embedding_array.tolist()

        return embedding[: self.embedding_dim]

    def cosine_similarity(self, emb1: list[float], emb2: list[float]) -> float:
        """Calculate cosine similarity between two embeddings.

        Args:
            emb1: First embedding vector
            emb2: Second embedding vector

        Returns:
            Similarity score between -1 and 1
        """
        if not self.enabled or not np:
            return 0.0

        vec1 = np.array(emb1)
        vec2 = np.array(emb2)

        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(dot_product / (norm1 * norm2))

    def register_speaker(
        self, identity: str, audio_data: bytes, replace: bool = False
    ) -> SpeakerProfile:
        """Register a new speaker profile.

        Args:
            identity: Speaker identity
            audio_data: Audio sample for embedding extraction
            replace: Whether to replace existing profile

        Returns:
            Created or updated speaker profile
        """
        embedding = self.extract_embedding(audio_data)

        if identity in self.profiles and not replace:
            # Update existing profile with running average
            existing = self.profiles[identity]

            if self.enabled and np:
                existing_emb = np.array(existing.embedding)
                new_emb = np.array(embedding)

                # Running average
                n = existing.num_samples
                updated_emb = (existing_emb * n + new_emb) / (n + 1)

                profile = SpeakerProfile(
                    identity=identity, embedding=updated_emb.tolist(), num_samples=n + 1
                )
            else:
                # Without numpy, just use the new embedding
                profile = SpeakerProfile(
                    identity=identity, embedding=embedding, num_samples=existing.num_samples + 1
                )
        else:
            profile = SpeakerProfile(identity=identity, embedding=embedding)

        self.profiles[identity] = profile
        logger.info("speaker-registered", extra={"identity": identity})
        return profile

    def identify_speaker(
        self, audio_data: bytes, threshold: float = 0.7
    ) -> tuple[Optional[str], float]:
        """Identify speaker from audio sample.

        Args:
            audio_data: Audio sample
            threshold: Minimum similarity threshold for identification

        Returns:
            Tuple of (identity, confidence) or (None, 0.0) if no match
        """
        if not self.profiles:
            return None, 0.0

        query_embedding = self.extract_embedding(audio_data)

        best_match: Optional[str] = None
        best_similarity = 0.0

        for identity, profile in self.profiles.items():
            similarity = self.cosine_similarity(query_embedding, profile.embedding)

            if similarity > best_similarity:
                best_similarity = similarity
                best_match = identity

        if best_similarity >= threshold:
            logger.info(
                "speaker-identified",
                extra={"identity": best_match, "confidence": best_similarity},
            )
            return best_match, best_similarity

        logger.info(
            "speaker-unknown", extra={"best_similarity": best_similarity, "threshold": threshold}
        )
        return None, 0.0

    def list_speakers(self) -> list[str]:
        """List all registered speaker identities.

        Returns:
            List of speaker identities
        """
        return list(self.profiles.keys())

    def remove_speaker(self, identity: str) -> bool:
        """Remove a speaker profile.

        Args:
            identity: Speaker identity to remove

        Returns:
            True if removed, False if not found
        """
        if identity in self.profiles:
            del self.profiles[identity]
            logger.info("speaker-removed", extra={"identity": identity})
            return True
        return False

    def export_profiles(self) -> dict[str, dict]:
        """Export all speaker profiles for persistence.

        Returns:
            Dictionary of speaker profiles
        """
        return {identity: profile.model_dump() for identity, profile in self.profiles.items()}

    def import_profiles(self, data: dict[str, dict]) -> int:
        """Import speaker profiles from exported data.

        Args:
            data: Dictionary of speaker profile data

        Returns:
            Number of profiles imported
        """
        count = 0
        for identity, profile_data in data.items():
            try:
                profile = SpeakerProfile(**profile_data)
                self.profiles[identity] = profile
                count += 1
            except Exception as e:
                logger.error("speaker-import-error", extra={"identity": identity, "error": str(e)})

        logger.info("speakers-imported", extra={"count": count})
        return count
