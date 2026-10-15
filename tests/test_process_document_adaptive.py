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
        split_threshold_chars=40000,
    )

    doc = Document(path=Path("small.pptx"), file_hash="hash_small", doc_type=DocumentType.SLIDES)
    target = NotionTarget(database_id="db1", course_name="Micro", database_title="Notes")

    res = usecase.execute(doc, target, "prompt")

    assert res.success is True
    # EXACTLY 1 call to generate_notes!
    assert llm_client.generate_notes.call_count == 1
    schema_exporter.extract_artifacts.assert_called_once()


def test_process_document_sparse_80_slides_stays_single_call():
    """
    Ratione sostanza: 80 slide ma con sole 15 parole l'una (~1.200 parole / ~7.200 caratteri).
    Non deve attivare il Two-Stage, evitando spreco di quote e preservando 1 sola chiamata.
    """
    state_repo = MagicMock(spec=IStateRepository)
    state_repo.get_entry.return_value = None

    staging_storage = MagicMock(spec=IStagingStorage)
    staging_storage.exists.return_value = False

    reader = MagicMock(spec=IDocumentReader)
    # 80 slide sparse con 15 parole (circa 90 caratteri per slide = ~7.200 caratteri in totale)
    reader.read.return_value = ["Title slide. Only a few words here for brief bullet point." for _ in range(80)]

    llm_client = MagicMock(spec=ILlmClient)
    llm_client.generate_notes.return_value = "# Sparse Deck Notes\nShort content"

    notion_client = MagicMock(spec=INotionClient)
    notion_client.create_page.return_value = "page_sparse"

    usecase = ProcessDocumentUseCase(
        readers={DocumentType.SLIDES: reader},
        llm_client=llm_client,
        notion_client=notion_client,
        state_repo=state_repo,
        staging_storage=staging_storage,
        split_threshold_chars=40000,
    )

    doc = Document(path=Path("sparse_80_slides.pptx"), file_hash="hash_sparse", doc_type=DocumentType.SLIDES)
    target = NotionTarget(database_id="db1", course_name="Management", database_title="Notes")

    res = usecase.execute(doc, target, "prompt")

    assert res.success is True
    # Substantive density check guarantees ONLY 1 call despite 80 slides!
    assert llm_client.generate_notes.call_count == 1


def test_process_document_adaptive_two_stage_dense():
    """
    Volume elevato (>= 40.000 caratteri di testo reale): Esegue 2 chiamate a Gemini (Two-Stage Decoupled).
    Call 1: Note analitiche
    Call 2: Estrazione schemi e drills dal markdown prodotto
    """
    state_repo = MagicMock(spec=IStateRepository)
    state_repo.get_entry.return_value = None

    staging_storage = MagicMock(spec=IStagingStorage)
    staging_storage.exists.return_value = False

    reader = MagicMock(spec=IDocumentReader)
    # Testo denso che supera ampiamente i 40.000 caratteri
    dense_text = "Detailed mathematical proofs, derivations, and econometric models. " * 800  # ~56.000 caratteri
    reader.read.return_value = [dense_text]

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
        split_threshold_chars=40000,
    )

    doc = Document(path=Path("heavy.pptx"), file_hash="hash_heavy", doc_type=DocumentType.SLIDES)
    target = NotionTarget(database_id="db1", course_name="Econometrics", database_title="Notes")

    res = usecase.execute(doc, target, "prompt")

    assert res.success is True
    # Truly dense content activates Two-Stage: EXACTLY 2 calls!
    assert llm_client.generate_notes.call_count == 2
    saved_markdown = staging_storage.save.call_args[0][1]
    assert "Chapter 1: Extensive Lecture" in saved_markdown
    assert "Conceptual Architecture" in saved_markdown


def test_process_document_windowed_slide_chunking(monkeypatch):
    """
    # ARCHITETTURA: Mazzo di slide esteso caratterizzato da alta densità (> split_threshold_chars).
    # Verifica che il trigger character-driven attivi il partizionamento bilanciato in 2 tranche,
    # ciascuna con chiamata LLM dedicata + 1 chiamata unificata di Stage 2 per gli artefatti (totale 3 chiamate).
    """
    state_repo = MagicMock(spec=IStateRepository)
    state_repo.get_entry.return_value = None

    staging_storage = MagicMock(spec=IStagingStorage)
    staging_storage.exists.return_value = False

    reader = MagicMock(spec=IDocumentReader)
    reader.read.return_value = "chunk_payload_data"

    llm_client = MagicMock(spec=ILlmClient)
    llm_client.generate_notes.side_effect = [
        "## Part 1 Notes\nExtensive coverage of slides 1 to 34.",
        "## Part 2 Notes\nExtensive coverage of slides 35 to 67.",
        "## 🧠 Conceptual Architecture\n```mermaid\ngraph TD\nRoot --> Leaf\n```",
    ]

    notion_client = MagicMock(spec=INotionClient)
    notion_client.create_page.return_value = "page_chunked"

    usecase = ProcessDocumentUseCase(
        readers={DocumentType.SLIDES: reader},
        llm_client=llm_client,
        notion_client=notion_client,
        state_repo=state_repo,
        staging_storage=staging_storage,
        split_threshold_chars=20000,
    )

    # Mock _get_slide_character_counts, _count_slides, and _slice_pdf_pages to avoid disk I/O in unit test
    # 67 slide con densità realistica (totale: 27.000 caratteri)
    counts = [400] * 67
    monkeypatch.setattr(usecase, "_get_slide_character_counts", lambda doc: counts)
    monkeypatch.setattr(usecase, "_count_slides", lambda doc: 67)
    monkeypatch.setattr(usecase, "_slice_pdf_pages", lambda in_p, pages, out_p: None)

    doc = Document(path=Path("deck_67_slides.pdf"), file_hash="hash_67_slides", doc_type=DocumentType.SLIDES)
    target = NotionTarget(database_id="db1", course_name="Big Data", database_title="Notes")

    res = usecase.execute(doc, target, "system_prompt")

    assert res.success is True
    # 2 chunk note calls + 1 unified artifacts call = 3 calls
    assert llm_client.generate_notes.call_count == 3
    # Reader cleanup must be invoked for each chunk payload
    assert reader.cleanup.call_count == 2

    # Verification of stitched markdown in staging
    saved_markdown = staging_storage.save.call_args[0][1]
    assert "Part 1 Notes" in saved_markdown
    assert "Part 2 Notes" in saved_markdown
    assert "Conceptual Architecture" in saved_markdown


def test_partition_slides_by_character_budget_skewed():
    """
    # STATISTICA: Verifica che il partizionamento bilanci la massa di caratteri
    # e non il mero conteggio delle slide quando la distribuzione è altamente asimmetrica.
    """
    usecase = ProcessDocumentUseCase(
        readers={},
        llm_client=MagicMock(),
        notion_client=MagicMock(),
        state_repo=MagicMock(),
        staging_storage=MagicMock(),
        split_threshold_chars=20000,
    )

    # 20 slide sparse (100 car ciascuna = 2.000 car) + 20 slide dense (1.500 car ciascuna = 30.000 car)
    # Totale: 32.000 caratteri distribuiti su 40 slide
    skewed_counts = [100] * 20 + [1500] * 20
    ranges = usecase._partition_slides_by_character_budget(skewed_counts, max_chunk_chars=20000)

    # Con target ~16.000 car/chunk, deve tagliare verso la slide 29-30, non rigidamente a metà (slide 20)
    assert len(ranges) == 2
    assert ranges[0][0] == 1
    assert ranges[0][1] >= 28  # Incorpora tutte le slide sparse più le prime dense
    assert ranges[1][0] == ranges[0][1] + 1
    assert ranges[1][1] == 40

    chunk1_chars = sum(skewed_counts[ranges[0][0] - 1:ranges[0][1]])
    chunk2_chars = sum(skewed_counts[ranges[1][0] - 1:ranges[1][1]])
    # Entrambi i chunk rimangono ampiamente al di sotto dei 20.000 caratteri di soglia
    assert chunk1_chars <= 20000
    assert chunk2_chars <= 20000


def test_slide_chunking_triggered_by_characters_not_slide_count(monkeypatch):
    """
    # ARCHITETTURA: Dimostrazione del principio Character-First:
    # Caso A: 20 slide ma dense (30.000 caratteri > threshold 25.000) -> ATTIVA chunking.
    # Caso B: 60 slide ma sparse (8.000 caratteri <= threshold 25.000) -> NON attiva chunking (single call).
    """
    state_repo = MagicMock(spec=IStateRepository)
    state_repo.get_entry.return_value = None
    staging_storage = MagicMock(spec=IStagingStorage)
    staging_storage.exists.return_value = False
    reader = MagicMock(spec=IDocumentReader)
    reader.read.return_value = "payload"
    llm_client = MagicMock(spec=ILlmClient)
    llm_client.generate_notes.return_value = "# Notes\nContent"
    notion_client = MagicMock(spec=INotionClient)
    notion_client.create_page.return_value = "p1"

    usecase = ProcessDocumentUseCase(
        readers={DocumentType.SLIDES: reader},
        llm_client=llm_client,
        notion_client=notion_client,
        state_repo=state_repo,
        staging_storage=staging_storage,
        split_threshold_chars=25000,
    )
    monkeypatch.setattr(usecase, "_slice_pdf_pages", lambda in_p, pages, out_p: None)

    # Caso A: 20 slide dense (1.500 car/slide = 30.000 caratteri)
    dense_20_counts = [1500] * 20
    monkeypatch.setattr(usecase, "_get_slide_character_counts", lambda doc: dense_20_counts)
    monkeypatch.setattr(usecase, "_count_slides", lambda doc: 20)

    doc_dense = Document(path=Path("dense_20.pdf"), file_hash="hash_dense", doc_type=DocumentType.SLIDES)
    target = NotionTarget(database_id="db1", course_name="Course", database_title="Notes")

    usecase.execute(doc_dense, target, "prompt")
    # 30.000 car > 25.000 car -> Chunker attivato! 2 chunk notes + 1 stage 2 artifacts = 3 calls
    assert llm_client.generate_notes.call_count == 3

    # Reset mock
    llm_client.generate_notes.reset_mock()

    # Caso B: 60 slide sparse (100 car/slide = 6.000 caratteri)
    sparse_60_counts = [100] * 60
    monkeypatch.setattr(usecase, "_get_slide_character_counts", lambda doc: sparse_60_counts)
    monkeypatch.setattr(usecase, "_count_slides", lambda doc: 60)

    doc_sparse = Document(path=Path("sparse_60.pdf"), file_hash="hash_sparse_60", doc_type=DocumentType.SLIDES)
    usecase.execute(doc_sparse, target, "prompt")
    # 6.000 car <= 25.000 car -> Chunker NON attivato! Single call = 1 sola chiamata
    assert llm_client.generate_notes.call_count == 1

