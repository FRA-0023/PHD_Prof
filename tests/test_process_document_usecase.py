from unittest.mock import MagicMock
from pathlib import Path
from src.core.domain.models import (
    Document,
    DocumentType,
    SyncStatus,
    SyncEntry,
    NotionTarget,
    GenerationMode,
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

def test_process_document_pptx_slides_routing():
    state_repo = MagicMock(spec=IStateRepository)
    state_repo.get_entry.return_value = None

    staging_storage = MagicMock(spec=IStagingStorage)
    staging_storage.exists.return_value = False

    slides_reader = MagicMock(spec=IDocumentReader)
    slides_reader.read.return_value = MagicMock()
    text_reader = MagicMock(spec=IDocumentReader)

    llm_client = MagicMock(spec=ILlmClient)
    llm_client.generate_notes.return_value = "# PPTX Notes"

    notion_client = MagicMock(spec=INotionClient)
    notion_client.create_page.return_value = "p_pptx"

    usecase = ProcessDocumentUseCase(
        readers={
            DocumentType.SLIDES: slides_reader,
            DocumentType.PAPER_OR_BOOK: text_reader,
        },
        llm_client=llm_client,
        notion_client=notion_client,
        state_repo=state_repo,
        staging_storage=staging_storage,
    )

    doc = Document(path=Path("slides.pptx"), file_hash="pptx_hash", doc_type=DocumentType.SLIDES)
    target = NotionTarget(database_id="db1", course_name="EA", database_title="Notes")

    res = usecase.execute(doc, target, "prompt")

    # SLIDES doc_type with .pptx must route to slides_reader (GeminiFileReader)
    slides_reader.read.assert_called_once_with(doc)
    text_reader.read.assert_not_called()
    assert res.success is True
    assert res.page_id == "p_pptx"


def test_process_document_pptx_paper_routing():
    state_repo = MagicMock(spec=IStateRepository)
    state_repo.get_entry.return_value = None

    staging_storage = MagicMock(spec=IStagingStorage)
    staging_storage.exists.return_value = False

    slides_reader = MagicMock(spec=IDocumentReader)
    text_reader = MagicMock(spec=IDocumentReader)
    text_reader.read.return_value = "extracted pptx text"

    llm_client = MagicMock(spec=ILlmClient)
    llm_client.generate_notes.return_value = "# PPTX Paper Notes"

    notion_client = MagicMock(spec=INotionClient)
    notion_client.create_page.return_value = "p_pptx_paper"

    usecase = ProcessDocumentUseCase(
        readers={
            DocumentType.SLIDES: slides_reader,
            DocumentType.PAPER_OR_BOOK: text_reader,
        },
        llm_client=llm_client,
        notion_client=notion_client,
        state_repo=state_repo,
        staging_storage=staging_storage,
    )

    doc = Document(path=Path("deck.pptx"), file_hash="pptx_hash_paper", doc_type=DocumentType.PAPER_OR_BOOK)
    target = NotionTarget(database_id="db1", course_name="EA", database_title="Notes")

    res = usecase.execute(doc, target, "prompt")

    # PAPER_OR_BOOK doc_type with .pptx must route to text_reader (MarkItDown/python-pptx)
    text_reader.read.assert_called_once_with(doc)
    slides_reader.read.assert_not_called()
    assert res.success is True
    assert res.page_id == "p_pptx_paper"


def test_process_figures_skip_when_already_exists_on_remote():
    visual_extractor = MagicMock()
    image_host = MagicMock()
    image_host.image_exists.return_value = True
    image_host.get_public_url.return_value = "https://cdn.example.com/notion/universita/math/fig1.png"

    usecase = ProcessDocumentUseCase(
        readers={},
        llm_client=MagicMock(),
        notion_client=MagicMock(),
        state_repo=MagicMock(),
        staging_storage=MagicMock(),
        visual_extractor=visual_extractor,
        image_host_client=image_host,
    )

    doc = Document(path=Path("doc.pdf"), file_hash="hash_123", doc_type=DocumentType.SLIDES)
    target = NotionTarget(database_id="db1", course_name="Math", database_title="Notes")

    raw_markdown = "Text before\n![Diagram](figure://slide_10)\nText after"
    processed = usecase._process_figures(raw_markdown, doc, target)

    # Verifica che visual_extractor e upload_image siano stati saltati
    visual_extractor.extract_figure.assert_not_called()
    image_host.upload_image.assert_not_called()
    assert "https://cdn.example.com/notion/universita/math/fig1.png" in processed


def test_process_figures_skip_extraction_when_local_cached(tmp_path: Path, monkeypatch):
    visual_extractor = MagicMock()
    image_host = MagicMock()
    image_host.image_exists.return_value = False
    image_host.upload_image.return_value = "https://cdn.example.com/uploaded.png"

    # Redirige staging/figures su tmp_path
    figures_dir = tmp_path / "staging" / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.chdir(tmp_path)

    import hashlib
    doc = Document(path=Path("doc.pdf"), file_hash="hash_abc", doc_type=DocumentType.SLIDES)
    target = NotionTarget(database_id="db1", course_name="Math", database_title="Notes")

    # Pre-creiamo il file locale deterministico
    raw_sig = f"{doc.file_hash}_5_full"
    img_id = hashlib.sha256(raw_sig.encode("utf-8")).hexdigest()[:16]
    cached_file = figures_dir / f"{img_id}.png"
    cached_file.write_bytes(b"dummy_png_bytes")

    usecase = ProcessDocumentUseCase(
        readers={},
        llm_client=MagicMock(),
        notion_client=MagicMock(),
        state_repo=MagicMock(),
        staging_storage=MagicMock(),
        visual_extractor=visual_extractor,
        image_host_client=image_host,
    )

    raw_markdown = "![Chart](figure://slide_5)"
    processed = usecase._process_figures(raw_markdown, doc, target)

    # Estrazione PyMuPDF saltata perché il file PNG locale esisteva già
    visual_extractor.extract_figure.assert_not_called()
    # Ma upload eseguito perché su R2 non esisteva ancora
    image_host.upload_image.assert_called_once()
    assert "https://cdn.example.com/uploaded.png" in processed


def test_process_document_notes_only_mode():
    state_repo = MagicMock(spec=IStateRepository)
    state_repo.get_entry.return_value = None

    staging_storage = MagicMock(spec=IStagingStorage)
    staging_storage.exists.return_value = True
    full_markdown = (
        "# Big Data Notes\n\n"
        "Content paragraph about distributed systems.\n\n"
        "---\n\n"
        "## 🧠 Conceptual Architecture & Relational Graphs\n\n"
        "```mermaid\nmindmap\n  root((Architecture))\n```\n"
    )
    staging_storage.read.return_value = full_markdown

    schema_exporter = MagicMock()
    notion_client = MagicMock(spec=INotionClient)
    notion_client.create_page.return_value = "notes_page_id"

    usecase = ProcessDocumentUseCase(
        readers={},
        llm_client=MagicMock(spec=ILlmClient),
        notion_client=notion_client,
        state_repo=state_repo,
        staging_storage=staging_storage,
        schema_exporter=schema_exporter,
    )

    doc = Document(path=Path("big_data.pdf"), file_hash="hash_bd", doc_type=DocumentType.SLIDES)
    target = NotionTarget(database_id="db1", course_name="Big Data", database_title="Notes")

    res = usecase.execute(doc, target, "prompt", generation_mode=GenerationMode.NOTES_ONLY)

    assert res.success is True
    # In NOTES_ONLY, schema_exporter should NOT be called
    schema_exporter.extract_artifacts.assert_not_called()
    # In NOTES_ONLY, appended blocks should only contain notes, not the mermaid mindmap
    appended_blocks = notion_client.append_blocks.call_args[0][1]
    has_mermaid = any(b.get("type") == "code" and b.get("code", {}).get("language") == "mermaid" for b in appended_blocks)
    assert has_mermaid is False


def test_process_document_graphs_only_mode(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    state_repo = MagicMock(spec=IStateRepository)
    state_repo.get_entry.return_value = None

    staging_storage = MagicMock(spec=IStagingStorage)
    staging_storage.exists.return_value = True
    full_markdown = (
        "# Big Data Notes\n\n"
        "Content paragraph.\n\n"
        "---\n\n"
        "## 🧠 Conceptual Architecture & Relational Graphs\n\n"
        "```mermaid\nmindmap\n  root((Architecture))\n```\n"
    )
    staging_storage.read.return_value = full_markdown

    schema_exporter = MagicMock()
    mock_artifact = MagicMock()
    mock_artifact.opml_content = "<opml></opml>"
    schema_exporter.extract_artifacts.return_value = mock_artifact

    notion_client = MagicMock(spec=INotionClient)
    notion_client.create_page.return_value = "graphs_page_id"

    usecase = ProcessDocumentUseCase(
        readers={},
        llm_client=MagicMock(spec=ILlmClient),
        notion_client=notion_client,
        state_repo=state_repo,
        staging_storage=staging_storage,
        schema_exporter=schema_exporter,
    )

    doc = Document(path=Path("big_data.pdf"), file_hash="hash_bd2", doc_type=DocumentType.SLIDES)
    target = NotionTarget(database_id="db1", course_name="Big Data", database_title="Notes")

    res = usecase.execute(doc, target, "prompt", generation_mode=GenerationMode.GRAPHS_ONLY)

    assert res.success is True
    # In GRAPHS_ONLY, schema_exporter SHOULD be called
    schema_exporter.extract_artifacts.assert_called_once()
    # In GRAPHS_ONLY, appended blocks should contain the mermaid code block
    appended_blocks = notion_client.append_blocks.call_args[0][1]
    has_mermaid = any(b.get("type") == "code" and b.get("code", {}).get("language") == "mermaid" for b in appended_blocks)
    assert has_mermaid is True


def test_process_document_force_resync():
    state_repo = MagicMock(spec=IStateRepository)
    # File is already marked as SYNCED
    state_repo.get_entry.return_value = SyncEntry(file_hash="hash_force", status=SyncStatus.SYNCED, page_id="old_page")

    staging_storage = MagicMock(spec=IStagingStorage)
    staging_storage.exists.return_value = True
    staging_storage.read.return_value = "# Updated Notes\nBody text"

    notion_client = MagicMock(spec=INotionClient)
    notion_client.create_page.return_value = "new_page_id"

    usecase = ProcessDocumentUseCase(
        readers={},
        llm_client=MagicMock(spec=ILlmClient),
        notion_client=notion_client,
        state_repo=state_repo,
        staging_storage=staging_storage,
    )

    doc = Document(path=Path("lecture.pdf"), file_hash="hash_force", doc_type=DocumentType.SLIDES)
    target = NotionTarget(database_id="db1", course_name="Math", database_title="Notes")

    # With force=True, it should NOT skip, but archive old page and create new one
    res = usecase.execute(doc, target, "prompt", force=True)

    assert res.success is True
    assert res.skipped is False
    assert res.page_id == "new_page_id"
    notion_client.archive_page.assert_called_once_with("old_page")
    notion_client.create_page.assert_called_once_with("db1", "lecture")



