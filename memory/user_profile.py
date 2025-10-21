from __future__ import annotations

import os

import yaml

from axon.memory import MemoryRepository, ProfileRecord


class UserProfileManager:
    """Store and retrieve user profiles via the unified memory layer."""

    def __init__(
        self, repository: MemoryRepository | None = None, prefs_path: str = "config/user_prefs.yaml"
    ) -> None:
        self.repository = repository or MemoryRepository()
        self.load_from_yaml(prefs_path)

    def set_profile(
        self,
        identity: str,
        persona: str | None = None,
        tone: str | None = None,
        email: str | None = None,
    ) -> None:
        record = ProfileRecord(
            id=identity, scope=identity, fields={"persona": persona, "tone": tone, "email": email}
        )
        existing = self.repository.store.get(identity)
        if existing:
            self.repository.store.update(identity, fields=record.fields)
        else:
            self.repository.store.put(record)

    def get_profile(self, identity: str) -> dict | None:
        rec = self.repository.store.get(identity)
        if isinstance(rec, ProfileRecord):
            data = rec.fields.copy()
            data["identity"] = identity
            return data
        return None

    def load_from_yaml(self, path: str = "config/user_prefs.yaml") -> None:
        if not os.path.exists(path):
            return
        try:
            with open(path) as f:
                data = yaml.safe_load(f) or {}
        except Exception:
            return
        for identity, prefs in data.items():
            if self.get_profile(identity) is None:
                self.set_profile(
                    identity,
                    persona=prefs.get("persona"),
                    tone=prefs.get("tone"),
                    email=prefs.get("email"),
                )
