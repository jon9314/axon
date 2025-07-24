"""Hands-free voice command shell using openwakeword and whisper."""

from __future__ import annotations

import shutil
import subprocess
from typing import Optional

from agent.plugin_loader import plugin
import time

try:  # pragma: no cover - optional deps
    from openwakeword.model import Model as WakeWordModel  # type: ignore
    import sounddevice as sd  # type: ignore
except Exception:  # pragma: no cover - optional deps
    WakeWordModel = None  # type: ignore
    sd = None  # type: ignore

try:  # pragma: no cover - optional deps
    import whisper  # type: ignore
except Exception:  # pragma: no cover - optional deps
    whisper = None  # type: ignore

__all__ = ["voice_shell"]


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


@plugin(
    name="voice_shell",
    description="Start a hands-free voice shell",
    usage="voice_shell(timeout=30)",
)
def voice_shell(
    model_path: str | None = None,
    wakeword: str = "axon",
    timeout: float | None = None,
) -> None:
    """Listen for a wake word and respond via speech.

    Parameters
    ----------
    model_path:
        Optional custom wake word model path.
    wakeword:
        Keyword that triggers recording.
    timeout:
        Maximum number of seconds to listen before exiting. ``None`` disables
        the time limit.
    """
    if WakeWordModel is None or whisper is None:
        print("openwakeword and whisper packages required")
        return

    wake = WakeWordModel(wakeword)
    asr = whisper.load_model("base")

    message = f"Say '{wakeword}' to begin recording."
    if timeout:
        message += f" Listening for {int(timeout)} seconds."
    message += " Ctrl+C to exit."
    print(message)
    start = time.monotonic()
    try:
        while True:
            if timeout is not None and time.monotonic() - start > timeout:
                print("Time limit reached, exiting voice shell")
                break
            data = _record(2.0)
            if data is None:
                break
            score = wake.predict(data)
            if score >= 0.5:
                audio = _record(5.0)
                if audio is None:
                    break
                text = asr.transcribe(audio, fp16=False)["text"].strip()
                _say(f"You said: {text}")
    except KeyboardInterrupt:
        print("Exiting voice shell")
