from __future__ import annotations

import secrets
from typing import Dict, Optional, Tuple


class SessionTracker:
    """In-memory mapping of session tokens to identity and thread."""

    def __init__(self) -> None:
        self._sessions: Dict[str, Tuple[str, str]] = {}

    def create_session(
        self, identity: str, thread_id: str | None = None
    ) -> tuple[str, str]:
        """Create a new session token for an identity."""
        token = secrets.token_urlsafe(16)
        tid = thread_id or f"{identity}_{secrets.token_hex(4)}"
        self._sessions[token] = (identity, tid)
        return token, tid

    def resolve(self, token: str) -> Optional[Tuple[str, str]]:
        """Return the identity and thread for a token if it exists."""
        return self._sessions.get(token)

    def remove(self, token: str) -> None:
        """Delete a session token."""
        self._sessions.pop(token, None)
