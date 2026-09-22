import time
import requests
from typing import List, Dict, Any, Optional
from src.ports.outbound.notion_client_port import INotionClient

NOTION_API_BASE = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"
SLEEP_NOTION_BATCH = 0.4

_CONTAINER_TYPES = {
    "column_list", "column", "toggle", "callout",
    "bulleted_list_item", "numbered_list_item", "quote",
    "synced_block", "template", "table",
}

class NotionApiAdapter(INotionClient):
    """
    Adapter for interacting with Notion REST API v1.
    Adheres strictly to Notion rate limits, batch constraints (100 blocks), and pagination.
    """
    def __init__(self, token: str):
        self.token = token

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Notion-Version": NOTION_VERSION,
        }

    def _fetch_children(self, parent_id: str) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        params: Dict[str, Any] = {"page_size": 100}
        url: Optional[str] = f"{NOTION_API_BASE}/blocks/{parent_id}/children"

        while url:
            r = requests.get(url, headers=self._headers(), params=params, timeout=30)
            r.raise_for_status()
            data = r.json()
            results.extend(data.get("results", []))
            if data.get("has_more"):
                params = {"page_size": 100, "start_cursor": data["next_cursor"]}
            else:
                url = None
        return results

    def fetch_courses(self, root_page_id: str) -> List[Dict[str, Any]]:
        """Queries course pages from the root Courses database or page."""
        results: List[Dict[str, Any]] = []
        payload: Dict[str, Any] = {"page_size": 100}
        url: Optional[str] = f"{NOTION_API_BASE}/databases/{root_page_id}/query"

        try:
            while url:
                r = requests.post(url, headers=self._headers(), json=payload, timeout=30)
                r.raise_for_status()
                data = r.json()
                for page in data.get("results", []):
                    title = "Senza titolo"
                    for prop in page.get("properties", {}).values():
                        if prop.get("type") == "title":
                            parts = prop.get("title", [])
                            if parts:
                                title = parts[0].get("plain_text", "Senza titolo")
                            break
                    results.append({"id": page["id"], "title": title})
                if data.get("has_more"):
                    payload = {"page_size": 100, "start_cursor": data["next_cursor"]}
                else:
                    url = None
        except requests.HTTPError as exc:
            # Fallback if root_page_id is a Page instead of a Database
            if exc.response is not None and exc.response.status_code == 400:
                children = self._fetch_children(root_page_id)
                for b in children:
                    if b.get("type") == "child_page":
                        results.append({
                            "id": b["id"],
                            "title": b.get("child_page", {}).get("title", "Senza titolo")
                        })
            else:
                raise exc

        return results

    def _fetch_database_title(self, database_id: str) -> str:
        try:
            r = requests.get(
                f"{NOTION_API_BASE}/databases/{database_id}",
                headers=self._headers(),
                timeout=30,
            )
            r.raise_for_status()
            data = r.json()
            parts = data.get("title", [])
            return parts[0].get("plain_text", "") if parts else ""
        except Exception:
            return ""

    def fetch_targets_in_course(self, course_id: str, _depth: int = 0) -> List[Dict[str, Any]]:
        if _depth > 4:
            return []
        items: List[Dict[str, Any]] = []
        for b in self._fetch_children(course_id):
            btype = b.get("type")
            if btype == "child_database":
                db_id = b["id"]
                title = b.get("child_database", {}).get("title", "").strip()
                if not title:
                    title = self._fetch_database_title(db_id)
                items.append({"id": db_id, "title": title or "Senza titolo", "kind": "database"})
            elif btype == "child_page":
                items.append({
                    "id": b["id"],
                    "title": b.get("child_page", {}).get("title", "Senza titolo"),
                    "kind": "page",
                })
            elif btype in _CONTAINER_TYPES and b.get(btype, {}).get("has_children") is not False:
                nested = self.fetch_targets_in_course(b["id"], _depth + 1)
                items.extend(nested)
        return items

    def resolve_database_id(self, target: Dict[str, Any]) -> str:
        if target["kind"] == "database":
            return target["id"]
        # Search inner database inside page
        inner = [
            b for b in self._fetch_children(target["id"])
            if b.get("type") == "child_database"
        ]
        if not inner:
            raise RuntimeError(
                f"Nessun database trovato dentro la pagina '{target['title']}'. "
                "Assicurati che contenga un database inline."
            )
        return inner[0]["id"]

    def page_exists(self, database_id: str, title: str) -> bool:
        r = requests.post(
            f"{NOTION_API_BASE}/databases/{database_id}/query",
            headers=self._headers(),
            json={"filter": {"property": "Name", "title": {"equals": title}}},
            timeout=30,
        )
        r.raise_for_status()
        return len(r.json().get("results", [])) > 0

    def create_page(self, database_id: str, title: str) -> str:
        r = requests.post(
            f"{NOTION_API_BASE}/pages",
            headers=self._headers(),
            json={
                "parent": {"database_id": database_id},
                "properties": {
                    "Name": {"title": [{"type": "text", "text": {"content": title}}]}
                },
            },
            timeout=30,
        )
        r.raise_for_status()
        return r.json()["id"]

    def append_blocks(self, page_id: str, blocks: List[Dict[str, Any]]) -> None:
        for i in range(0, len(blocks), 100):
            batch = blocks[i:i + 100]
            r = requests.patch(
                f"{NOTION_API_BASE}/blocks/{page_id}/children",
                headers=self._headers(),
                json={"children": batch},
                timeout=30,
            )
            r.raise_for_status()
            time.sleep(SLEEP_NOTION_BATCH)

    def archive_page(self, page_id: str) -> None:
        try:
            r = requests.patch(
                f"{NOTION_API_BASE}/pages/{page_id}",
                headers=self._headers(),
                json={"archived": True},
                timeout=30,
            )
            r.raise_for_status()
        except Exception as exc:
            print(f"    [ATTENZIONE] Impossibile archiviare la pagina orfana {page_id}: {exc}")
