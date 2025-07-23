"""LLM router integrating Qwen-Agent."""

from __future__ import annotations

from typing import Any, List, Dict, Iterable

from qwen_agent.agents import Assistant
from qwen_agent.tools import TOOL_REGISTRY
from config.settings import settings

from .fallback_prompt import generate_prompt, to_json
from .response_shaper import ResponseShaper


class LLMRouter:
    """Route prompts through a local Qwen-Agent assistant."""

    def __init__(self, model: str | None = None) -> None:
        """Create the assistant using Qwen3 and registered tools."""

        self.model = model or "Qwen/Qwen3-4B-Instruct"
        self.assistant: Assistant | None = None

    def _ensure_assistant(self) -> Assistant:
        """Lazily create the Qwen-Agent assistant."""
        if self.assistant is None:
            tool_names = list(TOOL_REGISTRY.keys())
            self.assistant = Assistant(
                function_list=tool_names,
                llm={"model": self.model, "model_type": "transformers"},
                generate_cfg=settings.llm.qwen_agent_generate_cfg,
            )
        return self.assistant

    def _needs_cloud(self, prompt: str) -> bool:
        """Heuristic to decide if a cloud model should be suggested."""
        lowered = prompt.lower()
        if any(k in lowered for k in ("summarize", "summary", "analyze", "analysis")):
            return True
        return len(prompt) > 400

    def _extract_text(self, response: Iterable[Dict[str, Any]] | Iterable[Any]) -> str:
        """Return the last assistant message text."""
        messages = list(response)
        if not messages:
            return ""
        last = messages[-1]
        if isinstance(last, dict):
            return (last.get("content") or "").strip()
        return (getattr(last, "content", "") or "").strip()

    def get_response(
        self,
        prompt: str,
        model: str,
        persona: str | None = None,
        tone: str | None = None,
        history: List[Dict[str, str]] | None = None,
    ) -> str:
        """Return the assistant reply or fallback suggestion."""
        if self._needs_cloud(prompt):
            fallback = generate_prompt(prompt)
            return to_json(fallback)

        messages: List[Dict[str, str]] = history[:] if history else []
        if persona or tone:
            styles = []
            if persona:
                styles.append(f"persona:{persona}")
            if tone:
                styles.append(f"tone:{tone}")
            messages.append({"role": "system", "content": f"[{','.join(styles)}]"})
        messages.append({"role": "user", "content": prompt})

        try:
            assistant = self._ensure_assistant()
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
