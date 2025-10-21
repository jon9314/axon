"""Track MCP server latency and failure metrics.

This module provides comprehensive monitoring of MCP server performance,
including latency tracking, failure rates, and health statistics.
"""

from __future__ import annotations

import json
import logging
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class MCPMetrics:
    """Track MCP server performance metrics."""

    def __init__(
        self,
        storage_path: str = "data/mcp_metrics.json",
        history_size: int = 1000,
        retention_days: int = 30,
    ) -> None:
        """Initialize MCP metrics tracker.

        Args:
            storage_path: Path to JSON file for storing metrics
            history_size: Maximum number of recent calls to keep in memory
            retention_days: Days to retain historical data
        """
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.history_size = history_size
        self.retention_days = retention_days

        # In-memory metrics
        self.call_history: dict[str, deque] = defaultdict(lambda: deque(maxlen=history_size))
        self.server_stats: dict[str, dict] = defaultdict(
            lambda: {
                "total_calls": 0,
                "successful_calls": 0,
                "failed_calls": 0,
                "total_latency_ms": 0.0,
                "min_latency_ms": float("inf"),
                "max_latency_ms": 0.0,
                "last_success": None,
                "last_failure": None,
                "consecutive_failures": 0,
            }
        )

        self._load_metrics()

    def _load_metrics(self) -> None:
        """Load metrics from storage."""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, encoding="utf-8") as f:
                    data = json.load(f)
                    self.server_stats = defaultdict(
                        lambda: {
                            "total_calls": 0,
                            "successful_calls": 0,
                            "failed_calls": 0,
                            "total_latency_ms": 0.0,
                            "min_latency_ms": float("inf"),
                            "max_latency_ms": 0.0,
                            "last_success": None,
                            "last_failure": None,
                            "consecutive_failures": 0,
                        },
                        **data.get("server_stats", {}),
                    )
            except Exception as e:
                logger.error("load-metrics-failed", extra={"error": str(e)})

    def _save_metrics(self) -> None:
        """Save metrics to storage."""
        try:
            data = {
                "server_stats": dict(self.server_stats),
                "last_updated": datetime.utcnow().isoformat(),
            }
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error("save-metrics-failed", extra={"error": str(e)})

    def record_call(
        self, server_name: str, latency_ms: float, success: bool, error: str | None = None
    ) -> None:
        """Record an MCP server call.

        Args:
            server_name: Name of the MCP server
            latency_ms: Call latency in milliseconds
            success: Whether the call succeeded
            error: Error message if call failed
        """
        timestamp = datetime.utcnow().isoformat()

        # Update statistics
        stats = self.server_stats[server_name]
        stats["total_calls"] += 1

        if success:
            stats["successful_calls"] += 1
            stats["last_success"] = timestamp
            stats["consecutive_failures"] = 0
        else:
            stats["failed_calls"] += 1
            stats["last_failure"] = timestamp
            stats["consecutive_failures"] += 1

        # Update latency stats
        if latency_ms > 0:
            stats["total_latency_ms"] += latency_ms
            stats["min_latency_ms"] = min(stats["min_latency_ms"], latency_ms)
            stats["max_latency_ms"] = max(stats["max_latency_ms"], latency_ms)

        # Add to call history
        self.call_history[server_name].append(
            {
                "timestamp": timestamp,
                "latency_ms": latency_ms,
                "success": success,
                "error": error,
            }
        )

        # Periodic save
        if stats["total_calls"] % 100 == 0:
            self._save_metrics()

        logger.debug(
            "mcp-call-recorded",
            extra={
                "server": server_name,
                "latency_ms": latency_ms,
                "success": success,
            },
        )

    def get_server_stats(self, server_name: str) -> dict:
        """Get statistics for a specific server.

        Args:
            server_name: Name of the MCP server

        Returns:
            Dictionary with server statistics
        """
        stats = self.server_stats.get(server_name, {})

        if not stats or stats["total_calls"] == 0:
            return {
                "server": server_name,
                "total_calls": 0,
                "status": "no_data",
            }

        # Calculate averages
        avg_latency = 0.0
        if stats["successful_calls"] > 0:
            avg_latency = stats["total_latency_ms"] / stats["successful_calls"]

        success_rate = 0.0
        if stats["total_calls"] > 0:
            success_rate = (stats["successful_calls"] / stats["total_calls"]) * 100

        # Determine health status
        health = "healthy"
        if stats["consecutive_failures"] >= 5:
            health = "critical"
        elif stats["consecutive_failures"] >= 3:
            health = "degraded"
        elif success_rate < 95:
            health = "degraded"

        return {
            "server": server_name,
            "total_calls": stats["total_calls"],
            "successful_calls": stats["successful_calls"],
            "failed_calls": stats["failed_calls"],
            "success_rate": round(success_rate, 2),
            "avg_latency_ms": round(avg_latency, 2),
            "min_latency_ms": stats["min_latency_ms"]
            if stats["min_latency_ms"] != float("inf")
            else 0,
            "max_latency_ms": stats["max_latency_ms"],
            "last_success": stats["last_success"],
            "last_failure": stats["last_failure"],
            "consecutive_failures": stats["consecutive_failures"],
            "health": health,
        }

    def get_all_servers_stats(self) -> list[dict]:
        """Get statistics for all tracked servers.

        Returns:
            List of server statistics dictionaries
        """
        return [self.get_server_stats(server) for server in self.server_stats.keys()]

    def get_latency_percentiles(self, server_name: str, percentiles: list[int] | None = None) -> dict:
        """Calculate latency percentiles for a server.

        Args:
            server_name: Name of the MCP server
            percentiles: List of percentiles to calculate

        Returns:
            Dictionary mapping percentiles to latency values
        """
        if percentiles is None:
            percentiles = [50, 90, 95, 99]

        history: Any = self.call_history.get(server_name, [])
        if not history:
            return {}

        # Get successful call latencies
        latencies = sorted([call["latency_ms"] for call in history if call["success"]])

        if not latencies:
            return {}

        result = {}
        for p in percentiles:
            index = int((p / 100.0) * len(latencies))
            index = min(index, len(latencies) - 1)
            result[f"p{p}"] = round(latencies[index], 2)

        return result

    def get_failure_analysis(self, server_name: str) -> dict:
        """Analyze failures for a server.

        Args:
            server_name: Name of the MCP server

        Returns:
            Dictionary with failure analysis
        """
        history: Any = self.call_history.get(server_name, [])
        if not history:
            return {"server": server_name, "failures": []}

        failures = [call for call in history if not call["success"]]

        # Group by error type
        error_counts: dict[str, int] = defaultdict(int)
        for failure in failures:
            error = failure.get("error", "Unknown error")
            error_counts[error] += 1

        return {
            "server": server_name,
            "total_failures": len(failures),
            "error_types": dict(error_counts),
            "recent_failures": failures[-10:],  # Last 10 failures
        }

    def get_health_summary(self) -> dict:
        """Get overall health summary of all MCP servers.

        Returns:
            Dictionary with health summary
        """
        all_stats = self.get_all_servers_stats()

        if not all_stats:
            return {
                "total_servers": 0,
                "healthy": 0,
                "degraded": 0,
                "critical": 0,
                "servers_by_health": {},
            }

        health_counts = {"healthy": 0, "degraded": 0, "critical": 0}
        servers_by_health: dict[str, list] = {"healthy": [], "degraded": [], "critical": []}

        for stats in all_stats:
            health = stats.get("health", "unknown")
            if health in health_counts:
                health_counts[health] += 1
                servers_by_health[health].append(stats["server"])

        return {
            "total_servers": len(all_stats),
            "healthy": health_counts["healthy"],
            "degraded": health_counts["degraded"],
            "critical": health_counts["critical"],
            "servers_by_health": servers_by_health,
            "timestamp": datetime.utcnow().isoformat(),
        }

    def export_metrics_report(self, output_path: str = "data/mcp_metrics_report.md") -> None:
        """Export metrics as a markdown report.

        Args:
            output_path: Path for markdown report
        """
        health = self.get_health_summary()
        all_stats = self.get_all_servers_stats()

        report = ["# MCP Server Metrics Report\n"]
        report.append(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}\n\n")

        # Health summary
        report.append("## Health Summary\n\n")
        report.append(f"- **Total Servers**: {health['total_servers']}\n")
        report.append(f"- **Healthy**: {health['healthy']} ✅\n")
        report.append(f"- **Degraded**: {health['degraded']} ⚠️\n")
        report.append(f"- **Critical**: {health['critical']} ❌\n\n")

        # Server details
        report.append("## Server Statistics\n\n")

        for stats in sorted(all_stats, key=lambda x: x["server"]):
            health_icon = {"healthy": "✅", "degraded": "⚠️", "critical": "❌"}.get(
                stats["health"], "❓"
            )

            report.append(f"### {stats['server']} {health_icon}\n\n")
            report.append(f"- **Total Calls**: {stats['total_calls']}\n")
            report.append(f"- **Success Rate**: {stats['success_rate']}%\n")
            report.append(f"- **Average Latency**: {stats['avg_latency_ms']} ms\n")
            report.append(f"- **Min Latency**: {stats['min_latency_ms']} ms\n")
            report.append(f"- **Max Latency**: {stats['max_latency_ms']} ms\n")

            # Percentiles
            percentiles = self.get_latency_percentiles(stats["server"])
            if percentiles:
                report.append(f"- **Latency Percentiles**: {percentiles}\n")

            if stats["consecutive_failures"] > 0:
                report.append(
                    f"- **⚠️ Consecutive Failures**: {stats['consecutive_failures']}\n"
                )

            report.append("\n")

        # Write report
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text("".join(report), encoding="utf-8")

        logger.info("metrics-report-exported", extra={"path": output_path})

    def clear_old_metrics(self) -> int:
        """Clear metrics older than retention period.

        Returns:
            Number of records cleared
        """
        cutoff = datetime.utcnow() - timedelta(days=self.retention_days)
        cutoff_str = cutoff.isoformat()

        cleared = 0
        for server_name, history in self.call_history.items():
            original_len = len(history)
            # Remove old entries
            new_history = deque(
                (call for call in history if call["timestamp"] >= cutoff_str),
                maxlen=self.history_size,
            )
            self.call_history[server_name] = new_history
            cleared += original_len - len(new_history)

        if cleared > 0:
            self._save_metrics()
            logger.info("old-metrics-cleared", extra={"count": cleared})

        return cleared


# Decorator for automatic metrics tracking
def track_mcp_call(metrics: MCPMetrics, server_name: str):
    """Decorator to automatically track MCP call metrics.

    Args:
        metrics: MCPMetrics instance
        server_name: Name of the server

    Returns:
        Decorator function
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            error = None
            success = True

            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                error = str(e)
                raise
            finally:
                latency_ms = (time.time() - start_time) * 1000
                metrics.record_call(server_name, latency_ms, success, error)

        return wrapper

    return decorator
