from abc import ABC, abstractmethod
from typing import Optional, Dict
from src.core.domain.models import SyncEntry, SyncStatus

class IStateRepository(ABC):
    """
    Port for cryptographic state persistence (Crash-Only Idempotency & Usage Tracking).
    """
    @abstractmethod
    def get_entry(self, file_hash: str) -> Optional[SyncEntry]:
        """Retrieves a sync entry by its SHA-256 hash."""
        pass

    @abstractmethod
    def set_entry(self, entry: SyncEntry) -> None:
        """Persists a sync entry status."""
        pass

    @abstractmethod
    def remove_entry(self, file_hash: str) -> None:
        """Removes a sync entry (e.g. during rollback)."""
        pass

    @abstractmethod
    def get_daily_usage(self) -> int:
        """Retrieves LLM API usage count for today."""
        pass

    @abstractmethod
    def increment_daily_usage(self) -> int:
        """Increments and persists today's LLM usage count."""
        pass
