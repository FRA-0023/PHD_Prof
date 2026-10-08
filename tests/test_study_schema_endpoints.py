import pytest
import httpx
from pathlib import Path
from unittest.mock import MagicMock

from src.core.domain.models import CourseProfile, DocumentType, NotionTarget
from src.ports.outbound.notion_client_port import INotionClient
from src.ports.outbound.llm_client_port import ILlmClient
from src.ports.outbound.course_profile_repository_port import ICourseProfileRepository
from src.ports.outbound.state_repository_port import IStateRepository
from src.core.usecases.process_document import ProcessDocumentUseCase
from src.adapters.inbound.web.web_adapter import WebAdapter

SAMPLE_STAGING_MD = """
# Chapter 1: Optimization
---
## 🧠 Conceptual Architecture & Relational Graphs
```mermaid
mindmap
  root((Optimization))
    Unconstrained
      Gradient Descent
    Constrained
      Lagrange Multipliers
```

```mermaid
graph TD
  KKT[KKT Conditions] --> Sol[Global Minimum]
```

---
## 🎯 Active Recall & Examination Drills
- **Drill 1:** Explain KKT complementary slackness.
  * **Rubric:** State $\\lambda_i g_i(x) = 0$.

---
## ⚖️ Model Boundary Conditions
| Model | Domain | Breakdown | Fix |
| :--- | :--- | :--- | :--- |
| Newton-Raphson | Convex | Saddle point | Damped Newton |
""".strip()

@pytest.fixture
def anyio_backend():
    return "asyncio"

@pytest.fixture
def web_adapter_instance(tmp_path):
    notion_client = MagicMock(spec=INotionClient)
    llm_client = MagicMock(spec=ILlmClient)
    usecase = MagicMock(spec=ProcessDocumentUseCase)
    repo = MagicMock(spec=ICourseProfileRepository)
    state_repo = MagicMock(spec=IStateRepository)

    adapter = WebAdapter(
        notion_client=notion_client,
        llm_client=llm_client,
        usecase=usecase,
        root_page_id="root_123",
        course_profile_repo=repo,
        state_repo=state_repo,
    )
    return adapter

@pytest.mark.anyio
async def test_get_study_schema_success(web_adapter_instance, tmp_path, monkeypatch):
    # Setup staging file
    staging_dir = Path("staging")
    staging_dir.mkdir(exist_ok=True)
    staging_file = staging_dir / "hash_test_123.md"
    staging_file.write_text(SAMPLE_STAGING_MD, encoding="utf-8")

    try:
        app = web_adapter_instance.app
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/study-schema/hash_test_123")
            assert resp.status_code == 200
            data = resp.json()
            assert data["file_hash"] == "hash_test_123"
            assert "mindmap" in data["mindmap_mermaid"]
            assert "graph TD" in data["flowchart_mermaid"]
            assert "Active Recall" in data["active_recall_markdown"]
            assert "Boundary Conditions" in data["boundary_matrix_markdown"]
            assert data["has_opml"] is True
    finally:
        if staging_file.exists():
            staging_file.unlink()

@pytest.mark.anyio
async def test_download_opml_success(web_adapter_instance):
    staging_dir = Path("staging")
    staging_dir.mkdir(exist_ok=True)
    staging_file = staging_dir / "hash_opml_456.md"
    staging_file.write_text(SAMPLE_STAGING_MD, encoding="utf-8")

    try:
        app = web_adapter_instance.app
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/study-schema/hash_opml_456/opml")
            assert resp.status_code == 200
            assert "application/xml" in resp.headers["content-type"]
            assert '<opml version="2.0">' in resp.text
            assert '<outline text="Optimization">' in resp.text
            assert '<outline text="Unconstrained">' in resp.text
    finally:
        if staging_file.exists():
            staging_file.unlink()

@pytest.mark.anyio
async def test_get_study_schema_404(web_adapter_instance):
    app = web_adapter_instance.app
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/study-schema/non_existent_hash")
        assert resp.status_code == 404
