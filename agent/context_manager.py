# axon/agent/context_manager.py

from memory.memory_handler import MemoryHandler
from config.settings import settings

class ContextManager:
    """
    Manages the current conversational context, including thread_id and identity.
    """
    def __init__(self, thread_id: str = "default_thread", identity: str = "default_user"):
        self.thread_id = thread_id
        self.identity = identity
        # Initialize the memory handler here, assuming it's needed per context
        self.memory_handler = MemoryHandler(db_uri=settings.database.postgres_uri)

    def add_fact(self, key: str, value: str):
        """
        Adds a fact to memory within the current context.
        """
        self.memory_handler.add_fact(
            thread_id=self.thread_id,
            key=key,
            value=value,
            identity=self.identity
        )

    def get_fact(self, key: str):
        """
        Retrieves a fact from memory within the current context.
        """
        return self.memory_handler.get_fact(thread_id=self.thread_id, key=key)

    def set_identity(self, identity: str):
        """
        Sets a new identity for the current context.
        """
        print(f"Context identity switched to: {identity}")
        self.identity = identity