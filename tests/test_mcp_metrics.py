"""Tests for MCP metrics tracking."""

import pytest

from agent.mcp_metrics import MCPMetrics


class TestMCPMetrics:
    """Test MCP metrics tracking functionality."""

    @pytest.fixture
    def metrics(self, tmp_path):
        """Create MCPMetrics instance with temporary storage."""
        storage = tmp_path / "test_metrics.json"
        return MCPMetrics(storage_path=str(storage), history_size=100, retention_days=7)

    def test_record_successful_call(self, metrics):
        """Should record successful MCP call."""
        metrics.record_call("test_server", latency_ms=50.5, success=True)

        stats = metrics.get_server_stats("test_server")
        assert stats["total_calls"] == 1
        assert stats["successful_calls"] == 1
        assert stats["failed_calls"] == 0
        assert stats["success_rate"] == 100.0
        assert stats["avg_latency_ms"] == 50.5
        assert stats["health"] == "healthy"

    def test_record_failed_call(self, metrics):
        """Should record failed MCP call."""
        metrics.record_call("test_server", latency_ms=100.0, success=False, error="Timeout")

        stats = metrics.get_server_stats("test_server")
        assert stats["total_calls"] == 1
        assert stats["successful_calls"] == 0
        assert stats["failed_calls"] == 1
        assert stats["success_rate"] == 0.0
        assert stats["consecutive_failures"] == 1
        assert stats["health"] == "degraded"

    def test_consecutive_failures_affects_health(self, metrics):
        """Consecutive failures should degrade health status."""
        # Record multiple failures
        for _i in range(5):
            metrics.record_call("test_server", latency_ms=100.0, success=False)

        stats = metrics.get_server_stats("test_server")
        assert stats["consecutive_failures"] == 5
        assert stats["health"] == "critical"

    def test_success_rate_calculation(self, metrics):
        """Should calculate success rate correctly."""
        # 7 successes, 3 failures = 70%
        for _i in range(7):
            metrics.record_call("test_server", latency_ms=50.0, success=True)
        for _i in range(3):
            metrics.record_call("test_server", latency_ms=100.0, success=False)

        stats = metrics.get_server_stats("test_server")
        assert stats["total_calls"] == 10
        assert stats["success_rate"] == 70.0

    def test_latency_statistics(self, metrics):
        """Should track min, max, and average latency."""
        latencies = [10.0, 50.0, 100.0, 25.0, 75.0]

        for lat in latencies:
            metrics.record_call("test_server", latency_ms=lat, success=True)

        stats = metrics.get_server_stats("test_server")
        assert stats["min_latency_ms"] == 10.0
        assert stats["max_latency_ms"] == 100.0
        assert stats["avg_latency_ms"] == 52.0  # Average of all values

    def test_get_latency_percentiles(self, metrics):
        """Should calculate latency percentiles."""
        # Record calls with known latencies
        for lat in range(1, 101):  # 1ms to 100ms
            metrics.record_call("test_server", latency_ms=float(lat), success=True)

        percentiles = metrics.get_latency_percentiles("test_server", [50, 90, 95, 99])

        assert percentiles["p50"] >= 45 and percentiles["p50"] <= 55
        assert percentiles["p90"] >= 85 and percentiles["p90"] <= 95
        assert percentiles["p99"] >= 95

    def test_get_all_servers_stats(self, metrics):
        """Should get stats for all tracked servers."""
        metrics.record_call("server1", latency_ms=50.0, success=True)
        metrics.record_call("server2", latency_ms=100.0, success=True)
        metrics.record_call("server3", latency_ms=75.0, success=False)

        all_stats = metrics.get_all_servers_stats()
        assert len(all_stats) == 3

        server_names = [s["server"] for s in all_stats]
        assert "server1" in server_names
        assert "server2" in server_names
        assert "server3" in server_names

    def test_health_summary(self, metrics):
        """Should generate health summary."""
        # Healthy server
        for _i in range(10):
            metrics.record_call("healthy_server", latency_ms=50.0, success=True)

        # Degraded server
        for _i in range(8):
            metrics.record_call("degraded_server", latency_ms=100.0, success=True)
        for _i in range(2):
            metrics.record_call("degraded_server", latency_ms=100.0, success=False)

        # Critical server
        for _i in range(5):
            metrics.record_call("critical_server", latency_ms=200.0, success=False)

        summary = metrics.get_health_summary()
        assert summary["total_servers"] == 3
        assert summary["healthy"] == 1
        assert summary["degraded"] >= 1
        assert summary["critical"] == 1

    def test_failure_analysis(self, metrics):
        """Should analyze failures by error type."""
        metrics.record_call("test_server", latency_ms=100.0, success=False, error="Timeout")
        metrics.record_call("test_server", latency_ms=100.0, success=False, error="Timeout")
        metrics.record_call("test_server", latency_ms=100.0, success=False, error="ConnectionError")

        analysis = metrics.get_failure_analysis("test_server")
        assert analysis["total_failures"] == 3
        assert analysis["error_types"]["Timeout"] == 2
        assert analysis["error_types"]["ConnectionError"] == 1

    def test_no_data_server_stats(self, metrics):
        """Should handle server with no data."""
        stats = metrics.get_server_stats("nonexistent_server")
        assert stats["total_calls"] == 0
        assert stats["status"] == "no_data"

    def test_persistence(self, tmp_path):
        """Should persist metrics to storage."""
        storage = tmp_path / "persist_test.json"

        # Create metrics and record calls
        metrics1 = MCPMetrics(storage_path=str(storage))
        metrics1.record_call("test_server", latency_ms=50.0, success=True)
        metrics1._save_metrics()

        # Load into new instance
        metrics2 = MCPMetrics(storage_path=str(storage))
        stats = metrics2.get_server_stats("test_server")
        assert stats["total_calls"] == 1

    def test_history_size_limit(self, tmp_path):
        """Should respect history size limit."""
        metrics = MCPMetrics(storage_path=str(tmp_path / "test.json"), history_size=10)

        # Record more calls than history limit
        for i in range(20):
            metrics.record_call("test_server", latency_ms=float(i), success=True)

        # History should be limited to 10
        history = metrics.call_history["test_server"]
        assert len(history) == 10

    def test_export_metrics_report(self, tmp_path):
        """Should export metrics as markdown report."""
        metrics = MCPMetrics(storage_path=str(tmp_path / "metrics.json"))

        metrics.record_call("server1", latency_ms=50.0, success=True)
        metrics.record_call("server2", latency_ms=100.0, success=False, error="Timeout")

        report_path = tmp_path / "report.md"
        metrics.export_metrics_report(str(report_path))

        assert report_path.exists()
        content = report_path.read_text()
        assert "MCP Server Metrics Report" in content
        assert "server1" in content
        assert "server2" in content
