"""Tests for hosted proxy client with manual consent."""

import json
from pathlib import Path

import pytest

from agent.hosted_proxy import ConsentRecord, HostedProxyClient


@pytest.fixture
def temp_consent_db(tmp_path):
    """Temporary consent database."""
    return tmp_path / "test_consent.json"


@pytest.fixture
def proxy_client(temp_consent_db):
    """Hosted proxy client with temporary database."""
    return HostedProxyClient(consent_db_path=str(temp_consent_db))


class TestConsentRecord:
    """Tests for ConsentRecord class."""

    def test_create_consent_record(self):
        """Should create consent record with defaults."""
        record = ConsentRecord()

        assert record.granted is False
        assert record.timestamp is not None
        assert record.session_only is False
        assert record.providers == []

    def test_consent_record_with_values(self):
        """Should create consent record with specific values."""
        record = ConsentRecord(
            granted=True, timestamp="2025-01-01T00:00:00Z", session_only=True, providers=["openai"]
        )

        assert record.granted is True
        assert record.timestamp == "2025-01-01T00:00:00Z"
        assert record.session_only is True
        assert record.providers == ["openai"]


class TestHostedProxyClient:
    """Tests for HostedProxyClient."""

    def test_initialization(self, proxy_client, temp_consent_db):
        """Should initialize proxy client."""
        assert proxy_client.consent_db_path == Path(temp_consent_db)
        assert proxy_client.consent_records == {}
        assert proxy_client.session_consent == {}

    def test_grant_consent_persistent(self, proxy_client, temp_consent_db):
        """Should grant persistent consent."""
        proxy_client.grant_consent("user1", "openai", session_only=False)

        assert "user1" in proxy_client.consent_records
        assert proxy_client.consent_records["user1"].granted is True
        assert proxy_client.consent_records["user1"].providers == ["openai"]

        # Should persist to disk
        assert temp_consent_db.exists()
        data = json.loads(temp_consent_db.read_text())
        assert "user1" in data

    def test_grant_consent_session_only(self, proxy_client):
        """Should grant session-only consent."""
        proxy_client.grant_consent("user1", "anthropic", session_only=True)

        assert "user1:anthropic" in proxy_client.session_consent
        assert "user1" not in proxy_client.consent_records

    def test_grant_consent_all_providers(self, proxy_client):
        """Should grant consent for all providers."""
        proxy_client.grant_consent("user1", "openai", all_providers=True)

        assert "user1" in proxy_client.consent_records
        assert proxy_client.consent_records["user1"].providers == []  # Empty means all

    def test_request_consent_granted(self, proxy_client):
        """Should return True for granted consent."""
        proxy_client.grant_consent("user1", "openai")

        assert proxy_client.request_consent("user1", "openai") is True

    def test_request_consent_not_granted(self, proxy_client):
        """Should return False for non-granted consent."""
        assert proxy_client.request_consent("user1", "openai") is False

    def test_request_consent_all_providers(self, proxy_client):
        """Should grant consent for any provider when all_providers=True."""
        proxy_client.grant_consent("user1", "openai", all_providers=True)

        assert proxy_client.request_consent("user1", "openai") is True
        assert proxy_client.request_consent("user1", "anthropic") is True
        assert proxy_client.request_consent("user1", "google") is True

    def test_revoke_consent_persistent(self, proxy_client, temp_consent_db):
        """Should revoke persistent consent."""
        proxy_client.grant_consent("user1", "openai")
        proxy_client.revoke_consent("user1", session_only=False)

        assert "user1" not in proxy_client.consent_records

        # Should remove from disk
        if temp_consent_db.exists():
            data = json.loads(temp_consent_db.read_text())
            assert "user1" not in data

    def test_revoke_consent_session_only(self, proxy_client):
        """Should revoke session consent."""
        proxy_client.grant_consent("user1", "openai", session_only=True)
        proxy_client.revoke_consent("user1", session_only=True)

        assert "user1:openai" not in proxy_client.session_consent

    def test_call_with_consent_success(self, proxy_client):
        """Should allow call with granted consent."""
        proxy_client.grant_consent("user1", "openai")

        result = proxy_client.call_with_consent(user_id="user1", provider="openai", prompt="Hello")

        assert result["status"] == "consent_granted_but_not_implemented"
        assert result["user_id"] == "user1"
        assert result["provider"] == "openai"

    def test_call_with_consent_denied(self, proxy_client):
        """Should deny call without consent."""
        with pytest.raises(PermissionError, match="Consent not granted"):
            proxy_client.call_with_consent(user_id="user1", provider="openai", prompt="Hello")

    def test_get_consent_status_granted(self, proxy_client):
        """Should get consent status for granted user."""
        proxy_client.grant_consent("user1", "openai")

        status = proxy_client.get_consent_status("user1")

        assert status["granted"] is True
        assert status["providers"] == ["openai"]

    def test_get_consent_status_not_granted(self, proxy_client):
        """Should get consent status for non-granted user."""
        status = proxy_client.get_consent_status("user1")

        assert status["granted"] is False
        assert status["providers"] == []

    def test_list_consents(self, proxy_client):
        """Should list all consents."""
        proxy_client.grant_consent("user1", "openai")
        proxy_client.grant_consent("user2", "anthropic", session_only=True)

        consents = proxy_client.list_consents()

        assert "user1" in consents
        assert "user2" in consents
        assert consents["user1"]["providers"] == ["openai"]
        assert consents["user2"]["session_only"] is True

    def test_load_consent_from_disk(self, temp_consent_db):
        """Should load consent records from disk."""
        # Create consent file
        data = {
            "user1": {
                "granted": True,
                "timestamp": "2025-01-01T00:00:00Z",
                "session_only": False,
                "providers": ["openai"],
            }
        }
        temp_consent_db.parent.mkdir(parents=True, exist_ok=True)
        temp_consent_db.write_text(json.dumps(data))

        # Create client (should load from disk)
        client = HostedProxyClient(consent_db_path=str(temp_consent_db))

        assert "user1" in client.consent_records
        assert client.consent_records["user1"].granted is True
        assert client.consent_records["user1"].providers == ["openai"]
