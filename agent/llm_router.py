"""LLM router integrating OpenRouter via Qwen-Agent."""

from __future__ import annotations

import re
from collections.abc import Iterable
from typing import Any

from qwen_agent.agents import Assistant
from qwen_agent.tools import TOOL_REGISTRY

from axon.config.settings import settings

from .fallback_prompt import generate_prompt, to_json
from .response_shaper import ResponseShaper


class LLMRouter:
    """Route prompts through an OpenRouter-backed Qwen-Agent assistant."""

    def __init__(self, model: str | None = None) -> None:
        """Create the assistant using OpenRouter and registered tools."""

        self.model = model or "openrouter/horizon-beta"
        self.assistant: Assistant | None = None

    def _ensure_assistant(self, model: str) -> Assistant:
        """Return an assistant configured for the requested model."""
        if self.assistant is None or model != self.model:
            tool_names = list(TOOL_REGISTRY.keys())
            llm_cfg: dict[str, Any] = {"model": model}
            if settings.llm.model_server:
                llm_cfg.update(
                    {
                        "model_type": "oai",
                        "model_server": settings.llm.model_server,
                    }
                )
            else:
                llm_cfg["model_type"] = "transformers"
            self.assistant = Assistant(
                function_list=tool_names,
                llm=llm_cfg,
                generate_cfg=settings.llm.qwen_agent_generate_cfg,
            )
            self.model = model
        return self.assistant

    def _needs_cloud(self, prompt: str) -> bool:
        """Heuristic to decide if a cloud model should be suggested."""
        lowered = prompt.lower()
        if any(k in lowered for k in ("summarize", "summary", "analyze", "analysis")):
            return True
        return len(prompt) > 400

    def _extract_text(self, response: Iterable[dict[str, Any]] | Iterable[Any]) -> str:
        """Return the last assistant message text."""
        messages = list(response)
        if not messages:
            return ""
        last = messages[-1]
        if isinstance(last, dict):
            return (last.get("content") or "").strip()
        return (getattr(last, "content", "") or "").strip()

    def calculate_confidence(self, response: str, prompt: str) -> float:
        """Calculate confidence score based on response quality indicators.

        Args:
            response: The LLM's response text
            prompt: The original user prompt

        Returns:
            Confidence score between 0.0 and 1.0
        """
        if not response or not response.strip():
            return 0.0

        confidence = 0.5  # Base confidence

        # Increase confidence for detailed responses
        if len(response) > 100:
            confidence += 0.1
        if len(response) > 300:
            confidence += 0.1

        # Decrease for vague/uncertain language
        uncertain_phrases = [
            "i'm not sure",
            "i don't know",
            "maybe",
            "perhaps",
            "i think",
            "possibly",
            "might be",
        ]
        lower_response = response.lower()
        uncertainty_count = sum(1 for phrase in uncertain_phrases if phrase in lower_response)
        confidence -= uncertainty_count * 0.1

        # Increase for structured content (lists, code, etc.)
        if re.search(r"(\n-|\n\d+\.|\n\*|```)", response):
            confidence += 0.15

        # Decrease for error messages or fallback indicators
        if "sorry" in lower_response or "error" in lower_response:
            confidence -= 0.2

        # Increase if response appears to directly address the prompt
        # Simple heuristic: check if key words from prompt appear in response
        prompt_words = set(re.findall(r"\w{4,}", prompt.lower()))
        response_words = set(re.findall(r"\w{4,}", lower_response))
        overlap_ratio = len(prompt_words & response_words) / max(len(prompt_words), 1)
        confidence += overlap_ratio * 0.2

        # Clamp to valid range
        return max(0.0, min(1.0, confidence))

    def get_response(
        self,
        prompt: str,
        model: str,
        persona: str | None = None,
        tone: str | None = None,
        history: list[dict[str, str]] | None = None,
    ) -> str:
        """Return the assistant reply or fallback suggestion."""
        if self._needs_cloud(prompt):
            fallback = generate_prompt(prompt)
            return to_json(fallback)

        messages: list[dict[str, str]] = history[:] if history else []
        if persona or tone:
            styles = []
            if persona:
                styles.append(f"persona:{persona}")
            if tone:
                styles.append(f"tone:{tone}")
            messages.append({"role": "system", "content": f"[{','.join(styles)}]"})
        messages.append({"role": "user", "content": prompt})

        try:
            assistant = self._ensure_assistant(model)
            output = assistant.run_nonstream(messages)
            text = self._extract_text(output)
            if text:
                shaper = ResponseShaper()
                return shaper.shape(text, persona=persona, tone=tone)
            return "Sorry, I received an empty response from Qwen3.".strip()
        except Exception:
            fallback = generate_prompt(
                prompt,
                reason="Local model call failed; please use a cloud model.",
            )
            return to_json(fallback)

    def get_response_with_confidence(
        self,
        prompt: str,
        model: str,
        persona: str | None = None,
        tone: str | None = None,
        history: list[dict[str, str]] | None = None,
    ) -> tuple[str, float]:
        """Return the assistant reply and confidence score.

        Args:
            prompt: User's input prompt
            model: Model identifier to use
            persona: Optional persona setting
            tone: Optional tone setting
            history: Optional conversation history

        Returns:
            Tuple of (response_text, confidence_score)
        """
        response = self.get_response(prompt, model, persona, tone, history)
        confidence = self.calculate_confidence(response, prompt)
        return response, confidence
