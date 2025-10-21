"""Tests for hybrid vector scoring algorithm."""

from unittest.mock import MagicMock, patch

import pytest

from memory.vector_store import VectorStore


class TestHybridScoring:
    """Test improved hybrid scoring algorithm."""

    @pytest.fixture
    def mock_vector_store(self):
        """Create a mock VectorStore with client disabled."""
        with patch("memory.vector_store.service_status") as mock_status:
            mock_status.qdrant = False
            store = VectorStore("localhost", 6333)
            return store

    def test_hybrid_search_with_no_results(self, mock_vector_store):
        """Hybrid search should handle empty results gracefully."""
        mock_vector_store.client = MagicMock()
        mock_vector_store.client.search.return_value = []

        results = mock_vector_store.hybrid_search(
            "test_collection", [0.1] * 10, llm_confidence=0.8
        )

        assert results == []

    def test_hybrid_search_applies_weights(self, mock_vector_store):
        """Hybrid scoring should apply configurable weights."""
        # Create mock scored points
        mock_point1 = MagicMock()
        mock_point1.score = 0.9  # High vector similarity

        mock_point2 = MagicMock()
        mock_point2.score = 0.5  # Lower vector similarity

        mock_vector_store.client = MagicMock()
        mock_vector_store.client.search.return_value = [mock_point1, mock_point2]

        # High vector weight, low confidence weight
        results = mock_vector_store.hybrid_search(
            "test_collection",
            [0.1] * 10,
            llm_confidence=0.3,
            vector_weight=0.9,
            confidence_weight=0.1,
        )

        # With high vector weight, point1 should score higher
        assert len(results) == 2
        # First result should have higher score than second
        assert results[0].score > results[1].score

    def test_hybrid_search_diversity_boost(self, mock_vector_store):
        """Diversity boost should penalize very similar results."""
        # Create mock points with very similar scores
        mock_point1 = MagicMock()
        mock_point1.score = 0.98

        mock_point2 = MagicMock()
        mock_point2.score = 0.97  # Very similar to point1

        mock_point3 = MagicMock()
        mock_point3.score = 0.80  # More diverse

        mock_vector_store.client = MagicMock()
        mock_vector_store.client.search.return_value = [mock_point1, mock_point2, mock_point3]

        # Run with diversity boost enabled
        results = mock_vector_store.hybrid_search(
            "test_collection",
            [0.1] * 10,
            llm_confidence=0.5,
            limit=3,
            diversity_boost=True,
        )

        assert len(results) == 3

    def test_hybrid_search_respects_limit(self, mock_vector_store):
        """Hybrid search should return at most 'limit' results."""
        # Create 10 mock points
        mock_points = []
        for i in range(10):
            point = MagicMock()
            point.score = 0.9 - (i * 0.05)
            mock_points.append(point)

        mock_vector_store.client = MagicMock()
        mock_vector_store.client.search.return_value = mock_points

        results = mock_vector_store.hybrid_search(
            "test_collection", [0.1] * 10, llm_confidence=0.7, limit=5
        )

        assert len(results) == 5

    def test_hybrid_search_sorts_by_score(self, mock_vector_store):
        """Results should be sorted by hybrid score descending."""
        mock_point1 = MagicMock()
        mock_point1.score = 0.5

        mock_point2 = MagicMock()
        mock_point2.score = 0.9

        mock_point3 = MagicMock()
        mock_point3.score = 0.7

        mock_vector_store.client = MagicMock()
        # Return in random order
        mock_vector_store.client.search.return_value = [mock_point1, mock_point2, mock_point3]

        results = mock_vector_store.hybrid_search(
            "test_collection", [0.1] * 10, llm_confidence=0.5
        )

        # Should be sorted highest to lowest
        for i in range(len(results) - 1):
            assert results[i].score >= results[i + 1].score

    def test_confidence_weight_affects_scoring(self, mock_vector_store):
        """Higher confidence weight should boost scores with high LLM confidence."""
        # Create separate mock points for each test
        mock_point_low = MagicMock()
        mock_point_low.score = 0.6  # Moderate vector score

        mock_point_high = MagicMock()
        mock_point_high.score = 0.6  # Same vector score

        mock_vector_store.client = MagicMock()

        # Test with low LLM confidence
        mock_vector_store.client.search.return_value = [mock_point_low]
        results_low_conf = mock_vector_store.hybrid_search(
            "test_collection",
            [0.1] * 10,
            llm_confidence=0.2,
            vector_weight=0.5,
            confidence_weight=0.5,
        )
        low_score = results_low_conf[0].score

        # Test with high LLM confidence
        mock_vector_store.client.search.return_value = [mock_point_high]
        results_high_conf = mock_vector_store.hybrid_search(
            "test_collection",
            [0.1] * 10,
            llm_confidence=0.9,
            vector_weight=0.5,
            confidence_weight=0.5,
        )
        high_score = results_high_conf[0].score

        # Higher confidence should result in higher hybrid score
        assert high_score > low_score
