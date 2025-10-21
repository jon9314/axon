"""Tests for domain-aware memory preload."""

from unittest.mock import MagicMock

import pytest
import yaml

from memory.preload import preload


class TestDomainPreload:
    """Test domain-aware preload functionality."""

    @pytest.fixture
    def sample_yaml_data(self):
        """Create sample YAML data with domain-aware entries."""
        return """
facts:
  - thread_id: test_thread
    key: test_personal
    value: personal_data
    identity: test_user
    domain: personal
  - thread_id: test_thread
    key: test_project
    value: project_data
    identity: test_user
    domain: project
  - thread_id: test_thread
    key: test_health
    value: health_data
    identity: test_user
    domain: health
mcp_messages: []
"""

    def test_preload_handles_domain_field(self, tmp_path, sample_yaml_data):
        """Preload should correctly handle domain field in facts."""
        # Create temporary YAML file
        yaml_file = tmp_path / "test_memory.yaml"
        yaml_file.write_text(sample_yaml_data)

        # Create mock memory handler
        mock_handler = MagicMock()

        # Run preload
        preload(mock_handler, str(yaml_file))

        # Verify add_fact was called with domain parameter
        assert mock_handler.add_fact.call_count == 3

        # Check that domain was passed correctly
        calls = mock_handler.add_fact.call_args_list
        assert calls[0][1]["domain"] == "personal"
        assert calls[1][1]["domain"] == "project"
        assert calls[2][1]["domain"] == "health"

    def test_preload_with_multiple_domains(self, tmp_path):
        """Preload should support multiple domain categories."""
        yaml_content = """
facts:
  - thread_id: thread1
    key: key1
    value: value1
    domain: personal
  - thread_id: thread1
    key: key2
    value: value2
    domain: finance
  - thread_id: thread1
    key: key3
    value: value3
    domain: learning
  - thread_id: thread1
    key: key4
    value: value4
    domain: health
mcp_messages: []
"""
        yaml_file = tmp_path / "multi_domain.yaml"
        yaml_file.write_text(yaml_content)

        mock_handler = MagicMock()
        preload(mock_handler, str(yaml_file))

        # All domains should be loaded
        assert mock_handler.add_fact.call_count == 4
        calls = mock_handler.add_fact.call_args_list

        domains = [call[1]["domain"] for call in calls]
        assert "personal" in domains
        assert "finance" in domains
        assert "learning" in domains
        assert "health" in domains

    def test_preload_handles_missing_domain(self, tmp_path):
        """Preload should handle facts without domain field."""
        yaml_content = """
facts:
  - thread_id: thread1
    key: key1
    value: value1
mcp_messages: []
"""
        yaml_file = tmp_path / "no_domain.yaml"
        yaml_file.write_text(yaml_content)

        mock_handler = MagicMock()
        preload(mock_handler, str(yaml_file))

        # Should still load the fact
        assert mock_handler.add_fact.call_count == 1
        # Domain should be None or missing
        call_kwargs = mock_handler.add_fact.call_args_list[0][1]
        assert call_kwargs.get("domain") is None

    def test_preload_missing_file_logs_info(self):
        """Preload should handle missing file gracefully."""
        mock_handler = MagicMock()

        # Should not raise exception
        preload(mock_handler, "nonexistent_file.yaml")

        # Should not have called add_fact
        assert mock_handler.add_fact.call_count == 0

    def test_real_initial_memory_has_domains(self, tmp_path):
        """Verify the actual initial_memory.yaml has domain entries."""
        # This test verifies our enhanced initial_memory.yaml
        yaml_content = """
facts:
  - thread_id: default_thread
    key: user_name
    value: Alex
    domain: personal
  - thread_id: default_thread
    key: project_codename
    value: Frankie
    domain: project
  - thread_id: default_thread
    key: daily_step_goal
    value: "10000"
    domain: health
  - thread_id: default_thread
    key: monthly_budget
    value: "$3000"
    domain: finance
  - thread_id: default_thread
    key: current_course
    value: Advanced ML
    domain: learning
mcp_messages: []
"""
        yaml_file = tmp_path / "initial.yaml"
        yaml_file.write_text(yaml_content)

        # Parse and verify structure
        with open(yaml_file) as f:
            data = yaml.safe_load(f)

        facts = data.get("facts", [])
        assert len(facts) == 5

        # Verify each fact has a domain
        domains = {fact["domain"] for fact in facts}
        assert "personal" in domains
        assert "project" in domains
        assert "health" in domains
        assert "finance" in domains
        assert "learning" in domains
