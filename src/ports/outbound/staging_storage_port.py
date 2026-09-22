from abc import ABC, abstractmethod
from typing import Optional

class IStagingStorage(ABC):
    """
    Port for decoupling LLM inference from Notion loading.
    Saves generated Markdown to local disk to ensure zero token waste on network drop.
    """
    @abstractmethod
    def exists(self, file_hash: str) -> bool:
        """Checks if generated markdown already exists in staging."""
        pass

    @abstractmethod
    def read(self, file_hash: str) -> Optional[str]:
        """Reads cached markdown from staging."""
        pass

    @abstractmethod
    def save(self, file_hash: str, content: str) -> None:
        """Persists generated markdown into staging."""
        pass
