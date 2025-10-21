"""Track documentation sources and generate visualization charts.

This module captures URLs from documentation MCP servers and provides
charting capabilities for data visualization.
"""

from __future__ import annotations

import json
import logging
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class DocSourceTracker:
    """Track documentation source URLs and usage statistics."""

    def __init__(self, storage_path: str = "data/doc_sources.json") -> None:
        """Initialize documentation source tracker.

        Args:
            storage_path: Path to JSON file for storing tracked sources
        """
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.sources: dict[str, dict] = self._load_sources()

    def _load_sources(self) -> dict[str, dict]:
        """Load tracked sources from storage."""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error("load-sources-failed", extra={"error": str(e)})
                return {}
        return {}

    def _save_sources(self) -> None:
        """Save tracked sources to storage."""
        try:
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(self.sources, f, indent=2)
        except Exception as e:
            logger.error("save-sources-failed", extra={"error": str(e)})

    def track_source(
        self,
        url: str,
        title: str | None = None,
        category: str | None = None,
        metadata: dict | None = None,
    ) -> None:
        """Track a documentation source URL.

        Args:
            url: Source URL
            title: Document title
            category: Category (e.g., "API", "Tutorial", "Reference")
            metadata: Additional metadata
        """
        if url not in self.sources:
            self.sources[url] = {
                "url": url,
                "title": title or url,
                "category": category or "Uncategorized",
                "first_accessed": datetime.utcnow().isoformat(),
                "access_count": 0,
                "metadata": metadata or {},
            }

        # Update access count and timestamp
        self.sources[url]["access_count"] += 1
        self.sources[url]["last_accessed"] = datetime.utcnow().isoformat()

        if title:
            self.sources[url]["title"] = title
        if category:
            self.sources[url]["category"] = category
        if metadata:
            self.sources[url]["metadata"].update(metadata)

        self._save_sources()
        logger.info("source-tracked", extra={"url": url, "category": category})

    def get_source(self, url: str) -> dict | None:
        """Get information about a tracked source.

        Args:
            url: Source URL

        Returns:
            Source information dictionary or None
        """
        return self.sources.get(url)

    def list_sources(
        self, category: str | None = None, sort_by: str = "access_count"
    ) -> list[dict]:
        """List tracked sources.

        Args:
            category: Filter by category
            sort_by: Sort field (access_count, first_accessed, last_accessed)

        Returns:
            List of source dictionaries
        """
        sources = list(self.sources.values())

        if category:
            sources = [s for s in sources if s.get("category") == category]

        # Sort
        reverse = sort_by == "access_count"  # Most accessed first
        sources.sort(key=lambda x: x.get(sort_by, 0), reverse=reverse)

        return sources

    def get_statistics(self) -> dict:
        """Get usage statistics.

        Returns:
            Dictionary with statistics
        """
        if not self.sources:
            return {
                "total_sources": 0,
                "total_accesses": 0,
                "categories": {},
                "most_accessed": None,
            }

        total_accesses = sum(s["access_count"] for s in self.sources.values())

        # Count by category
        categories: dict[str, int] = defaultdict(int)
        for source in self.sources.values():
            categories[source.get("category", "Uncategorized")] += 1

        # Find most accessed
        most_accessed = max(self.sources.values(), key=lambda x: x["access_count"])

        return {
            "total_sources": len(self.sources),
            "total_accesses": total_accesses,
            "categories": dict(categories),
            "most_accessed": {
                "url": most_accessed["url"],
                "title": most_accessed["title"],
                "count": most_accessed["access_count"],
            },
        }

    def generate_chart_data(
        self, chart_type: str = "category_pie", limit: int = 10
    ) -> dict[str, Any]:
        """Generate data for chart visualization.

        Args:
            chart_type: Type of chart (category_pie, access_bar, timeline)
            limit: Maximum data points for bar/timeline charts

        Returns:
            Dictionary with chart configuration and data
        """
        if chart_type == "category_pie":
            # Pie chart of sources by category
            categories: dict[str, int] = defaultdict(int)
            for source in self.sources.values():
                categories[source.get("category", "Uncategorized")] += 1

            return {
                "type": "pie",
                "title": "Documentation Sources by Category",
                "labels": list(categories.keys()),
                "data": list(categories.values()),
            }

        elif chart_type == "access_bar":
            # Bar chart of most accessed sources
            sources = sorted(
                self.sources.values(), key=lambda x: x["access_count"], reverse=True
            )[:limit]

            return {
                "type": "bar",
                "title": f"Top {limit} Most Accessed Sources",
                "labels": [s["title"] for s in sources],
                "data": [s["access_count"] for s in sources],
            }

        elif chart_type == "timeline":
            # Timeline of source access
            sources = sorted(self.sources.values(), key=lambda x: x["first_accessed"])[:limit]

            return {
                "type": "timeline",
                "title": "Source Access Timeline",
                "data": [
                    {
                        "title": s["title"],
                        "first_accessed": s["first_accessed"],
                        "last_accessed": s.get("last_accessed", s["first_accessed"]),
                        "count": s["access_count"],
                    }
                    for s in sources
                ],
            }

        return {"type": "unknown", "error": "Unknown chart type"}

    def export_markdown_report(self, output_path: str = "data/doc_sources_report.md") -> None:
        """Export tracked sources as a markdown report.

        Args:
            output_path: Path for markdown report
        """
        stats = self.get_statistics()
        sources_by_category: dict[str, list] = defaultdict(list)

        for source in self.sources.values():
            category = source.get("category", "Uncategorized")
            sources_by_category[category].append(source)

        # Generate markdown
        report = ["# Documentation Sources Report\n"]
        report.append(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}\n\n")

        # Statistics
        report.append("## Statistics\n")
        report.append(f"- **Total Sources**: {stats['total_sources']}\n")
        report.append(f"- **Total Accesses**: {stats['total_accesses']}\n")
        report.append(f"- **Categories**: {len(stats['categories'])}\n\n")

        if stats["most_accessed"]:
            report.append("### Most Accessed\n")
            ma = stats["most_accessed"]
            report.append(f"- **Title**: {ma['title']}\n")
            report.append(f"- **URL**: {ma['url']}\n")
            report.append(f"- **Access Count**: {ma['count']}\n\n")

        # Sources by category
        report.append("## Sources by Category\n\n")

        for category in sorted(sources_by_category.keys()):
            sources = sources_by_category[category]
            report.append(f"### {category} ({len(sources)} sources)\n\n")

            for source in sorted(sources, key=lambda x: x["access_count"], reverse=True):
                report.append(f"#### {source['title']}\n\n")
                report.append(f"- **URL**: [{source['url']}]({source['url']})\n")
                report.append(f"- **Access Count**: {source['access_count']}\n")
                report.append(f"- **First Accessed**: {source['first_accessed']}\n")

                if "last_accessed" in source:
                    report.append(f"- **Last Accessed**: {source['last_accessed']}\n")

                if source.get("metadata"):
                    report.append(f"- **Metadata**: {source['metadata']}\n")

                report.append("\n")

        # Write report
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text("".join(report), encoding="utf-8")

        logger.info("markdown-report-exported", extra={"path": output_path})

    def clear_old_sources(self, days: int = 90) -> int:
        """Clear sources not accessed in specified days.

        Args:
            days: Number of days of inactivity before clearing

        Returns:
            Number of sources cleared
        """
        from datetime import timedelta

        cutoff = datetime.utcnow() - timedelta(days=days)
        cutoff_str = cutoff.isoformat()

        cleared = 0
        sources_to_remove = []

        for url, source in self.sources.items():
            last_accessed = source.get("last_accessed", source["first_accessed"])
            if last_accessed < cutoff_str:
                sources_to_remove.append(url)

        for url in sources_to_remove:
            del self.sources[url]
            cleared += 1

        if cleared > 0:
            self._save_sources()
            logger.info("sources-cleared", extra={"count": cleared, "days": days})

        return cleared
