from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Union
from src.core.domain.models import Document

class IDocumentReader(ABC):
    """
    Port for reading document content from disk.
    Implementations may upload to Gemini File API (multimodal) or extract local Markdown/Text.
    """
    @abstractmethod
    def read(self, document: Document) -> Any:
        """
        Processes the document file and returns an object suitable for the LLM client
        (e.g., a genai_types.File instance or extracted raw text string).
        """
        pass

    @abstractmethod
    def cleanup(self, payload: Any) -> None:
        """
        Cleans up temporary resources (e.g. deleting remote files from Gemini File API).
        """
        pass
