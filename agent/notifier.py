"""Cross-platform system notifications with optional TTS fallback."""

from __future__ import annotations

import logging
import platform
import shutil
import subprocess

try:
    from plyer import notification  # pragma: no cover - optional dep

    HAS_PLYER = True
except Exception:  # pragma: no cover - optional dep
    notification = None
    HAS_PLYER = False


class Notifier:
    """Send desktop notifications and optionally speak them."""

    def __init__(self) -> None:
        self.platform = platform.system().lower()
        self.tts_cmd = self._detect_tts()

    def _detect_tts(self) -> list[str] | None:
        if shutil.which("piper"):
            return ["piper", "--text"]
        if self.platform == "darwin" and shutil.which("say"):
            return ["say"]
        if self.platform.startswith("linux") and shutil.which("espeak"):
            return ["espeak"]
        if self.platform.startswith("win") and shutil.which("powershell"):
            return ["powershell", "-Command"]
        return None

    def _speak(self, text: str) -> bool:
        """Attempt to read ``text`` aloud using the detected TTS command.

        Returns ``True`` on success and ``False`` if the speech command fails.
        Only expected subprocess errors are caught so unexpected issues can
        surface during development.
        """

        if not self.tts_cmd:
            return False

        try:
            if self.tts_cmd[0] == "powershell":
                subprocess.run(
                    self.tts_cmd
                    + [
                        "Add-Type -AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak('{}')".format(
                            text.replace("'", " ")
                        )
                    ],
                    check=True,
                )
            else:
                subprocess.run(self.tts_cmd + [text], check=True)
            return True
        except (subprocess.CalledProcessError, OSError) as exc:
            logging.warning("Speech synthesis failed: %s", exc)
            return False

    def notify(self, title: str, message: str) -> None:
        text = f"{title}: {message}"
        sent = False
        if self.platform.startswith("linux") and shutil.which("notify-send"):
            try:
                subprocess.run(["notify-send", title, message], check=True)
                sent = True
            except Exception:  # pragma: no cover - optional
                sent = False
        elif self.platform == "darwin":
            try:
                subprocess.run(
                    [
                        "osascript",
                        "-e",
                        f'display notification "{message}" with title "{title}"',
                    ],
                    check=True,
                )
                sent = True
            except Exception:  # pragma: no cover - optional
                sent = False

        if not sent and notification:
            try:
                notification.notify(title=title, message=message)
                sent = True
            except Exception:  # pragma: no cover - optional
                sent = False

        if not sent:
            logging.info("notify", extra={"text": text})

        self._speak(text)
