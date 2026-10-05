"""
test_web_adapter.py
-------------------
Unit tests for the Inbound Web Adapter and TelemetryStreamer.
Verifies HTTP endpoints, profile management, file scanning, and telemetry event bus offline with mocks.
"""
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
from src.adapters.inbound.web.telemetry_streamer import TelemetryStreamer

@pytest.fixture
def anyio_backend():
    return "asyncio"

@pytest.fixture
def mock_dependencies(tmp_path):
    notion_client = MagicMock(spec=INotionClient)
    llm_client = MagicMock(spec=ILlmClient)
    llm_client.get_remaining_calls.return_value = 750
    llm_client.model = "gemini-2.5-flash"

    usecase = MagicMock(spec=ProcessDocumentUseCase)
    repo = MagicMock(spec=ICourseProfileRepository)
    state_repo = MagicMock(spec=IStateRepository)

    course_folder = tmp_path / "slides_test"
    course_folder.mkdir()
    (course_folder / "lecture_01.pdf").write_bytes(b"%PDF-1.4 sample content")
    (course_folder / "slides_02.pptx").write_bytes(b"PK sample presentation")

    sample_profile = CourseProfile(
        subject="Enterprise Architecture",
        professor_type="PhD Professor in Enterprise Architecture",
        doc_type=DocumentType.SLIDES,
        folder_path=course_folder,
        target=NotionTarget(
            database_id="db_ea_123",
            course_name="Enterprise Architecture",
            database_title="Notes",
        ),
    )
    repo.list_profiles.return_value = [sample_profile]
    state_repo.get_entry.return_value = None

    adapter = WebAdapter(
        notion_client=notion_client,
        llm_client=llm_client,
        usecase=usecase,
        root_page_id="root_notion_page",
        course_profile_repo=repo,
        state_repo=state_repo,
    )

    return {
        "adapter": adapter,
        "repo": repo,
        "state_repo": state_repo,
        "llm_client": llm_client,
        "folder": course_folder,
        "profile": sample_profile,
    }

@pytest.mark.anyio
async def test_web_adapter_serves_index(mock_dependencies):
    adapter = mock_dependencies["adapter"]
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=adapter.app), base_url="http://testserver") as client:
        response = await client.get("/")
        assert response.status_code == 200
        assert "PHD Prof Cockpit" in response.text
        assert "text/html" in response.headers["content-type"]

@pytest.mark.anyio
async def test_web_adapter_get_profiles(mock_dependencies):
    adapter = mock_dependencies["adapter"]
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=adapter.app), base_url="http://testserver") as client:
        response = await client.get("/api/profiles")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["subject"] == "Enterprise Architecture"
        assert data[0]["files_count"] == 2
        assert data[0]["key"] == "enterprise_architecture"

@pytest.mark.anyio
async def test_web_adapter_get_quota(mock_dependencies):
    adapter = mock_dependencies["adapter"]
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=adapter.app), base_url="http://testserver") as client:
        response = await client.get("/api/quota")
        assert response.status_code == 200
        data = response.json()
        assert data["remaining"] == 750
        assert data["model"] == "gemini-2.5-flash"
        assert data["is_exhausted"] is False

@pytest.mark.anyio
async def test_web_adapter_get_profile_files(mock_dependencies):
    adapter = mock_dependencies["adapter"]
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=adapter.app), base_url="http://testserver") as client:
        response = await client.get("/api/profiles/enterprise_architecture/files")
        assert response.status_code == 200
        data = response.json()
        assert "files" in data
        assert len(data["files"]) == 2
        file_names = [f["name"] for f in data["files"]]
        assert "lecture_01.pdf" in file_names
        assert "slides_02.pptx" in file_names
        assert all(f["status"] == "IDLE" for f in data["files"])

@pytest.mark.anyio
async def test_web_adapter_save_profile_valid(mock_dependencies, tmp_path):
    adapter = mock_dependencies["adapter"]
    repo = mock_dependencies["repo"]

    new_folder = tmp_path / "new_course"
    new_folder.mkdir()

    payload = {
        "subject": "Deep Learning",
        "professor_type": "PhD Professor in AI",
        "doc_type": "slides",
        "folder_path": str(new_folder),
        "target": {
            "database_id": "db_dl_999",
            "course_name": "Deep Learning",
            "database_title": "Notes",
        },
    }

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=adapter.app), base_url="http://testserver") as client:
        response = await client.post("/api/profiles", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["key"] == "deep_learning"
        repo.save_profile.assert_called_once()
        saved = repo.save_profile.call_args[0][0]
        assert saved.subject == "Deep Learning"
        assert saved.target.database_id == "db_dl_999"

@pytest.mark.anyio
async def test_web_adapter_save_profile_invalid_folder(mock_dependencies):
    adapter = mock_dependencies["adapter"]
    payload = {
        "subject": "Ghost Course",
        "professor_type": "",
        "doc_type": "slides",
        "folder_path": "C:\\non_existent_folder_path_12345",
        "target": {
            "database_id": "db_000",
            "course_name": "Ghost",
            "database_title": "Notes",
        },
    }
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=adapter.app), base_url="http://testserver") as client:
        response = await client.post("/api/profiles", json=payload)
        assert response.status_code == 400
        assert "Folder does not exist" in response.json()["detail"]

def test_telemetry_streamer_log_and_history():
    streamer = TelemetryStreamer(buffer_size=10)
    streamer.log("Test initial message", source="sys")
    streamer.log("[LLM] Generating study notes...")
    streamer.log("[Notion] Block created")

    history = streamer.get_history()
    assert len(history) == 3
    assert history[0]["data"]["message"] == "Test initial message"
    assert history[1]["data"]["source"] == "llm"
    assert history[1]["data"]["message"] == "Generating study notes..."
    assert history[2]["data"]["source"] == "notion"

def test_telemetry_streamer_capture_stdout():
    streamer = TelemetryStreamer(buffer_size=10)
    with streamer.capture_stdout(source="etl"):
        print("    [Local] File gia sincronizzato — skip.")
        print("    [Notion] OK — 211 blocchi archiviati.")

    history = streamer.get_history()
    assert len(history) >= 2
    sources = [h["data"]["source"] for h in history]
    assert "local" in sources
    assert "notion" in sources

@pytest.mark.anyio
async def test_web_adapter_heartbeat_and_unload(mock_dependencies):
    adapter = mock_dependencies["adapter"]
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=adapter.app), base_url="http://testserver") as client:
        # Test heartbeat
        hb_res = await client.post("/api/heartbeat")
        assert hb_res.status_code == 200
        assert hb_res.json()["status"] == "alive"

        # Test unload
        unload_res = await client.post("/api/unload")
        assert unload_res.status_code == 200
        assert unload_res.json()["status"] == "acknowledged"

def test_web_adapter_default_port_is_80(mock_dependencies):
    adapter = mock_dependencies["adapter"]
    assert adapter.port == 80
    assert adapter.host == "127.0.0.1"

def test_web_adapter_ssl_configuration(mock_dependencies):
    ssl_adapter = WebAdapter(
        notion_client=mock_dependencies["adapter"].notion_client,
        llm_client=mock_dependencies["adapter"].llm_client,
        usecase=mock_dependencies["adapter"].usecase,
        root_page_id="root_id",
        host="127.0.0.1",
        port=443,
        ssl_keyfile="certs/server.key",
        ssl_certfile="certs/server.crt",
    )
    assert ssl_adapter.port == 443
    assert ssl_adapter.ssl_keyfile == "certs/server.key"
    assert ssl_adapter.ssl_certfile == "certs/server.crt"


