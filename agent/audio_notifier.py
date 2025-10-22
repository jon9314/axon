"""Text-to-speech and audio notifications.

This module provides TTS capabilities for agent responses and
audio notification alerts for reminders and important events.
"""

from __future__ import annotations

import logging
import subprocess
import sys
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Check for optional TTS dependencies
HAS_PYTTSX3 = False
HAS_GTTS = False
HAS_PYGAME = False

try:
    import pyttsx3

    HAS_PYTTSX3 = True
except ImportError:
    pass

try:
    from gtts import gTTS

    HAS_GTTS = True
except ImportError:
    pass

try:
    import pygame

    HAS_PYGAME = True
except ImportError:
    pass


class TTSEngine:
    """Text-to-speech engine with multiple backend support."""

    def __init__(
        self,
        engine: str = "auto",
        rate: int = 175,
        volume: float = 0.9,
        voice: str | None = None,
    ) -> None:
        """Initialize TTS engine.

        Args:
            engine: TTS engine to use ("pyttsx3", "gtts", "system", "auto")
            rate: Speech rate (words per minute)
            volume: Volume level (0.0 to 1.0)
            voice: Voice identifier (engine-specific)
        """
        self.engine_name = engine
        self.rate = rate
        self.volume = volume
        self.voice = voice

        # Select engine
        if engine == "auto":
            self.engine_name = self._select_best_engine()

        self.tts_engine: Any = None
        self._initialize_engine()

    def _select_best_engine(self) -> str:
        """Select best available TTS engine."""
        if HAS_PYTTSX3:
            return "pyttsx3"
        elif HAS_GTTS:
            return "gtts"
        else:
            return "system"

    def _initialize_engine(self) -> None:
        """Initialize the selected TTS engine."""
        if self.engine_name == "pyttsx3" and HAS_PYTTSX3:
            try:
                self.tts_engine = pyttsx3.init()
                self.tts_engine.setProperty("rate", self.rate)
                self.tts_engine.setProperty("volume", self.volume)

                if self.voice:
                    self.tts_engine.setProperty("voice", self.voice)

                logger.info("TTS engine initialized: pyttsx3")
            except Exception as e:
                logger.error(f"Failed to initialize pyttsx3: {e}")
                self.engine_name = "system"

    def speak(self, text: str, blocking: bool = True) -> bool:
        """Speak text using TTS.

        Args:
            text: Text to speak
            blocking: If True, wait for speech to complete

        Returns:
            True if successful, False otherwise
        """
        if not text:
            return False

        try:
            if self.engine_name == "pyttsx3" and self.tts_engine:
                self.tts_engine.say(text)
                if blocking:
                    self.tts_engine.runAndWait()
                return True

            elif self.engine_name == "gtts" and HAS_GTTS:
                return self._speak_gtts(text)

            elif self.engine_name == "system":
                return self._speak_system(text)

            else:
                logger.warning(f"No TTS engine available (requested: {self.engine_name})")
                return False

        except Exception as e:
            logger.error(f"TTS error: {e}")
            return False

    def _speak_gtts(self, text: str) -> bool:
        """Speak using Google TTS (requires internet)."""
        try:
            import tempfile

            tts = gTTS(text=text, lang="en")

            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
                temp_file = fp.name
                tts.save(temp_file)

            # Play audio file
            if HAS_PYGAME:
                pygame.mixer.init()
                pygame.mixer.music.load(temp_file)
                pygame.mixer.music.play()

                while pygame.mixer.music.get_busy():
                    pygame.time.Clock().tick(10)

                Path(temp_file).unlink()
            else:
                logger.warning("pygame not available for audio playback")
                return False

            return True

        except Exception as e:
            logger.error(f"gTTS error: {e}")
            return False

    def _speak_system(self, text: str) -> bool:
        """Speak using system TTS command."""
        try:
            if sys.platform == "darwin":  # macOS
                subprocess.run(["say", text], check=False)
                return True

            elif sys.platform == "win32":  # Windows
                # Use PowerShell Add-Type for TTS
                ps_command = f'Add-Type -AssemblyName System.Speech; $synth = New-Object System.Speech.Synthesis.SpeechSynthesizer; $synth.Speak("{text}")'
                subprocess.run(["powershell", "-Command", ps_command], check=False)
                return True

            elif sys.platform.startswith("linux"):
                # Try espeak on Linux
                result = subprocess.run(
                    ["espeak", text],
                    capture_output=True,
                    check=False,
                )
                if result.returncode == 0:
                    return True

                # Fall back to festival
                result = subprocess.run(
                    ["festival", "--tts"],
                    input=text.encode(),
                    capture_output=True,
                    check=False,
                )
                return result.returncode == 0

            else:
                logger.warning(f"No system TTS available for platform: {sys.platform}")
                return False

        except Exception as e:
            logger.error(f"System TTS error: {e}")
            return False

    def list_voices(self) -> list[str]:
        """List available voices.

        Returns:
            List of voice identifiers
        """
        if self.engine_name == "pyttsx3" and self.tts_engine:
            try:
                voices = self.tts_engine.getProperty("voices")
                return [v.id for v in voices]
            except Exception:
                return []

        return []

    def set_voice(self, voice_id: str) -> None:
        """Set voice by identifier.

        Args:
            voice_id: Voice identifier from list_voices()
        """
        self.voice = voice_id

        if self.engine_name == "pyttsx3" and self.tts_engine:
            try:
                self.tts_engine.setProperty("voice", voice_id)
            except Exception as e:
                logger.error(f"Failed to set voice: {e}")


class AudioNotifier:
    """Audio notification system for alerts and reminders."""

    def __init__(self, sounds_dir: str = "data/sounds") -> None:
        """Initialize audio notifier.

        Args:
            sounds_dir: Directory containing notification sound files
        """
        self.sounds_dir = Path(sounds_dir)
        self.sounds_dir.mkdir(parents=True, exist_ok=True)

        # Initialize pygame mixer for sound playback
        if HAS_PYGAME:
            try:
                pygame.mixer.init()
                self.enabled = True
            except Exception as e:
                logger.error(f"Failed to initialize pygame mixer: {e}")
                self.enabled = False
        else:
            self.enabled = False
            logger.warning("pygame not available - audio notifications disabled")

    def play_notification(self, sound_name: str = "default") -> bool:
        """Play notification sound.

        Args:
            sound_name: Name of sound file (without extension)

        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            return False

        sound_file = self.sounds_dir / f"{sound_name}.wav"

        if not sound_file.exists():
            # Try to play system beep as fallback
            return self._play_system_beep()

        try:
            sound = pygame.mixer.Sound(str(sound_file))
            sound.play()
            return True
        except Exception as e:
            logger.error(f"Failed to play sound: {e}")
            return self._play_system_beep()

    def _play_system_beep(self) -> bool:
        """Play system beep sound."""
        try:
            if sys.platform == "darwin":  # macOS
                subprocess.run(["afplay", "/System/Library/Sounds/Ping.aiff"], check=False)
                return True

            elif sys.platform == "win32":  # Windows
                import winsound

                winsound.Beep(1000, 200)  # 1000 Hz for 200ms
                return True

            elif sys.platform.startswith("linux"):
                # Use beep command on Linux
                subprocess.run(["beep"], check=False)
                return True

            else:
                print("\a")  # ASCII bell character
                return True

        except Exception as e:
            logger.error(f"Failed to play system beep: {e}")
            return False

    def notify_reminder(self, message: str, speak: bool = True) -> None:
        """Send reminder notification with optional TTS.

        Args:
            message: Reminder message
            speak: If True, speak the message using TTS
        """
        # Play notification sound
        self.play_notification("reminder")

        # Speak message if requested
        if speak:
            tts = TTSEngine()
            tts.speak(message)

        logger.info("reminder-notification", extra={"message": message, "speak": speak})

    def notify_alert(self, message: str, urgency: str = "normal") -> None:
        """Send alert notification.

        Args:
            message: Alert message
            urgency: Urgency level ("low", "normal", "high", "critical")
        """
        sound_map = {
            "low": "notification",
            "normal": "alert",
            "high": "urgent",
            "critical": "critical",
        }

        sound_name = sound_map.get(urgency, "alert")
        self.play_notification(sound_name)

        logger.info("alert-notification", extra={"message": message, "urgency": urgency})


class TTSNotificationService:
    """Combined TTS and audio notification service."""

    def __init__(
        self,
        tts_engine: str = "auto",
        sounds_dir: str = "data/sounds",
        enabled: bool = True,
    ) -> None:
        """Initialize notification service.

        Args:
            tts_engine: TTS engine to use
            sounds_dir: Directory for sound files
            enabled: Enable/disable notifications
        """
        self.enabled = enabled
        self.tts = TTSEngine(engine=tts_engine) if enabled else None
        self.audio = AudioNotifier(sounds_dir=sounds_dir) if enabled else None

    def speak_response(self, text: str, blocking: bool = False) -> bool:
        """Speak agent response.

        Args:
            text: Response text
            blocking: Wait for speech to complete

        Returns:
            True if successful
        """
        if not self.enabled or not self.tts:
            return False

        return self.tts.speak(text, blocking=blocking)

    def notify_with_speech(self, message: str, sound: str = "notification") -> None:
        """Send notification with TTS.

        Args:
            message: Message to speak
            sound: Notification sound to play
        """
        if not self.enabled:
            return

        if self.audio:
            self.audio.play_notification(sound)

        if self.tts:
            self.tts.speak(message)

    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable notifications.

        Args:
            enabled: Enable notifications
        """
        self.enabled = enabled
        logger.info("notifications-toggled", extra={"enabled": enabled})
