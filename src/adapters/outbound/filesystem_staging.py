from pathlib import Path
from typing import Optional
from src.ports.outbound.staging_storage_port import IStagingStorage

class FileSystemStaging(IStagingStorage):
    """
    Adapter that stores raw LLM-generated markdown on the local filesystem.
    Trade-off: Writing to disk before calling Notion API introduces a minimal I/O overhead
    (~2ms) but completely guarantees zero token waste if the network drops during Notion ingestion.
    """
    def __init__(self, staging_dir: Path):
        self.staging_dir = staging_dir
        self.staging_dir.mkdir(parents=True, exist_ok=True)

    def _get_path(self, file_hash: str) -> Path:
        return self.staging_dir / f"{file_hash}.md"

    def exists(self, file_hash: str) -> bool:
        return self._get_path(file_hash).exists()

    def read(self, file_hash: str) -> Optional[str]:
        target = self._get_path(file_hash)
        if target.exists():
            return target.read_text(encoding="utf-8")
        return None

    def save(self, file_hash: str, content: str) -> None:
        target = self._get_path(file_hash)
        target.write_text(content, encoding="utf-8")
