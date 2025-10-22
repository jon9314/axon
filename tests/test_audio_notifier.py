"""Tests for text-to-speech and audio notifications."""


from agent.audio_notifier import AudioNotifier, TTSEngine, TTSNotificationService


class TestTTSEngine:
    """Tests for TTSEngine."""

    def test_initialization(self):
        """Should initialize TTS engine."""
        tts = TTSEngine(engine="system", rate=175, volume=0.9)

        assert tts.engine_name == "system"
        assert tts.rate == 175
        assert tts.volume == 0.9

    def test_select_best_engine(self):
        """Should select best available engine."""
        tts = TTSEngine(engine="auto")

        assert tts.engine_name in ["pyttsx3", "gtts", "system"]

    def test_speak_empty_text(self):
        """Should return False for empty text."""
        tts = TTSEngine(engine="system")

        result = tts.speak("")

        assert result is False

    def test_speak_system_backend(self):
        """Should attempt to speak using system backend."""
        tts = TTSEngine(engine="system")

        # This may or may not succeed depending on platform
        # Just verify it doesn't crash
        result = tts.speak("test", blocking=False)

        assert isinstance(result, bool)

    def test_list_voices_no_engine(self):
        """Should return empty list when no engine available."""
        tts = TTSEngine(engine="system")

        voices = tts.list_voices()

        # System engine has no voice listing
        assert isinstance(voices, list)


class TestAudioNotifier:
    """Tests for AudioNotifier."""

    def test_initialization(self, tmp_path):
        """Should initialize audio notifier."""
        sounds_dir = tmp_path / "sounds"
        notifier = AudioNotifier(sounds_dir=str(sounds_dir))

        assert notifier.sounds_dir == sounds_dir
        assert sounds_dir.exists()

    def test_play_notification_missing_file(self, tmp_path):
        """Should fall back to system beep for missing file."""
        notifier = AudioNotifier(sounds_dir=str(tmp_path / "sounds"))

        # Should not crash, may return True or False depending on platform
        result = notifier.play_notification("nonexistent")

        assert isinstance(result, bool)

    def test_notify_reminder(self, tmp_path):
        """Should send reminder notification."""
        notifier = AudioNotifier(sounds_dir=str(tmp_path / "sounds"))

        # Should not crash
        notifier.notify_reminder("Test reminder", speak=False)

    def test_notify_alert_levels(self, tmp_path):
        """Should send alerts with different urgency levels."""
        notifier = AudioNotifier(sounds_dir=str(tmp_path / "sounds"))

        for urgency in ["low", "normal", "high", "critical"]:
            notifier.notify_alert("Test alert", urgency=urgency)


class TestTTSNotificationService:
    """Tests for TTSNotificationService."""

    def test_initialization_enabled(self):
        """Should initialize service when enabled."""
        service = TTSNotificationService(enabled=True)

        assert service.enabled is True
        assert service.tts is not None
        assert service.audio is not None

    def test_initialization_disabled(self):
        """Should initialize service when disabled."""
        service = TTSNotificationService(enabled=False)

        assert service.enabled is False
        assert service.tts is None
        assert service.audio is None

    def test_speak_response_disabled(self):
        """Should return False when disabled."""
        service = TTSNotificationService(enabled=False)

        result = service.speak_response("test")

        assert result is False

    def test_speak_response_enabled(self):
        """Should attempt to speak when enabled."""
        service = TTSNotificationService(enabled=True)

        # May or may not succeed depending on platform
        result = service.speak_response("test", blocking=False)

        assert isinstance(result, bool)

    def test_notify_with_speech_disabled(self):
        """Should do nothing when disabled."""
        service = TTSNotificationService(enabled=False)

        # Should not crash
        service.notify_with_speech("test")

    def test_set_enabled(self):
        """Should enable/disable service."""
        service = TTSNotificationService(enabled=False)

        service.set_enabled(True)
        assert service.enabled is True

        service.set_enabled(False)
        assert service.enabled is False


class TestTTSBackends:
    """Tests for different TTS backends."""

    def test_system_backend_initialization(self):
        """Should initialize system backend."""
        tts = TTSEngine(engine="system")

        assert tts.engine_name == "system"

    def test_pyttsx3_backend_fallback(self):
        """Should fall back to system if pyttsx3 unavailable."""
        tts = TTSEngine(engine="pyttsx3")

        # If pyttsx3 not available, should fall back to system
        assert tts.engine_name in ["pyttsx3", "system"]

    def test_gtts_backend_selection(self):
        """Should select gtts backend if requested."""
        tts = TTSEngine(engine="gtts")

        # If gtts not available, should be set to gtts (but won't work)
        assert tts.engine_name == "gtts"
