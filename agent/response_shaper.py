"""Utilities for tweaking LLM responses based on persona and tone."""

from __future__ import annotations

import re


class ResponseShaper:
    """Apply simple stylistic transformations to model output."""

    _INFORMAL = {
        r"\bI am\b": "I'm",
        r"\byou are\b": "you're",
        r"\bdo not\b": "don't",
        r"\bdoes not\b": "doesn't",
        r"\bcan not\b": "can't",
        r"\bcannot\b": "can't",
        r"\bwill not\b": "won't",
        r"\bare not\b": "aren't",
        r"\bis not\b": "isn't",
        r"\bit is\b": "it's",
    }

    _FORMAL = {
        r"\bI'm\b": "I am",
        r"\byou're\b": "you are",
        r"\bdon't\b": "do not",
        r"\bdoesn't\b": "does not",
        r"\bcan't\b": "cannot",
        r"\bwon't\b": "will not",
        r"\baren't\b": "are not",
        r"\bisn't\b": "is not",
        r"\bit's\b": "it is",
    }

    _PERSONA_PREFIX = {
        "partner": "Hey there,",
    }

    def __init__(self, max_length: int | None = None) -> None:
        self.max_length = max_length

    def _apply_map(self, text: str, mapping: dict[str, str]) -> str:
        for pat, repl in mapping.items():
            text = re.sub(pat, repl, text, flags=re.IGNORECASE)
        return text

    def shape(self, text: str, persona: str | None = None, tone: str | None = None) -> str:
        """Return the text adjusted for persona and tone."""
        shaped = text

        if tone == "informal":
            shaped = self._apply_map(shaped, self._INFORMAL)
        elif tone == "formal":
            shaped = self._apply_map(shaped, self._FORMAL)

        prefix = self._PERSONA_PREFIX.get(persona or "", "")
        if prefix:
            shaped = f"{prefix} {shaped}".strip()

        if self.max_length is not None and len(shaped) > self.max_length:
            shaped = shaped[: self.max_length].rstrip()

        return shaped
