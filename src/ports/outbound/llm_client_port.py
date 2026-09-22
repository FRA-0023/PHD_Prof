from abc import ABC, abstractmethod
from typing import Any

class ILlmClient(ABC):
    """
    Port for interacting with the LLM provider (e.g. Google Gemini).
    """
    @abstractmethod
    def generate_notes(self, prompt: str, content_payload: Any) -> str:
        """
        Generates study notes given a prompt and the document content payload.
        Handles retry backoff and rate limit tracking.
        """
        pass

    @abstractmethod
    def get_remaining_calls(self) -> int:
        """Returns the number of remaining daily API calls."""
        pass
