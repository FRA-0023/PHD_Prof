from abc import ABC, abstractmethod
from typing import List, Optional
from src.core.domain.models import CourseProfile

class ICourseProfileRepository(ABC):
    """
    Port for managing persistent course configuration profiles.
    Allows quick one-click reuse of course parameters (subject, professor role, folder, Notion target).
    """

    @abstractmethod
    def list_profiles(self) -> List[CourseProfile]:
        """Returns all saved course profiles."""
        pass

    @abstractmethod
    def get_profile(self, subject_or_key: str) -> Optional[CourseProfile]:
        """Retrieves a course profile by name or key (case-insensitive)."""
        pass

    @abstractmethod
    def save_profile(self, profile: CourseProfile) -> None:
        """Saves or updates a course profile."""
        pass

    @abstractmethod
    def delete_profile(self, subject_or_key: str) -> bool:
        """Deletes a course profile if it exists."""
        pass
