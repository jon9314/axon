"""Auto-commit patches via GitHub tooling.

This module provides automated git operations for committing patches
and changes using the GitHub MCP server.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class GitHubAutoCommit:
    """Automate git commits via GitHub MCP server."""

    def __init__(self, mcp_router: Any | None = None, repo_path: str = ".") -> None:
        """Initialize GitHub auto-commit.

        Args:
            mcp_router: MCP router for GitHub operations
            repo_path: Path to git repository
        """
        self.mcp_router = mcp_router
        self.repo_path = Path(repo_path)
        self.enabled = self._check_github_mcp()

    def _check_github_mcp(self) -> bool:
        """Check if GitHub MCP is available."""
        if not self.mcp_router:
            return False

        try:
            return self.mcp_router.check_tool("github")
        except Exception:
            return False

    def create_patch(
        self, files: list[str], message: str, branch: str | None = None
    ) -> dict:
        """Create a git patch with specified files.

        Args:
            files: List of file paths to include
            message: Commit message
            branch: Optional branch name (creates if doesn't exist)

        Returns:
            Dictionary with commit info
        """
        if not self.enabled:
            logger.warning("GitHub MCP not available")
            return {"status": "error", "message": "GitHub MCP not configured"}

        try:
            # If branch specified, create/checkout branch
            if branch:
                try:
                    self.mcp_router.call(
                        "github", {"command": "branch", "name": branch, "create": True}
                    )
                except Exception as e:
                    logger.warning(f"Branch creation skipped: {e}")

            # Stage files
            for file_path in files:
                try:
                    self.mcp_router.call("github", {"command": "add", "file": file_path})
                except Exception as e:
                    logger.error(f"Failed to stage {file_path}: {e}")

            # Create commit
            result = self.mcp_router.call("github", {"command": "commit", "message": message})

            logger.info("auto-commit-created", extra={"files": len(files), "message": message})

            return {
                "status": "success",
                "commit": result,
                "files_committed": len(files),
                "message": message,
            }

        except Exception as e:
            logger.error("auto-commit-failed", extra={"error": str(e)})
            return {"status": "error", "message": str(e)}

    def create_patch_from_diff(self, message: str, auto_stage: bool = True) -> dict:
        """Create commit from current diff.

        Args:
            message: Commit message
            auto_stage: Automatically stage all changes

        Returns:
            Dictionary with commit info
        """
        if not self.enabled:
            return {"status": "error", "message": "GitHub MCP not configured"}

        try:
            # Get current diff
            diff_result = self.mcp_router.call("github", {"command": "diff"})

            if not diff_result or not diff_result.get("changes"):
                return {"status": "no_changes", "message": "No changes to commit"}

            # Auto-stage if requested
            if auto_stage:
                self.mcp_router.call("github", {"command": "add", "file": "."})

            # Create commit
            result = self.mcp_router.call("github", {"command": "commit", "message": message})

            return {
                "status": "success",
                "commit": result,
                "message": message,
                "changes": diff_result.get("changes", 0),
            }

        except Exception as e:
            logger.error("patch-from-diff-failed", extra={"error": str(e)})
            return {"status": "error", "message": str(e)}

    def auto_commit_memory_changes(
        self, memory_file: str = "data/memory_store.json", frequency: str = "daily"
    ) -> dict:
        """Automatically commit memory store changes.

        Args:
            memory_file: Path to memory file
            frequency: Commit frequency (hourly, daily, weekly)

        Returns:
            Dictionary with commit status
        """
        if not self.enabled:
            return {"status": "disabled"}

        try:
            # Check if file has changes
            status_result = self.mcp_router.call("github", {"command": "status"})

            if memory_file not in str(status_result):
                return {"status": "no_changes", "file": memory_file}

            # Generate timestamped message
            from datetime import datetime

            timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
            message = f"chore: auto-commit memory changes ({frequency}) - {timestamp}"

            # Create commit
            return self.create_patch([memory_file], message)

        except Exception as e:
            logger.error("auto-commit-memory-failed", extra={"error": str(e)})
            return {"status": "error", "message": str(e)}

    def create_feature_branch_with_changes(
        self, branch_name: str, files: list[str], message: str, push: bool = False
    ) -> dict:
        """Create feature branch and commit changes.

        Args:
            branch_name: Name of feature branch
            files: Files to commit
            message: Commit message
            push: Whether to push to remote

        Returns:
            Dictionary with operation status
        """
        if not self.enabled:
            return {"status": "error", "message": "GitHub MCP not configured"}

        try:
            # Create branch
            self.mcp_router.call("github", {"command": "branch", "name": branch_name, "create": True})

            # Commit changes
            commit_result = self.create_patch(files, message, branch=branch_name)

            if commit_result["status"] != "success":
                return commit_result

            # Push if requested
            if push:
                try:
                    push_result = self.mcp_router.call(
                        "github", {"command": "push", "branch": branch_name}
                    )
                    commit_result["pushed"] = True
                    commit_result["push_result"] = push_result
                except Exception as e:
                    commit_result["push_error"] = str(e)
                    commit_result["pushed"] = False

            commit_result["branch"] = branch_name
            return commit_result

        except Exception as e:
            logger.error("feature-branch-failed", extra={"error": str(e)})
            return {"status": "error", "message": str(e)}

    def get_commit_history(self, limit: int = 10) -> list[dict]:
        """Get recent commit history.

        Args:
            limit: Number of commits to retrieve

        Returns:
            List of commit dictionaries
        """
        if not self.enabled:
            return []

        try:
            result = self.mcp_router.call("github", {"command": "log", "limit": limit})

            if isinstance(result, dict) and "commits" in result:
                return result["commits"]

            return []

        except Exception as e:
            logger.error("get-history-failed", extra={"error": str(e)})
            return []

    def rollback_last_commit(self, soft: bool = True) -> dict:
        """Rollback the last commit.

        Args:
            soft: If True, keep changes in working directory

        Returns:
            Dictionary with rollback status
        """
        if not self.enabled:
            return {"status": "error", "message": "GitHub MCP not configured"}

        try:
            mode = "soft" if soft else "hard"
            result = self.mcp_router.call("github", {"command": "reset", "mode": mode, "count": 1})

            logger.info("rollback-commit", extra={"mode": mode})

            return {"status": "success", "mode": mode, "result": result}

        except Exception as e:
            logger.error("rollback-failed", extra={"error": str(e)})
            return {"status": "error", "message": str(e)}
