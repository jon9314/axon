"""Tests for domain management API endpoints."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


class TestDomainAPI:
    """Test domain management endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client with mocked dependencies."""
        # Import here to avoid circular dependencies
        import sys
        from pathlib import Path

        # Add parent directory to path
        sys.path.insert(0, str(Path(__file__).parent.parent))

        from backend.main import app

        return TestClient(app)

    @pytest.fixture
    def mock_memory(self):
        """Create mock memory handler."""
        with patch("backend.main.memory_handler") as mock:
            yield mock

    def test_list_domains_empty(self, client, mock_memory):
        """Should return empty list when no domains exist."""
        mock_memory.list_facts.return_value = []
        mock_memory.repo.store.search.return_value = []

        response = client.get("/domains/test_thread")

        assert response.status_code == 200
        data = response.json()
        assert "domains" in data
        assert data["domains"] == []

    def test_list_domains_with_data(self, client, mock_memory):
        """Should list unique domains from memory."""
        # Mock facts with domain tags
        mock_memory.list_facts.return_value = [
            ("key1", "value1", "user1", False, ["domain:personal"]),
            ("key2", "value2", "user1", False, ["domain:project"]),
            ("key3", "value3", "user1", False, ["domain:personal"]),
        ]

        # Mock repository records
        mock_rec1 = MagicMock()
        mock_rec1.scope = "personal"
        mock_rec2 = MagicMock()
        mock_rec2.scope = "project"

        mock_memory.repo.store.search.return_value = [mock_rec1, mock_rec2]

        response = client.get("/domains/test_thread")

        assert response.status_code == 200
        data = response.json()
        assert "domains" in data
        # Should have unique domains sorted
        assert set(data["domains"]) == {"personal", "project"}

    def test_domain_stats(self, client, mock_memory):
        """Should return statistics per domain."""
        # Mock repository records with different scopes
        records = []
        for i in range(3):
            rec = MagicMock()
            rec.scope = "personal"
            records.append(rec)

        for i in range(2):
            rec = MagicMock()
            rec.scope = "project"
            records.append(rec)

        mock_memory.repo.store.search.return_value = records

        response = client.get("/domains/test_thread/stats")

        assert response.status_code == 200
        data = response.json()
        assert "domains" in data
        assert len(data["domains"]) >= 2

        # Check that stats are present
        domain_names = [d["name"] for d in data["domains"]]
        assert "personal" in domain_names
        assert "project" in domain_names

    def test_domain_stats_empty(self, client, mock_memory):
        """Should handle empty memory gracefully."""
        mock_memory.repo.store.search.return_value = []

        response = client.get("/domains/test_thread/stats")

        assert response.status_code == 200
        data = response.json()
        assert "domains" in data
        assert data["domains"] == []

    def test_memory_filtering_by_domain(self, client, mock_memory):
        """Should be able to filter memory by domain."""
        mock_memory.list_facts.return_value = [
            ("key1", "value1", "user1", False, ["tag1"]),
        ]

        response = client.get("/memory/test_thread?domain=personal")

        assert response.status_code == 200
        # Verify that list_facts was called with domain parameter
        mock_memory.list_facts.assert_called_once()
        call_args = mock_memory.list_facts.call_args
        assert call_args[0][0] == "test_thread"  # thread_id
        assert call_args[0][2] == "personal"  # domain argument

    def test_add_memory_with_domain(self, client, mock_memory):
        """Should be able to add memory with domain."""
        response = client.post(
            "/memory/test_thread",
            params={"key": "test_key", "value": "test_value", "domain": "personal"},
        )

        assert response.status_code == 200
        # Verify add_fact was called with domain
        mock_memory.add_fact.assert_called_once()
        call_args = mock_memory.add_fact.call_args
        assert call_args[1]["domain"] == "personal"

    def test_delete_memory_by_domain(self, client, mock_memory):
        """Should be able to delete all facts in a domain."""
        mock_memory.delete_facts.return_value = 5

        response = client.delete("/memory/test_thread?domain=personal")

        assert response.status_code == 200
        data = response.json()
        assert data["deleted"] == 5
        # Verify delete_facts was called with domain
        mock_memory.delete_facts.assert_called_once()
        call_args = mock_memory.delete_facts.call_args
        assert call_args[1]["domain"] == "personal"
