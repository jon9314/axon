from __future__ import annotations

import logging
import shutil
import subprocess

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


class ShellInput(BaseModel):
    timeout: float | None = None
    model_path: str | None = None
    wakeword: str = "axon"


class ShellOutput(BaseModel):
    result: str | None = None


def _say(text: str) -> None:
    """Use piper TTS if available."""
    if shutil.which("piper"):
        try:  # pragma: no cover - optional command
            subprocess.run(["piper", "--text", text], check=True)
            return
        except Exception:
            pass
    logging.info("say", extra={"text": text})


def _record(duration: float = 5.0, rate: int = 16000) -> bytes | None:
    """Record audio from the microphone and return raw bytes."""
    if not sd:  # pragma: no cover - optional dependency
        logging.error("sounddevice-missing")
        return None
    audio = sd.rec(int(duration * rate), samplerate=rate, channels=1, dtype="int16")
    sd.wait()
    return audio.tobytes()


class VoiceShellPlugin(Plugin[ShellInput, ShellOutput]):
    """Hands-free voice shell."""

    input_model = ShellInput
    output_model = ShellOutput

    def load(self, config: BaseModel | None) -> None:  # pragma: no cover - simple
        return

    def describe(self) -> dict[str, str]:
        return {"name": self.manifest.name, "description": self.manifest.description}

    def execute(self, data: ShellInput) -> ShellOutput:
        if WakeWordModel is None or whisper is None:  # pragma: no cover - optional deps
            return ShellOutput(result="openwakeword and whisper packages required")
        _say("Voice shell started")
        return ShellOutput(result=None)


PLUGIN_CLASS = VoiceShellPlugin
