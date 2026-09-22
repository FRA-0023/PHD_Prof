from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

class INotionClient(ABC):
    """
    Port for Notion API operations (navigation, page creation, block injection, rollback).
    """
    @abstractmethod
    def fetch_courses(self, root_page_id: str) -> List[Dict[str, Any]]:
        """Queries courses from the root Notion database or page."""
        pass

    @abstractmethod
    def fetch_targets_in_course(self, course_id: str) -> List[Dict[str, Any]]:
        """Recursively traverses course containers to find child databases or pages."""
        pass

    @abstractmethod
    def resolve_database_id(self, target: Dict[str, Any]) -> str:
        """Resolves target database ID, inspecting inner databases if target is a page."""
        pass

    @abstractmethod
    def page_exists(self, database_id: str, title: str) -> bool:
        """Checks if a page with the given title already exists in the target database."""
        pass

    @abstractmethod
    def create_page(self, database_id: str, title: str) -> str:
        """Creates an empty page in the target database and returns its new page ID."""
        pass

    @abstractmethod
    def append_blocks(self, page_id: str, blocks: List[Dict[str, Any]]) -> None:
        """Appends formatted blocks to a page, managing Notion's 100-block batch limit."""
        pass

    @abstractmethod
    def archive_page(self, page_id: str) -> None:
        """Archives (deletes) a page to perform clean rollbacks on failure."""
        pass
