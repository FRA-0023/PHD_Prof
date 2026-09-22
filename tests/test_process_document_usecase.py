from unittest.mock import MagicMock
from pathlib import Path
from src.core.domain.models import (
    Document,
    DocumentType,
    SyncStatus,
    SyncEntry,
    NotionTarget,
)
from src.core.usecases.process_document import ProcessDocumentUseCase
from src.ports.outbound.document_reader_port import IDocumentReader
from src.ports.outbound.llm_client_port import ILlmClient
from src.ports.outbound.notion_client_port import INotionClient
from src.ports.outbound.state_repository_port import IStateRepository
from src.ports.outbound.staging_storage_port import IStagingStorage

def test_process_document_already_synced():
    state_repo = MagicMock(spec=IStateRepository)
    state_repo.get_entry.return_value = SyncEntry(file_hash="hash_1", status=SyncStatus.SYNCED, page_id="p1")

    usecase = ProcessDocumentUseCase(
        readers={},
        llm_client=MagicMock(spec=ILlmClient),
        notion_client=MagicMock(spec=INotionClient),
        state_repo=state_repo,
        staging_storage=MagicMock(spec=IStagingStorage),
    )

    doc = Document(path=Path("sample.pdf"), file_hash="hash_1", doc_type=DocumentType.SLIDES)
    target = NotionTarget(database_id="db1", course_name="Math", database_title="Notes")

    res = usecase.execute(doc, target, "prompt")
    assert res.success is True
    assert res.skipped is True
    assert res.page_id == "p1"

def test_process_document_rollback_orphaned():
    state_repo = MagicMock(spec=IStateRepository)
    state_repo.get_entry.return_value = SyncEntry(file_hash="hash_1", status=SyncStatus.SYNCING, page_id="orphan_page")

    notion_client = MagicMock(spec=INotionClient)
    notion_client.create_page.return_value = "new_page_id"

    staging_storage = MagicMock(spec=IStagingStorage)
    staging_storage.exists.return_value = True
    staging_storage.read.return_value = "# Note"

    usecase = ProcessDocumentUseCase(
        readers={},
        llm_client=MagicMock(spec=ILlmClient),
        notion_client=notion_client,
        state_repo=state_repo,
        staging_storage=staging_storage,
    )

    doc = Document(path=Path("sample.pdf"), file_hash="hash_1", doc_type=DocumentType.SLIDES)
    target = NotionTarget(database_id="db1", course_name="Math", database_title="Notes")

    res = usecase.execute(doc, target, "prompt")

    # Verify rollback was called on the orphaned page
    notion_client.archive_page.assert_called_once_with("orphan_page")
    state_repo.remove_entry.assert_called_once_with("hash_1")

    # Verify new page was created and completed
    notion_client.create_page.assert_called_once_with("db1", "sample")
    assert res.success is True
    assert res.page_id == "new_page_id"

def test_process_document_full_flow():
    state_repo = MagicMock(spec=IStateRepository)
    state_repo.get_entry.return_value = None

    staging_storage = MagicMock(spec=IStagingStorage)
    staging_storage.exists.return_value = False

    reader = MagicMock(spec=IDocumentReader)
    reader.read.return_value = "raw_content"

    llm_client = MagicMock(spec=ILlmClient)
    llm_client.generate_notes.return_value = "# Generated Title\nBody"

    notion_client = MagicMock(spec=INotionClient)
    notion_client.create_page.return_value = "created_page_id"

    usecase = ProcessDocumentUseCase(
        readers={DocumentType.SLIDES: reader},
        llm_client=llm_client,
        notion_client=notion_client,
        state_repo=state_repo,
        staging_storage=staging_storage,
    )

    doc = Document(path=Path("lecture.pdf"), file_hash="hash_new", doc_type=DocumentType.SLIDES)
    target = NotionTarget(database_id="db_math", course_name="Math", database_title="Notes")

    res = usecase.execute(doc, target, "prompt")

    reader.read.assert_called_once_with(doc)
    llm_client.generate_notes.assert_called_once_with("prompt", "raw_content")
    reader.cleanup.assert_called_once_with("raw_content")
    staging_storage.save.assert_called_once_with("hash_new", "# Generated Title\nBody")
    notion_client.create_page.assert_called_once_with("db_math", "lecture")
    notion_client.append_blocks.assert_called_once()
    assert res.success is True
    assert res.page_id == "created_page_id"
