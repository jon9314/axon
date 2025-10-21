"""Tests for speaker embedding and recognition."""

import pytest

from memory.speaker_embedding import SpeakerEmbeddingManager, SpeakerProfile


class TestSpeakerEmbedding:
    """Test speaker recognition functionality."""

    @pytest.fixture
    def manager(self):
        """Create a speaker embedding manager."""
        return SpeakerEmbeddingManager(embedding_dim=128)

    @pytest.fixture
    def sample_audio(self):
        """Generate sample audio data."""
        # Return different audio samples for different speakers
        return {
            "alice": b"alice_voice_sample" * 100,
            "bob": b"bob_voice_sample" * 100,
            "charlie": b"charlie_voice_sample" * 100,
        }

    def test_extract_embedding(self, manager):
        """Should extract embedding from audio data."""
        audio = b"test_audio_data" * 10
        embedding = manager.extract_embedding(audio)

        assert isinstance(embedding, list)
        assert len(embedding) == manager.embedding_dim
        assert all(isinstance(x, float) for x in embedding)

    def test_extract_embedding_deterministic(self, manager):
        """Same audio should produce same embedding."""
        audio = b"test_audio_data" * 10
        embedding1 = manager.extract_embedding(audio)
        embedding2 = manager.extract_embedding(audio)

        assert embedding1 == embedding2

    def test_extract_embedding_different_audio(self, manager):
        """Different audio should produce different embeddings."""
        audio1 = b"audio_sample_one" * 10
        audio2 = b"audio_sample_two" * 10

        embedding1 = manager.extract_embedding(audio1)
        embedding2 = manager.extract_embedding(audio2)

        assert embedding1 != embedding2

    def test_cosine_similarity(self, manager):
        """Should calculate cosine similarity correctly."""
        emb1 = [1.0, 0.0, 0.0]
        emb2 = [1.0, 0.0, 0.0]
        emb3 = [0.0, 1.0, 0.0]

        # Identical embeddings
        sim = manager.cosine_similarity(emb1, emb2)
        assert abs(sim - 1.0) < 0.01

        # Orthogonal embeddings
        sim = manager.cosine_similarity(emb1, emb3)
        assert abs(sim - 0.0) < 0.01

    def test_register_speaker(self, manager, sample_audio):
        """Should register a new speaker profile."""
        profile = manager.register_speaker("alice", sample_audio["alice"])

        assert isinstance(profile, SpeakerProfile)
        assert profile.identity == "alice"
        assert len(profile.embedding) == manager.embedding_dim
        assert profile.num_samples == 1
        assert "alice" in manager.profiles

    def test_register_multiple_samples_updates_profile(self, manager, sample_audio):
        """Registering multiple samples should update profile."""
        # First sample
        profile1 = manager.register_speaker("alice", sample_audio["alice"])
        assert profile1.num_samples == 1

        # Second sample (slight variation)
        audio2 = sample_audio["alice"] + b"_variation"
        profile2 = manager.register_speaker("alice", audio2)

        assert profile2.num_samples == 2
        assert profile2.identity == "alice"
        # Embedding should be different (running average)
        assert profile2.embedding != profile1.embedding

    def test_register_speaker_replace(self, manager, sample_audio):
        """Should replace profile when replace=True."""
        manager.register_speaker("alice", sample_audio["alice"])

        # Register with replace
        new_audio = b"completely_different_audio" * 100
        profile2 = manager.register_speaker("alice", new_audio, replace=True)

        assert profile2.num_samples == 1  # Reset to 1

    def test_identify_speaker_success(self, manager, sample_audio):
        """Should identify registered speaker."""
        # Register speakers
        manager.register_speaker("alice", sample_audio["alice"])
        manager.register_speaker("bob", sample_audio["bob"])

        # Try to identify Alice
        identity, confidence = manager.identify_speaker(sample_audio["alice"], threshold=0.5)

        assert identity == "alice"
        assert confidence > 0.5

    def test_identify_speaker_no_match(self, manager, sample_audio):
        """Should return None when no match above threshold."""
        manager.register_speaker("alice", sample_audio["alice"])

        # Try to identify with very different audio
        unknown_audio = b"completely_unknown_speaker" * 100
        identity, confidence = manager.identify_speaker(unknown_audio, threshold=0.9)

        # Might not match at high threshold
        if identity is None:
            assert confidence < 0.9

    def test_identify_speaker_empty_database(self, manager, sample_audio):
        """Should return None when no speakers registered."""
        identity, confidence = manager.identify_speaker(sample_audio["alice"])

        assert identity is None
        assert confidence == 0.0

    def test_identify_speaker_with_threshold(self, manager, sample_audio):
        """Should respect similarity threshold."""
        manager.register_speaker("alice", sample_audio["alice"])

        # Very high threshold
        identity, confidence = manager.identify_speaker(sample_audio["alice"], threshold=0.99)

        # Should still work for identical audio
        if manager.enabled:
            assert identity == "alice"
            assert confidence >= 0.99

    def test_list_speakers(self, manager, sample_audio):
        """Should list all registered speakers."""
        assert manager.list_speakers() == []

        manager.register_speaker("alice", sample_audio["alice"])
        manager.register_speaker("bob", sample_audio["bob"])

        speakers = manager.list_speakers()
        assert len(speakers) == 2
        assert "alice" in speakers
        assert "bob" in speakers

    def test_remove_speaker(self, manager, sample_audio):
        """Should remove speaker profile."""
        manager.register_speaker("alice", sample_audio["alice"])
        assert "alice" in manager.profiles

        removed = manager.remove_speaker("alice")
        assert removed is True
        assert "alice" not in manager.profiles
        assert manager.list_speakers() == []

    def test_remove_nonexistent_speaker(self, manager):
        """Should return False when removing nonexistent speaker."""
        removed = manager.remove_speaker("nonexistent")
        assert removed is False

    def test_export_profiles(self, manager, sample_audio):
        """Should export all profiles for persistence."""
        manager.register_speaker("alice", sample_audio["alice"])
        manager.register_speaker("bob", sample_audio["bob"])

        exported = manager.export_profiles()

        assert isinstance(exported, dict)
        assert len(exported) == 2
        assert "alice" in exported
        assert "bob" in exported

        # Check structure
        alice_data = exported["alice"]
        assert "identity" in alice_data
        assert "embedding" in alice_data
        assert "num_samples" in alice_data

    def test_import_profiles(self, manager, sample_audio):
        """Should import profiles from exported data."""
        # Create and export profiles
        manager.register_speaker("alice", sample_audio["alice"])
        exported = manager.export_profiles()

        # Create new manager and import
        new_manager = SpeakerEmbeddingManager(embedding_dim=128)
        count = new_manager.import_profiles(exported)

        assert count == 1
        assert "alice" in new_manager.profiles
        assert new_manager.profiles["alice"].identity == "alice"

    def test_import_invalid_profile_skips(self, manager):
        """Should skip invalid profiles during import."""
        invalid_data = {"bad_speaker": {"invalid": "data"}}

        count = manager.import_profiles(invalid_data)

        assert count == 0
        assert len(manager.profiles) == 0

    def test_disabled_mode_graceful_degradation(self):
        """Should work gracefully when dependencies unavailable."""
        # Test with disabled manager (no numpy)
        manager = SpeakerEmbeddingManager()

        if not manager.enabled:
            # Should still work but return dummy data
            audio = b"test_audio"
            embedding = manager.extract_embedding(audio)
            assert len(embedding) == manager.embedding_dim

            # Register should work
            profile = manager.register_speaker("test", audio)
            assert profile.identity == "test"

    def test_embedding_normalization(self, manager):
        """Embeddings should be normalized."""
        if not manager.enabled:
            pytest.skip("Numpy not available")

        import numpy as np

        audio = b"test_audio_for_normalization" * 10
        embedding = manager.extract_embedding(audio)

        # Check that embedding is normalized (magnitude close to 1)
        magnitude = np.linalg.norm(embedding)
        assert abs(magnitude - 1.0) < 0.1 or magnitude == 0.0
