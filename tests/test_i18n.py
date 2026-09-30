import pytest
from pathlib import Path
from unittest.mock import MagicMock
from src.adapters.inbound.i18n import I18n
from src.adapters.inbound.cli_adapter import CLIAdapter
from src.core.domain.models import CourseProfile, DocumentType, NotionTarget
from src.ports.outbound.notion_client_port import INotionClient
from src.ports.outbound.llm_client_port import ILlmClient
from src.ports.outbound.course_profile_repository_port import ICourseProfileRepository
from src.core.usecases.process_document import ProcessDocumentUseCase

def test_i18n_default_and_normalization():
    it = I18n()
    assert it.lang == "IT"

    en = I18n("en")
    assert en.lang == "EN"

    invalid = I18n("FR")
    assert invalid.lang == "IT"

def test_i18n_translation_and_formatting():
    it = I18n("IT")
    assert "Chiamate disponibili oggi: 5" == it.t("remaining_calls", count=5)

    en = I18n("EN")
    assert "Available API calls today: 5" == en.t("remaining_calls", count=5)

def test_i18n_fallback_on_unknown_key():
    it = I18n("IT")
    assert it.t("non_existent_key_xyz") == "non_existent_key_xyz"

def test_cli_adapter_english_mode(monkeypatch, tmp_path):
    notion_client = MagicMock(spec=INotionClient)
    llm_client = MagicMock(spec=ILlmClient)
    usecase = MagicMock(spec=ProcessDocumentUseCase)
    repo = MagicMock(spec=ICourseProfileRepository)

    course_folder = tmp_path / "en_slides"
    course_folder.mkdir()
    (course_folder / "slide1.pdf").write_bytes(b"%PDF dummy")

    saved_profile = CourseProfile(
        subject="Deep Learning",
        professor_type="PhD Professor in Deep Learning",
        doc_type=DocumentType.SLIDES,
        folder_path=course_folder,
        target=NotionTarget(database_id="db_dl", course_name="Deep Learning", database_title="Notes"),
    )
    repo.list_profiles.return_value = [saved_profile]

    # English affirmative input: "1" then "y" (or Enter)
    inputs = iter(["1", "y"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

    en_i18n = I18n("EN")
    cli = CLIAdapter(
        notion_client=notion_client,
        llm_client=llm_client,
        usecase=usecase,
        root_page_id="root_123",
        course_profile_repo=repo,
        i18n=en_i18n,
    )

    folder, doc_type, target, prompt = cli.setup_session()

    assert folder == course_folder
    assert doc_type == DocumentType.SLIDES
    assert target.database_id == "db_dl"
    assert cli.i18n.lang == "EN"
