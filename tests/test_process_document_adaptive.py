from unittest.mock import MagicMock
from pathlib import Path
from src.core.domain.models import (
    Document,
    DocumentType,
    SyncStatus,
    SyncEntry,
    NotionTarget,
    StudyArtifact,
)
from src.core.usecases.process_document import ProcessDocumentUseCase
from src.ports.outbound.document_reader_port import IDocumentReader
from src.ports.outbound.llm_client_port import ILlmClient
from src.ports.outbound.notion_client_port import INotionClient
from src.ports.outbound.state_repository_port import IStateRepository
from src.ports.outbound.staging_storage_port import IStagingStorage
from src.ports.outbound.study_schema_exporter_port import IStudySchemaExporter

def test_process_document_adaptive_single_call():
    """
    Volume moderato (< threshold): Esegue esattamente 1 chiamata a Gemini (Single-Call).
    """
    state_repo = MagicMock(spec=IStateRepository)
    state_repo.get_entry.return_value = None

    staging_storage = MagicMock(spec=IStagingStorage)
    staging_storage.exists.return_value = False

    reader = MagicMock(spec=IDocumentReader)
    # 20 slide -> under threshold (default 50)
    reader.read.return_value = ["Slide 1", "Slide 2"] * 10

    llm_client = MagicMock(spec=ILlmClient)
    llm_client.generate_notes.return_value = "# Lecture Notes\nContent"

    notion_client = MagicMock(spec=INotionClient)
    notion_client.create_page.return_value = "page_1"

    schema_exporter = MagicMock(spec=IStudySchemaExporter)
    schema_exporter.extract_artifacts.return_value = StudyArtifact(
        document_hash="hash_small",
        title="Small",
        opml_content="<opml></opml>",
    )

    usecase = ProcessDocumentUseCase(
        readers={DocumentType.SLIDES: reader},
        llm_client=llm_client,
        notion_client=notion_client,
        state_repo=state_repo,
        staging_storage=staging_storage,
        schema_exporter=schema_exporter,
        split_threshold_slides=50,
    )

    doc = Document(path=Path("small.pptx"), file_hash="hash_small", doc_type=DocumentType.SLIDES)
    target = NotionTarget(database_id="db1", course_name="Micro", database_title="Notes")

    res = usecase.execute(doc, target, "prompt")

    assert res.success is True
    # EXACTLY 1 call to generate_notes!
    assert llm_client.generate_notes.call_count == 1
    schema_exporter.extract_artifacts.assert_called_once()


def test_process_document_adaptive_two_stage():
    """
    Volume elevato (>= threshold): Esegue 2 chiamate a Gemini (Two-Stage Decoupled).
    Call 1: Note analitiche
    Call 2: Estrazione schemi e drills dal markdown prodotto
    """
    state_repo = MagicMock(spec=IStateRepository)
    state_repo.get_entry.return_value = None

    staging_storage = MagicMock(spec=IStagingStorage)
    staging_storage.exists.return_value = False

    reader = MagicMock(spec=IDocumentReader)
    # 60 slide -> exceeds threshold (50)
    reader.read.return_value = ["Dense Slide content"] * 60

    llm_client = MagicMock(spec=ILlmClient)
    llm_client.generate_notes.side_effect = [
        "# Chapter 1: Extensive Lecture\nDeep analysis of estimators.", # Stage 1
        "## 🧠 Conceptual Architecture\n```mermaid\nmindmap\nroot((Deep))\n```", # Stage 2
    ]

    notion_client = MagicMock(spec=INotionClient)
    notion_client.create_page.return_value = "page_heavy"

    schema_exporter = MagicMock(spec=IStudySchemaExporter)
    schema_exporter.extract_artifacts.return_value = StudyArtifact(
        document_hash="hash_heavy",
        title="Heavy",
        opml_content="<opml></opml>",
    )

    usecase = ProcessDocumentUseCase(
        readers={DocumentType.SLIDES: reader},
        llm_client=llm_client,
        notion_client=notion_client,
        state_repo=state_repo,
        staging_storage=staging_storage,
        schema_exporter=schema_exporter,
        split_threshold_slides=50,
    )

    doc = Document(path=Path("heavy.pptx"), file_hash="hash_heavy", doc_type=DocumentType.SLIDES)
    target = NotionTarget(database_id="db1", course_name="Econometrics", database_title="Notes")

    res = usecase.execute(doc, target, "prompt")

    assert res.success is True
    # EXACTLY 2 calls to generate_notes!
    assert llm_client.generate_notes.call_count == 2
    # Verify both notes and artifacts were saved to staging
    saved_markdown = staging_storage.save.call_args[0][1]
    assert "Chapter 1: Extensive Lecture" in saved_markdown
    assert "Conceptual Architecture" in saved_markdown
    schema_exporter.extract_artifacts.assert_called_once()
