"""Optional fallback through hosted proxy with manual consent.

This module provides controlled cloud integration for LLM requests,
requiring explicit user consent before making any external API calls.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class ConsentRecord:
    """Record of user consent for hosted proxy usage."""

    def __init__(
        self,
        granted: bool = False,
        timestamp: str | None = None,
        session_only: bool = False,
        providers: list[str] | None = None,
    ) -> None:
        self.granted = granted
        self.timestamp = timestamp or datetime.utcnow().isoformat()
        self.session_only = session_only
        self.providers = providers or []


class HostedProxyClient:
    """Client for hosted LLM proxy with manual consent requirements.

    This client ensures that all external API calls require explicit
    user consent. No automatic requests are made without confirmation.
    """

    def __init__(
        self,
        consent_db_path: str = "data/proxy_consent.json",
        proxy_url: str | None = None,
    ) -> None:
        """Initialize hosted proxy client.

        Args:
            consent_db_path: Path to consent database file
            proxy_url: URL of hosted proxy service (if None, uses environment)
        """
        self.consent_db_path = Path(consent_db_path)
        self.consent_db_path.parent.mkdir(parents=True, exist_ok=True)
        self.proxy_url = proxy_url or self._get_proxy_url()

        # Load consent records
        self.consent_records: dict[str, ConsentRecord] = {}
        self._load_consent()

        # Session-level consent (not persisted)
        self.session_consent: dict[str, bool] = {}

    def _get_proxy_url(self) -> str:
        """Get proxy URL from environment or settings."""
        import os

        url = os.getenv("AXON_HOSTED_PROXY_URL", "")
        if not url:
            logger.warning("No hosted proxy URL configured")
        return url

    def _load_consent(self) -> None:
        """Load consent records from disk."""
        if not self.consent_db_path.exists():
            return

        try:
            data = json.loads(self.consent_db_path.read_text())
            for user_id, record in data.items():
                self.consent_records[user_id] = ConsentRecord(
                    granted=record.get("granted", False),
                    timestamp=record.get("timestamp"),
                    session_only=record.get("session_only", False),
                    providers=record.get("providers", []),
                )
        except Exception as e:
            logger.error(f"Failed to load consent records: {e}")

    def _save_consent(self) -> None:
        """Save consent records to disk."""
        try:
            data = {}
            for user_id, record in self.consent_records.items():
                if not record.session_only:  # Only persist non-session consent
                    data[user_id] = {
                        "granted": record.granted,
                        "timestamp": record.timestamp,
                        "session_only": record.session_only,
                        "providers": record.providers,
                    }

            self.consent_db_path.write_text(json.dumps(data, indent=2))
        except Exception as e:
            logger.error(f"Failed to save consent records: {e}")

    def request_consent(
        self,
        user_id: str,
        provider: str,
        session_only: bool = False,
    ) -> bool:
        """Request consent from user for hosted proxy usage.

        This is a synchronous check - actual consent collection would
        be done through UI or CLI prompts elsewhere.

        Args:
            user_id: User identifier
            provider: Provider name (e.g., "openai", "anthropic")
            session_only: If True, consent is only for current session

        Returns:
            True if consent already granted, False otherwise
        """
        # Check session consent
        session_key = f"{user_id}:{provider}"
        if session_key in self.session_consent:
            return self.session_consent[session_key]

        # Check persisted consent
        if user_id in self.consent_records:
            record = self.consent_records[user_id]
            if record.granted and (not record.providers or provider in record.providers):
                return True

        return False

    def grant_consent(
        self,
        user_id: str,
        provider: str,
        session_only: bool = False,
        all_providers: bool = False,
    ) -> None:
        """Grant consent for hosted proxy usage.

        Args:
            user_id: User identifier
            provider: Provider name to grant consent for
            session_only: If True, consent is only for current session
            all_providers: If True, grant consent for all providers
        """
        providers = [] if all_providers else [provider]

        record = ConsentRecord(
            granted=True,
            timestamp=datetime.utcnow().isoformat(),
            session_only=session_only,
            providers=providers,
        )

        if session_only:
            # Store in session memory
            session_key = f"{user_id}:{provider}" if not all_providers else f"{user_id}:*"
            self.session_consent[session_key] = True
        else:
            # Persist consent
            self.consent_records[user_id] = record
            self._save_consent()

        logger.info(
            "proxy-consent-granted",
            extra={
                "user_id": user_id,
                "provider": provider,
                "session_only": session_only,
                "all_providers": all_providers,
            },
        )

    def revoke_consent(self, user_id: str, session_only: bool = False) -> None:
        """Revoke consent for hosted proxy usage.

        Args:
            user_id: User identifier
            session_only: If True, only revoke session consent
        """
        if session_only:
            # Clear session consent
            keys_to_remove = [k for k in self.session_consent.keys() if k.startswith(f"{user_id}:")]
            for key in keys_to_remove:
                del self.session_consent[key]
        else:
            # Remove persisted consent
            if user_id in self.consent_records:
                del self.consent_records[user_id]
                self._save_consent()

        logger.info("proxy-consent-revoked", extra={"user_id": user_id, "session_only": session_only})

    def call_with_consent(
        self,
        user_id: str,
        provider: str,
        prompt: str,
        model: str | None = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
    ) -> dict[str, Any]:
        """Call hosted proxy with consent check.

        Args:
            user_id: User identifier
            provider: Provider name (e.g., "openai", "anthropic")
            prompt: Prompt to send to model
            model: Specific model to use
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature

        Returns:
            Response from hosted proxy

        Raises:
            PermissionError: If consent not granted
            RuntimeError: If proxy URL not configured or request fails
        """
        if not self.request_consent(user_id, provider):
            raise PermissionError(
                f"Consent not granted for user '{user_id}' and provider '{provider}'. "
                "Use grant_consent() first or enable manual approval in UI."
            )

        if not self.proxy_url:
            raise RuntimeError("Hosted proxy URL not configured. Set AXON_HOSTED_PROXY_URL.")

        # This is a placeholder for actual HTTP request to hosted proxy
        # In production, this would use requests or httpx
        logger.info(
            "proxy-call-requested",
            extra={
                "user_id": user_id,
                "provider": provider,
                "model": model,
                "prompt_length": len(prompt),
            },
        )

        # Simulate response structure
        # In production, this would make actual HTTP request:
        # response = requests.post(
        #     f"{self.proxy_url}/v1/chat/completions",
        #     headers={"Authorization": f"Bearer {api_key}"},
        #     json={
        #         "provider": provider,
        #         "model": model,
        #         "prompt": prompt,
        #         "max_tokens": max_tokens,
        #         "temperature": temperature,
        #     }
        # )

        return {
            "status": "consent_granted_but_not_implemented",
            "message": "Hosted proxy call would be made here with user consent",
            "user_id": user_id,
            "provider": provider,
            "model": model,
            "prompt_preview": prompt[:100] + "..." if len(prompt) > 100 else prompt,
        }

    def get_consent_status(self, user_id: str) -> dict[str, Any]:
        """Get consent status for a user.

        Args:
            user_id: User identifier

        Returns:
            Dictionary with consent status information
        """
        if user_id in self.consent_records:
            record = self.consent_records[user_id]
            return {
                "granted": record.granted,
                "timestamp": record.timestamp,
                "session_only": record.session_only,
                "providers": record.providers or ["*"],
            }

        # Check session consent
        session_keys = [k for k in self.session_consent.keys() if k.startswith(f"{user_id}:")]
        if session_keys:
            return {
                "granted": True,
                "timestamp": None,
                "session_only": True,
                "providers": [k.split(":", 1)[1] for k in session_keys],
            }

        return {
            "granted": False,
            "timestamp": None,
            "session_only": False,
            "providers": [],
        }

    def list_consents(self) -> dict[str, dict[str, Any]]:
        """List all consent records.

        Returns:
            Dictionary mapping user IDs to consent status
        """
        result: dict[str, dict[str, Any]] = {}

        # Add persisted consents
        for user_id, record in self.consent_records.items():
            result[user_id] = {
                "granted": record.granted,
                "timestamp": record.timestamp,
                "session_only": record.session_only,
                "providers": record.providers or ["*"],
            }

        # Add session consents
        for session_key in self.session_consent.keys():
            user_id, provider = session_key.split(":", 1)
            if user_id not in result:
                result[user_id] = {
                    "granted": True,
                    "timestamp": None,
                    "session_only": True,
                    "providers": [provider],
                }
            elif provider not in result[user_id]["providers"]:
                result[user_id]["providers"].append(provider)

        return result
