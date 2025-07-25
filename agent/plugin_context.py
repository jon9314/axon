from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from agent.goal_tracker import GoalTracker
from axon.config.settings import settings
from memory.memory_handler import MemoryHandler


@dataclass
class PluginContext:
    """Lightweight helper exposing memory and goal APIs to plugins."""

    memory_handler: MemoryHandler
    goal_tracker: GoalTracker
    thread_id: str = "plugin_thread"
    identity: str = "plugin_user"

    def add_fact(
        self,
        key: str,
        value: str,
        identity: Optional[str] = None,
        domain: Optional[str] = None,
        tags: Iterable[str] | None = None,
    ) -> None:
        """Store a fact in Axon's memory."""
        self.memory_handler.add_fact(
            thread_id=self.thread_id,
            key=key,
            value=value,
            identity=identity or self.identity,
            domain=domain,
            tags=tags,
        )

    def add_goal(
        self,
        text: str,
        identity: Optional[str] = None,
        priority: int = 0,
        deadline: str | None = None,
    ) -> None:
        """Record a goal via the GoalTracker."""
        dl = datetime.fromisoformat(deadline) if deadline else None
        self.goal_tracker.add_goal(
            thread_id=self.thread_id,
            text=text,
            identity=identity or self.identity,
            priority=priority,
            deadline=dl,
        )


# Default context used by plugins
context = PluginContext(
    memory_handler=MemoryHandler(),
    goal_tracker=GoalTracker(db_uri=settings.database.postgres_uri),
)
