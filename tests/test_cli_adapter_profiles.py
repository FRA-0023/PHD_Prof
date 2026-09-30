import pytest
from pathlib import Path
from unittest.mock import MagicMock
from src.core.domain.models import CourseProfile, DocumentType, NotionTarget
from src.adapters.inbound.cli_adapter import CLIAdapter
from src.ports.outbound.notion_client_port import INotionClient
from src.ports.outbound.llm_client_port import ILlmClient
from src.ports.outbound.course_profile_repository_port import ICourseProfileRepository
from src.core.usecases.process_document import ProcessDocumentUseCase

@pytest.fixture
def mock_clients():
    notion_client = MagicMock(spec=INotionClient)
    llm_client = MagicMock(spec=ILlmClient)
    usecase = MagicMock(spec=ProcessDocumentUseCase)
    repo = MagicMock(spec=ICourseProfileRepository)
    return notion_client, llm_client, usecase, repo

def test_cli_adapter_setup_session_uses_saved_profile(mock_clients, monkeypatch, tmp_path):
    notion_client, llm_client, usecase, repo = mock_clients

    # Create dummy folder with a dummy slide
    course_folder = tmp_path / "slides"
    course_folder.mkdir()
    (course_folder / "lecture1.pdf").write_bytes(b"%PDF dummy")

    saved_profile = CourseProfile(
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
    repo.list_profiles.return_value = [saved_profile]

    # User inputs: "1" to pick profile, "" (Enter) to confirm
    inputs = iter(["1", ""])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

    cli = CLIAdapter(
        notion_client=notion_client,
        llm_client=llm_client,
        usecase=usecase,
        root_page_id="root_123",
        course_profile_repo=repo,
    )

    folder, doc_type, target, prompt = cli.setup_session()

    assert folder == course_folder
    assert doc_type == DocumentType.SLIDES
    assert target.database_id == "db_ea_123"
    assert target.course_name == "Enterprise Architecture"
    assert "Enterprise Architecture" in prompt
    # Verifies zero network discovery calls to Notion!
    notion_client.fetch_courses.assert_not_called()

def test_cli_adapter_setup_session_modifies_profile(mock_clients, monkeypatch, tmp_path):
    notion_client, llm_client, usecase, repo = mock_clients

    course_folder = tmp_path / "slides"
    course_folder.mkdir()
    (course_folder / "lecture1.pdf").write_bytes(b"%PDF dummy")

    saved_profile = CourseProfile(
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
    repo.list_profiles.return_value = [saved_profile]

    # User inputs:
    # "1": choose profile
    # "m": choose modify
    # "": keep subject
    # "Visiting Professor": new professor type
    # "2": switch to PAPER_OR_BOOK
    # "": keep folder
    # "n": do not reconfigure Notion
    # "s": save changes
    inputs = iter(["1", "m", "", "Visiting Professor", "2", "", "n", "s"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

    cli = CLIAdapter(
        notion_client=notion_client,
        llm_client=llm_client,
        usecase=usecase,
        root_page_id="root_123",
        course_profile_repo=repo,
    )

    folder, doc_type, target, prompt = cli.setup_session()

    assert doc_type == DocumentType.PAPER_OR_BOOK
    assert "Enterprise Architecture" in prompt
    repo.save_profile.assert_called_once()
    saved_arg = repo.save_profile.call_args[0][0]
    assert saved_arg.professor_type == "Visiting Professor"
    assert saved_arg.doc_type == DocumentType.PAPER_OR_BOOK

def test_cli_adapter_manual_setup_saves_new_profile(mock_clients, monkeypatch, tmp_path):
    notion_client, llm_client, usecase, repo = mock_clients

    # No saved profiles
    repo.list_profiles.return_value = []

    course_folder = tmp_path / "tm_docs"
    course_folder.mkdir()
    (course_folder / "tm1.pptx").write_bytes(b"dummy pptx")

    # Mock navigate_to_target
    target = NotionTarget(database_id="db_tm_456", course_name="Text Mining", database_title="Notes")
    cli = CLIAdapter(
        notion_client=notion_client,
        llm_client=llm_client,
        usecase=usecase,
        root_page_id="root_123",
        course_profile_repo=repo,
    )
    monkeypatch.setattr(cli, "navigate_to_target", lambda s: target)

    # Inputs:
    # "Text Mining": subject
    # "": default professor
    # "1": slides
    # str(course_folder): folder
    # "s": save profile choice
    inputs = iter(["Text Mining", "", "1", str(course_folder), "s"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

    folder, doc_type, out_target, prompt = cli.setup_session()

    assert folder == course_folder
    assert doc_type == DocumentType.SLIDES
    assert out_target.database_id == "db_tm_456"
    repo.save_profile.assert_called_once()
    saved = repo.save_profile.call_args[0][0]
    assert saved.subject == "Text Mining"
    assert saved.target.database_id == "db_tm_456"
