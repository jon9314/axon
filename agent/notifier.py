"""Simple notification helper using plyer if available."""
from __future__ import annotations

try:
    from plyer import notification
except Exception:  # pragma: no cover - optional dep
    notification = None


class Notifier:
    def notify(self, title: str, message: str) -> None:
        if notification:
            try:
                notification.notify(title=title, message=message)
            except Exception:
                print(f"[NOTIFY] {title}: {message}")
        else:  # fallback to console output
            print(f"[NOTIFY] {title}: {message}")

