from dataclasses import dataclass
import json
from typing import Tuple


@dataclass
class FallbackPrompt:
    """Metadata for a prompt intended for a remote LLM."""

    model: str
    prompt: str
    reason: str


def suggest_model(user_message: str) -> Tuple[str, str]:
    """Suggest a cloud model and reason based on the message."""

    lowered = user_message.lower()
    if "summarize" in lowered or "summary" in lowered:
        return (
            "claude-3-sonnet",
            "Claude is recommended for summarization tasks.",
        )
    return (
        "gpt-4o",
        "Local model may be insufficient for this request.",
    )


def generate_prompt(
    user_message: str, model: str | None = None, reason: str | None = None
) -> dict:
    """Return a dict describing a cloud prompt."""

    if model is None or reason is None:
        suggested_model, suggested_reason = suggest_model(user_message)
        model = model or suggested_model
        reason = reason or suggested_reason

    prompt = (
        "You are Axon's remote assistant. "
        f"Please answer the following user request:\n{user_message}"
    )
    return {
        "type": "cloud_prompt",
        "model": model,
        "prompt": prompt,
        "reason": reason,
    }


def to_json(data: dict) -> str:
    """Serialize fallback prompt dict to JSON string."""

    return json.dumps(data)
