from dataclasses import dataclass
import json

@dataclass
class FallbackPrompt:
    """Metadata for a prompt intended for a remote LLM"""
    model: str
    prompt: str
    reason: str

def generate_prompt(user_message: str, model: str = "gpt-4o", reason: str | None = None) -> dict:
    """Return a dict describing a cloud prompt."""
    if reason is None:
        reason = "Local model may be insufficient for this request."
    prompt = (
        "You are Axon's remote assistant. "
        f"Please answer the following user request:\n{user_message}"
    )
    return {"type": "cloud_prompt", "model": model, "prompt": prompt, "reason": reason}


def to_json(data: dict) -> str:
    """Serialize fallback prompt dict to JSON string."""
    return json.dumps(data)
