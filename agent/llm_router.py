# axon/agent/llm_router.py

import requests
import json
from .fallback_prompt import generate_prompt, to_json

class LLMRouter:
    """
    Handles routing prompts to a local Ollama server.
    """
    def __init__(self, server_url: str = "http://192.168.1.148:11434/api/generate"):
        """
        Initializes the LLMRouter with the URL for the Ollama server.

        Args:
            server_url (str): The URL of the Ollama server's generate endpoint.
                              'host.docker.internal' is a special DNS name that
                              Docker containers can use to connect to the host machine.
        """
        self.server_url = server_url
        print(f"LLMRouter initialized to connect to Ollama at: {self.server_url}")

    def _needs_cloud(self, prompt: str) -> bool:
        """Simple heuristic to decide if a cloud model should be suggested."""

        return len(prompt) > 400

    def get_response(self, prompt: str, model: str) -> str:
        """
        Sends a prompt to the Ollama server and returns the response.

        Args:
            prompt (str): The user's prompt.
            model (str): The name of the model to use (e.g., 'mistral', 'llama2').
        """
        if self._needs_cloud(prompt):
            fallback = generate_prompt(prompt)
            return to_json(fallback)

        headers = {"Content-Type": "application/json"}
        data = {"model": model, "prompt": prompt, "stream": False}

        try:
            response = requests.post(self.server_url, headers=headers, data=json.dumps(data))
            response.raise_for_status()
            response_data = response.json()
            return response_data.get("response", "Sorry, I received an empty response from Ollama.").strip()

        except requests.exceptions.RequestException:
            fallback = generate_prompt(
                prompt,
                reason="Local model call failed; please use a cloud model.",
            )
            return to_json(fallback)
