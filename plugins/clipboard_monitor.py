from agent.plugin_loader import plugin
import time

try:
    import pyperclip
    import keyboard
except Exception:  # pragma: no cover - optional dependency
    pyperclip = None
    keyboard = None

@plugin(
    name="clipboard_monitor",
    description="Watch clipboard for updates for a few seconds",
    usage="clipboard_monitor(seconds=15)"
)
def clipboard_monitor(seconds: int = 15):
    """Return clipboard changes detected within the given period."""
    if not pyperclip or not keyboard:
        return "pyperclip and keyboard modules required"
    end = time.time() + seconds
    last = pyperclip.paste()
    seen: list[str] = []
    while time.time() < end:
        current = pyperclip.paste()
        if current != last:
            seen.append(current)
            last = current
        time.sleep(0.5)
    return seen
