import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from src.core.domain.models import CourseProfile
from src.ports.outbound.course_profile_repository_port import ICourseProfileRepository

class JsonCourseProfileRepository(ICourseProfileRepository):
    """
    Adapter for storing and retrieving CourseProfile entities from a local JSON file.
    Provides fast lookup, listing, atomic updates, and fallback defaults.
    """
    def __init__(self, file_path: Path):
        self.file_path = file_path

    def _load_data(self) -> Dict[str, Any]:
        if self.file_path.exists():
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if content:
                        return json.loads(content)
            except Exception:
                pass
        return {}

    def _save_data(self, data: Dict[str, Any]) -> None:
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        temp_file = self.file_path.with_suffix(".tmp")
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        temp_file.replace(self.file_path)

    def list_profiles(self) -> List[CourseProfile]:
        data = self._load_data()
        profiles = []
        for key, item in data.items():
            try:
                profiles.append(CourseProfile.from_dict(item))
            except Exception:
                continue
        return sorted(profiles, key=lambda p: p.subject.lower())

    def get_profile(self, subject_or_key: str) -> Optional[CourseProfile]:
        data = self._load_data()
        norm = subject_or_key.strip().lower().replace(" ", "_")
        if norm in data:
            try:
                return CourseProfile.from_dict(data[norm])
            except Exception:
                return None

        # Fallback to matching subject directly
        target_name = subject_or_key.strip().lower()
        for key, item in data.items():
            if item.get("subject", "").strip().lower() == target_name:
                try:
                    return CourseProfile.from_dict(item)
                except Exception:
                    return None
        return None

    def save_profile(self, profile: CourseProfile) -> None:
        data = self._load_data()
        data[profile.key] = profile.to_dict()
        self._save_data(data)

    def delete_profile(self, subject_or_key: str) -> bool:
        data = self._load_data()
        norm = subject_or_key.strip().lower().replace(" ", "_")
        key_to_delete = None
        if norm in data:
            key_to_delete = norm
        else:
            target_name = subject_or_key.strip().lower()
            for key, item in data.items():
                if item.get("subject", "").strip().lower() == target_name:
                    key_to_delete = key
                    break

        if key_to_delete:
            del data[key_to_delete]
            self._save_data(data)
            return True
        return False
