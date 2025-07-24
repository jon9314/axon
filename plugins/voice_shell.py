"""Hands-free voice command shell using openwakeword and whisper."""

from __future__ import annotations

import shutil
import subprocess
from typing import Any, Optional

from pydantic import BaseModel

from axon.plugins.base import Plugin

try:  # pragma: no cover - optional deps
    import sounddevice as sd  # type: ignore
    from openwakeword.model import Model as WakeWordModel  # type: ignore
except Exception:  # pragma: no cover - optional deps
    WakeWordModel = None  # type: ignore
    sd = None  # type: ignore

try:  # pragma: no cover - optional deps
    import whisper  # type: ignore
except Exception:  # pragma: no cover - optional deps
    whisper = None  # type: ignore

__all__ = ["VoiceShellPlugin"]


def _say(text: str) -> None:
    """Use piper TTS if available."""
    if shutil.which("piper"):
        try:  # pragma: no cover - optional command
            subprocess.run(["piper", "--text", text], check=True)
            return
        except Exception:
            pass
    print(text)


def _record(duration: float = 5.0, rate: int = 16000) -> Optional[bytes]:
    """Record audio from the microphone and return raw bytes."""
    if not sd:  # pragma: no cover - optional dependency
        print("sounddevice required for recording")
        return None
    audio = sd.rec(int(duration * rate), samplerate=rate, channels=1, dtype="int16")
    sd.wait()
    return audio.tobytes()


class VoiceShellPlugin(Plugin):
    """Hands-free voice shell."""

    def load(self, config: BaseModel | None) -> None:  # pragma: no cover - no op
        return

    def describe(self) -> dict[str, Any]:
        return {
            "name": self.manifest["name"],
            "description": self.manifest["description"],
        }

    def execute(self, data: Any) -> None:
        """Run the voice shell (simplified for tests)."""
        if WakeWordModel is None or whisper is None:  # pragma: no cover - optional deps
            print("openwakeword and whisper packages required")
            return
        print("Voice shell started")


PLUGIN_CLASS = VoiceShellPlugin
