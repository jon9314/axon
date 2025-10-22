"""Tests for pasteback handler with source annotations."""

import json

import pytest

from agent.pasteback_handler import PastebackHandler, SourceAnnotation


class MockMemoryHandler:
    """Mock memory handler for testing."""

    def __init__(self):
        self.facts = []

    def add_fact(
        self, thread_id, key, value, identity=None, domain=None, tags=None
    ):
        self.facts.append(
            {
                "thread_id": thread_id,
                "key": key,
                "value": value,
                "identity": identity,
                "domain": domain,
                "tags": tags or [],
            }
        )

    def list_facts(self, thread_id, domain=None):
        """List facts matching criteria."""
        results = []
        for fact in self.facts:
            if fact["thread_id"] == thread_id:
                if domain is None or fact["domain"] == domain:
                    results.append(
                        (
                            fact["key"],
                            fact["value"],
                            fact["identity"],
                            False,  # locked
                            fact["tags"],
                        )
                    )
        return results


@pytest.fixture
def memory_handler():
    """Mock memory handler."""
    return MockMemoryHandler()


@pytest.fixture
def pasteback_handler(memory_handler):
    """Pasteback handler with mock memory."""
    return PastebackHandler(memory_handler)


class TestSourceAnnotation:
    """Tests for SourceAnnotation class."""

    def test_create_annotation(self):
        """Should create source annotation."""
        annotation = SourceAnnotation(
            model="gpt-4", provider="openai", url="https://chat.openai.com", cost=0.03, tokens=500
        )

        assert annotation.model == "gpt-4"
        assert annotation.provider == "openai"
        assert annotation.url == "https://chat.openai.com"
        assert annotation.cost == 0.03
        assert annotation.tokens == 500

    def test_infer_provider_openai(self):
        """Should infer OpenAI provider."""
        annotation = SourceAnnotation(model="gpt-4-turbo")

        assert annotation.provider == "openai"

    def test_infer_provider_anthropic(self):
        """Should infer Anthropic provider."""
        annotation = SourceAnnotation(model="claude-3-opus")

        assert annotation.provider == "anthropic"

    def test_infer_provider_google(self):
        """Should infer Google provider."""
        annotation = SourceAnnotation(model="gemini-pro")

        assert annotation.provider == "google"

    def test_infer_provider_meta(self):
        """Should infer Meta provider."""
        annotation = SourceAnnotation(model="llama-3-70b")

        assert annotation.provider == "meta"

    def test_infer_provider_unknown(self):
        """Should return unknown for unrecognized models."""
        annotation = SourceAnnotation(model="custom-model")

        assert annotation.provider == "unknown"

    def test_to_dict(self):
        """Should convert to dictionary."""
        annotation = SourceAnnotation(model="gpt-4", provider="openai", cost=0.03)

        data = annotation.to_dict()

        assert data["model"] == "gpt-4"
        assert data["provider"] == "openai"
        assert data["cost"] == 0.03
        assert "timestamp" in data

    def test_to_json(self):
        """Should convert to JSON string."""
        annotation = SourceAnnotation(model="gpt-4")

        json_str = annotation.to_json()

        data = json.loads(json_str)
        assert data["model"] == "gpt-4"

    def test_from_dict(self):
        """Should create from dictionary."""
        data = {
            "model": "gpt-4",
            "provider": "openai",
            "timestamp": "2025-01-01T00:00:00Z",
            "url": "https://example.com",
            "cost": 0.03,
            "tokens": 500,
            "metadata": {"key": "value"},
        }

        annotation = SourceAnnotation.from_dict(data)

        assert annotation.model == "gpt-4"
        assert annotation.provider == "openai"
        assert annotation.cost == 0.03
        assert annotation.metadata == {"key": "value"}

    def test_from_json(self):
        """Should create from JSON string."""
        json_str = '{"model": "gpt-4", "provider": "openai", "cost": 0.03}'

        annotation = SourceAnnotation.from_json(json_str)

        assert annotation.model == "gpt-4"
        assert annotation.provider == "openai"
        assert annotation.cost == 0.03


class TestPastebackHandler:
    """Tests for PastebackHandler with source annotations."""

    def test_store_without_annotation(self, pasteback_handler, memory_handler):
        """Should store response without annotation (backward compatible)."""
        pasteback_handler.store(
            thread_id="test_thread", prompt="What is AI?", response="AI is...", model="gpt-4"
        )

        assert len(memory_handler.facts) == 2  # Prompt + response
        prompt_fact = memory_handler.facts[0]
        response_fact = memory_handler.facts[1]

        assert "cloud_prompt_" in prompt_fact["key"]
        assert prompt_fact["value"] == "What is AI?"
        assert prompt_fact["domain"] == "cloud_interaction"

        assert "cloud_response_" in response_fact["key"]
        assert response_fact["value"] == "AI is..."
        assert "cloud" in response_fact["tags"]

    def test_store_with_annotation(self, pasteback_handler, memory_handler):
        """Should store response with annotation."""
        annotation = SourceAnnotation(model="gpt-4", provider="openai", cost=0.03, tokens=500)

        pasteback_handler.store(
            thread_id="test_thread",
            prompt="What is AI?",
            response="AI is...",
            model="gpt-4",
            source_annotation=annotation,
        )

        response_fact = memory_handler.facts[1]

        # Response should be JSON with annotation
        data = json.loads(response_fact["value"])
        assert data["response"] == "AI is..."
        assert data["source"]["model"] == "gpt-4"
        assert data["source"]["cost"] == 0.03

        # Should have annotated tag
        assert "annotated" in response_fact["tags"]
        assert "openai" in response_fact["tags"]

    def test_store_with_metadata(self, pasteback_handler, memory_handler):
        """Should store response with metadata."""
        pasteback_handler.store_with_metadata(
            thread_id="test_thread",
            prompt="What is AI?",
            response="AI is...",
            model="gpt-4",
            provider="openai",
            url="https://chat.openai.com",
            cost=0.03,
            tokens=500,
            metadata={"session_id": "abc123"},
        )

        response_fact = memory_handler.facts[1]

        data = json.loads(response_fact["value"])
        assert data["source"]["url"] == "https://chat.openai.com"
        assert data["source"]["metadata"]["session_id"] == "abc123"

    def test_get_annotated_responses(self, pasteback_handler, memory_handler):
        """Should retrieve annotated responses."""
        # Store some annotated responses
        annotation1 = SourceAnnotation(model="gpt-4", provider="openai", cost=0.03)
        annotation2 = SourceAnnotation(model="claude-3", provider="anthropic", cost=0.05)

        pasteback_handler.store(
            "test_thread", "Question 1", "Answer 1", "gpt-4", annotation1
        )
        pasteback_handler.store(
            "test_thread", "Question 2", "Answer 2", "claude-3", annotation2
        )

        # Retrieve responses
        responses = pasteback_handler.get_annotated_responses("test_thread", memory_handler)

        assert len(responses) == 2
        assert responses[0]["response"] == "Answer 1"
        assert responses[0]["source"].model == "gpt-4"
        assert responses[1]["response"] == "Answer 2"
        assert responses[1]["source"].model == "claude-3"

    def test_get_annotated_responses_filters_non_annotated(
        self, pasteback_handler, memory_handler
    ):
        """Should only return annotated responses."""
        # Store one annotated and one plain response
        annotation = SourceAnnotation(model="gpt-4")

        pasteback_handler.store("test_thread", "Q1", "A1", "gpt-4", annotation)
        pasteback_handler.store("test_thread", "Q2", "A2", "gpt-3.5")  # No annotation

        responses = pasteback_handler.get_annotated_responses("test_thread", memory_handler)

        # Should only get the annotated one
        assert len(responses) == 1
        assert responses[0]["response"] == "A1"

    def test_store_preserves_identity(self, pasteback_handler, memory_handler):
        """Should preserve model as identity."""
        pasteback_handler.store("test_thread", "prompt", "response", model="custom-model")

        prompt_fact = memory_handler.facts[0]
        response_fact = memory_handler.facts[1]

        assert prompt_fact["identity"] == "custom-model"
        assert response_fact["identity"] == "custom-model"

    def test_store_adds_tags(self, pasteback_handler, memory_handler):
        """Should add appropriate tags."""
        annotation = SourceAnnotation(model="gpt-4", provider="openai")

        pasteback_handler.store("test_thread", "p", "r", "gpt-4", annotation)

        prompt_fact = memory_handler.facts[0]
        response_fact = memory_handler.facts[1]

        assert "cloud" in prompt_fact["tags"]
        assert "prompt" in prompt_fact["tags"]
        assert "remote" in prompt_fact["tags"]

        assert "cloud" in response_fact["tags"]
        assert "response" in response_fact["tags"]
        assert "annotated" in response_fact["tags"]
        assert "openai" in response_fact["tags"]
