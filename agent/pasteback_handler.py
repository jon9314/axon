import time
from memory.memory_handler import MemoryHandler

class PastebackHandler:
    """Store remote model responses in memory."""

    def __init__(self, memory_handler: MemoryHandler):
        self.memory_handler = memory_handler

    def store(self, thread_id: str, prompt: str, response: str, model: str = "gpt") -> None:
        ts = int(time.time())
        self.memory_handler.add_fact(thread_id, f"cloud_prompt_{ts}", prompt, identity=model)
        self.memory_handler.add_fact(thread_id, f"cloud_response_{ts}", response, identity=model)
