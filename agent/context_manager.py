# axon/agent/context_manager.py

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Optional

from agent.goal_tracker import GoalTracker
from axon.config.settings import settings
from memory.memory_handler import MemoryHandler


@dataclass
class ChatMessage:
    identity: str
    text: str


class ContextManager:
    """Manages the current conversational context, including thread and identity."""

    def __init__(
        self,
        thread_id: str = "default_thread",
        identity: str = "default_user",
        goal_tracker: Optional[GoalTracker] = None,
    ) -> None:
        self.thread_id = thread_id
        self.identity = identity
        self.memory_handler = MemoryHandler()
        self.goal_tracker = goal_tracker or GoalTracker(db_uri=settings.database.postgres_uri)
        self.chat_history: list[ChatMessage] = []

    def add_fact(
        self,
        key: str,
        value: str,
        identity: Optional[str] = None,
        domain: Optional[str] = None,
        tags: Iterable[str] | None = None,
    ) -> None:
        """
        Adds a fact to memory within the current context.
        """
        self.memory_handler.add_fact(
            thread_id=self.thread_id,
            key=key,
            value=value,
            identity=identity or self.identity,
            domain=domain,
            tags=tags,
        )

    def get_fact(self, key: str, include_identity: bool = False):
        """
        Retrieves a fact from memory within the current context.
        """
        return self.memory_handler.get_fact(
            thread_id=self.thread_id, key=key, include_identity=include_identity
        )

    def set_identity(self, identity: str):
        """
        Sets a new identity for the current context.
        """
        print(f"Context identity switched to: {identity}")
        self.identity = identity

    def set_thread(self, thread_id: str):
        """Switches the context to a different thread."""
        print(f"Context thread switched to: {thread_id}")
        self.thread_id = thread_id

    def update_fact(
        self,
        key: str,
        value: str,
        domain: Optional[str] = None,
        tags: Iterable[str] | None = None,
    ) -> None:
        self.memory_handler.update_fact(
            thread_id=self.thread_id,
            key=key,
            value=value,
            identity=self.identity,
            domain=domain,
            tags=tags,
        )

    def delete_fact(self, key: str) -> bool:
        return self.memory_handler.delete_fact(self.thread_id, key)

    def set_lock(self, key: str, locked: bool) -> bool:
        return self.memory_handler.set_lock(self.thread_id, key, locked)

    def add_chat_message(self, text: str, identity: Optional[str] = None) -> None:
        """Record a chat message with its speaker identity and detect goals."""
        speaker = identity or self.identity
        self.chat_history.append(ChatMessage(identity=speaker, text=text))
        if self.goal_tracker:
            self.goal_tracker.detect_and_add_goal(self.thread_id, text, identity=speaker)
