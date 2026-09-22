import tempfile
from pathlib import Path
from src.core.domain.models import SyncEntry, SyncStatus
from src.adapters.outbound.json_state_repository import JsonStateRepository
from src.adapters.outbound.filesystem_staging import FileSystemStaging

def test_json_state_repository_lifecycle():
    with tempfile.TemporaryDirectory() as tmpdir:
        state_file = Path(tmpdir) / "sync_state.json"
        usage_file = Path(tmpdir) / "gemini_usage.json"
        repo = JsonStateRepository(state_file=state_file, usage_file=usage_file)

        # Initially empty
        assert repo.get_entry("hash123") is None

        # Add entry
        entry = SyncEntry(file_hash="hash123", status=SyncStatus.SYNCING, page_id="page_abc")
        repo.set_entry(entry)

        retrieved = repo.get_entry("hash123")
        assert retrieved is not None
        assert retrieved.file_hash == "hash123"
        assert retrieved.status == SyncStatus.SYNCING
        assert retrieved.page_id == "page_abc"

        # Update entry to SYNCED
        entry.status = SyncStatus.SYNCED
        repo.set_entry(entry)
        assert repo.get_entry("hash123").status == SyncStatus.SYNCED

        # Remove entry (rollback)
        repo.remove_entry("hash123")
        assert repo.get_entry("hash123") is None

def test_json_state_repository_usage_tracking():
    with tempfile.TemporaryDirectory() as tmpdir:
        state_file = Path(tmpdir) / "sync_state.json"
        usage_file = Path(tmpdir) / "gemini_usage.json"
        repo = JsonStateRepository(state_file=state_file, usage_file=usage_file)

        assert repo.get_daily_usage() == 0
        repo.increment_daily_usage()
        repo.increment_daily_usage()
        assert repo.get_daily_usage() == 2

def test_filesystem_staging():
    with tempfile.TemporaryDirectory() as tmpdir:
        staging = FileSystemStaging(Path(tmpdir))
        file_hash = "abc123hash"

        assert not staging.exists(file_hash)
        assert staging.read(file_hash) is None

        staging.save(file_hash, "# Notes content\nLine 1")
        assert staging.exists(file_hash)
        assert staging.read(file_hash) == "# Notes content\nLine 1"
