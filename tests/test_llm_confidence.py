"""Tests for LLM confidence calculation."""

import pytest

from agent.llm_router import LLMRouter


class TestLLMConfidence:
    """Test confidence calculation for LLM responses."""

    def test_empty_response_returns_zero_confidence(self):
        """Empty responses should have zero confidence."""
        router = LLMRouter()
        confidence = router.calculate_confidence("", "what is the weather")
        assert confidence == 0.0

    def test_detailed_response_increases_confidence(self):
        """Longer, detailed responses should have higher confidence."""
        router = LLMRouter()
        short_response = "Yes."
        long_response = (
            "Yes, that's correct. The weather forecast indicates "
            "clear skies with temperatures ranging from 65-75°F "
            "throughout the week."
        )

        short_conf = router.calculate_confidence(short_response, "will it be sunny?")
        long_conf = router.calculate_confidence(long_response, "will it be sunny?")

        assert long_conf > short_conf

    def test_uncertain_language_decreases_confidence(self):
        """Responses with uncertain language should have lower confidence."""
        router = LLMRouter()
        certain_response = "The answer is 42."
        uncertain_response = "I'm not sure, but maybe the answer is 42."

        certain_conf = router.calculate_confidence(certain_response, "what is the answer")
        uncertain_conf = router.calculate_confidence(uncertain_response, "what is the answer")

        assert certain_conf > uncertain_conf

    def test_structured_content_increases_confidence(self):
        """Structured responses (lists, code) should have higher confidence."""
        router = LLMRouter()
        # Use responses with similar keywords but different structure
        plain_response = "The methods include option alpha, option beta, and option gamma for completion."
        structured_response = """The methods include:
        1. Option alpha
        2. Option beta
        3. Option gamma
        These provide completion."""

        plain_conf = router.calculate_confidence(plain_response, "what are the methods")
        structured_conf = router.calculate_confidence(structured_response, "what are the methods")

        assert structured_conf > plain_conf

    def test_error_messages_decrease_confidence(self):
        """Error messages should decrease confidence."""
        router = LLMRouter()
        success_response = "Here's the result you requested."
        error_response = "Sorry, I encountered an error processing your request."

        success_conf = router.calculate_confidence(success_response, "get result")
        error_conf = router.calculate_confidence(error_response, "get result")

        assert success_conf > error_conf

    def test_prompt_keyword_overlap_increases_confidence(self):
        """Responses that address prompt keywords should have higher confidence."""
        router = LLMRouter()
        prompt = "explain machine learning algorithms"
        relevant_response = "Machine learning algorithms include supervised learning techniques."
        irrelevant_response = "The weather is nice today."

        relevant_conf = router.calculate_confidence(relevant_response, prompt)
        irrelevant_conf = router.calculate_confidence(irrelevant_response, prompt)

        assert relevant_conf > irrelevant_conf

    def test_confidence_is_bounded(self):
        """Confidence should always be between 0.0 and 1.0."""
        router = LLMRouter()
        test_cases = [
            ("", "test"),
            ("short", "test"),
            ("a" * 1000, "test"),
            ("I'm not sure maybe possibly perhaps I think", "test"),
        ]

        for response, prompt in test_cases:
            confidence = router.calculate_confidence(response, prompt)
            assert 0.0 <= confidence <= 1.0
