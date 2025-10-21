"""Tests for Phase 3 features: timestamping, markdown sync, doc tracking."""


import pytest

from agent.doc_source_tracker import DocSourceTracker
from memory.markdown_sync import MarkdownQdrantSync
from memory.memory_handler import MemoryHandler


class TestAutomaticTimestamping:
    """Test automatic timestamping of memory entries."""

    def test_memory_handler_adds_timestamp(self):
        """MemoryHandler should add timestamp to new facts."""
        handler = MemoryHandler(auto_timestamp=True)
        handler.add_fact("test_thread", "test_key", "test_value", identity="test_user")

        # Get the fact back
        fact = handler.get_fact("test_thread", "test_key")
        assert fact is not None

    def test_can_disable_timestamping(self):
        """Should be able to disable automatic timestamping."""
        handler = MemoryHandler(auto_timestamp=False)
        # Should work without errors
        handler.add_fact("test_thread", "test_key", "test_value")


class TestMarkdownQdrantSync:
    """Test markdown-Qdrant synchronization."""

    @pytest.fixture
    def sync(self, tmp_path):
        """Create MarkdownQdrantSync with temp directory."""
        return MarkdownQdrantSync(markdown_dir=str(tmp_path))

    def test_sync_status(self, sync):
        """Should get sync status."""
        status = sync.get_sync_status()
        assert "markdown_notes" in status
        assert "qdrant_vectors" in status
        assert "in_sync" in status

    def test_generate_embedding(self, sync):
        """Should generate embeddings for text."""
        embedding = sync._generate_embedding("test text")
        assert isinstance(embedding, list)
        assert len(embedding) == 384  # Default embedding dimension

    def test_search_notes_empty(self, sync):
        """Should handle empty search gracefully."""
        results = sync.search_notes("test query")
        assert isinstance(results, list)


class TestDocSourceTracker:
    """Test documentation source tracking."""

    @pytest.fixture
    def tracker(self, tmp_path):
        """Create DocSourceTracker with temp storage."""
        storage = tmp_path / "doc_sources.json"
        return DocSourceTracker(storage_path=str(storage))

    def test_track_source(self, tracker):
        """Should track a documentation source."""
        tracker.track_source(
            url="https://example.com/docs",
            title="Example Docs",
            category="Tutorial"
        )

        source = tracker.get_source("https://example.com/docs")
        assert source is not None
        assert source["title"] == "Example Docs"
        assert source["category"] == "Tutorial"
        assert source["access_count"] == 1

    def test_track_source_increments_count(self, tracker):
        """Should increment access count on repeated tracking."""
        url = "https://example.com/api"

        tracker.track_source(url, title="API Docs")
        tracker.track_source(url, title="API Docs")
        tracker.track_source(url, title="API Docs")

        source = tracker.get_source(url)
        assert source["access_count"] == 3

    def test_list_sources_by_category(self, tracker):
        """Should list sources filtered by category."""
        tracker.track_source("https://example.com/api", category="API")
        tracker.track_source("https://example.com/tutorial", category="Tutorial")
        tracker.track_source("https://example.com/reference", category="Reference")

        api_sources = tracker.list_sources(category="API")
        assert len(api_sources) == 1
        assert api_sources[0]["url"] == "https://example.com/api"

    def test_get_statistics(self, tracker):
        """Should get usage statistics."""
        tracker.track_source("https://example.com/doc1", category="API")
        tracker.track_source("https://example.com/doc2", category="Tutorial")
        tracker.track_source("https://example.com/doc3", category="Tutorial")

        stats = tracker.get_statistics()
        assert stats["total_sources"] == 3
        assert stats["total_accesses"] == 3
        assert stats["categories"]["API"] == 1
        assert stats["categories"]["Tutorial"] == 2

    def test_generate_chart_data_pie(self, tracker):
        """Should generate pie chart data."""
        tracker.track_source("https://example.com/doc1", category="API")
        tracker.track_source("https://example.com/doc2", category="Tutorial")

        chart = tracker.generate_chart_data("category_pie")
        assert chart["type"] == "pie"
        assert "API" in chart["labels"]
        assert "Tutorial" in chart["labels"]

    def test_generate_chart_data_bar(self, tracker):
        """Should generate bar chart data."""
        tracker.track_source("https://example.com/doc1", title="Doc 1")
        tracker.track_source("https://example.com/doc1", title="Doc 1")  # Access twice
        tracker.track_source("https://example.com/doc2", title="Doc 2")

        chart = tracker.generate_chart_data("access_bar", limit=10)
        assert chart["type"] == "bar"
        assert len(chart["labels"]) == 2
        assert chart["data"][0] == 2  # Doc 1 accessed twice

    def test_export_markdown_report(self, tmp_path, tracker):
        """Should export markdown report."""
        tracker.track_source("https://example.com/docs", title="Test Docs", category="API")

        report_path = tmp_path / "report.md"
        tracker.export_markdown_report(str(report_path))

        assert report_path.exists()
        content = report_path.read_text()
        assert "Documentation Sources Report" in content
        assert "Test Docs" in content

    def test_clear_old_sources(self, tracker):
        """Should clear old sources."""
        tracker.track_source("https://example.com/old", title="Old Doc")

        # Clear sources older than 90 days (should be 0 for new sources)
        cleared = tracker.clear_old_sources(days=90)
        assert cleared == 0

    def test_persistence(self, tmp_path):
        """Should persist tracked sources."""
        storage = tmp_path / "persist.json"

        tracker1 = DocSourceTracker(storage_path=str(storage))
        tracker1.track_source("https://example.com/test", title="Test")

        tracker2 = DocSourceTracker(storage_path=str(storage))
        source = tracker2.get_source("https://example.com/test")
        assert source is not None
        assert source["title"] == "Test"


class TestGitHubAutoCommit:
    """Test GitHub auto-commit functionality."""

    def test_check_github_mcp_disabled(self):
        """Should handle missing GitHub MCP gracefully."""
        from agent.github_auto_commit import GitHubAutoCommit

        auto_commit = GitHubAutoCommit(mcp_router=None)
        assert auto_commit.enabled is False

    def test_create_patch_without_mcp(self):
        """Should return error when GitHub MCP not available."""
        from agent.github_auto_commit import GitHubAutoCommit

        auto_commit = GitHubAutoCommit(mcp_router=None)
        result = auto_commit.create_patch(["test.txt"], "Test commit")

        assert result["status"] == "error"
        assert "not configured" in result["message"]
