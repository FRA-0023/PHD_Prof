import json
import datetime
from pathlib import Path
from typing import Optional
from src.core.domain.models import SyncEntry, SyncStatus
from src.ports.outbound.state_repository_port import IStateRepository

class JsonStateRepository(IStateRepository):
    """
    Persists cryptographic state and daily rate limits into JSON files.
    Ensures idempotency across batch executions and facilitates self-healing rollbacks.
    """
    def __init__(self, state_file: Path, usage_file: Path):
        self.state_file = state_file
        self.usage_file = usage_file

    def _load_state(self) -> dict:
        if self.state_file.exists():
            try:
                with open(self.state_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def _save_state(self, state: dict) -> None:
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)

    def get_entry(self, file_hash: str) -> Optional[SyncEntry]:
        state = self._load_state()
        data = state.get(file_hash)
        if not data:
            return None
        return SyncEntry(
            file_hash=file_hash,
            status=SyncStatus(data.get("status", SyncStatus.IDLE)),
            page_id=data.get("page_id"),
            last_updated=data.get("last_updated"),
        )

    def set_entry(self, entry: SyncEntry) -> None:
        state = self._load_state()
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        state[entry.file_hash] = {
            "status": entry.status.value,
            "page_id": entry.page_id,
            "last_updated": now,
        }
        self._save_state(state)

    def remove_entry(self, file_hash: str) -> None:
        state = self._load_state()
        if file_hash in state:
            del state[file_hash]
            self._save_state(state)

    def _load_usage(self) -> dict:
        if self.usage_file.exists():
            try:
                with open(self.usage_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"date": "", "count": 0}

    def _save_usage(self, data: dict) -> None:
        with open(self.usage_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def get_daily_usage(self) -> int:
        today = datetime.date.today().isoformat()
        usage = self._load_usage()
        if usage.get("date") == today:
            return usage.get("count", 0)
        return 0

    def increment_daily_usage(self) -> int:
        today = datetime.date.today().isoformat()
        usage = self._load_usage()
        if usage.get("date") != today:
            usage = {"date": today, "count": 0}
        usage["count"] += 1
        self._save_usage(usage)
        return usage["count"]
