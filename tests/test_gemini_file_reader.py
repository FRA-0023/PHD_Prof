import pytest
from pathlib import Path
from unittest.mock import MagicMock
import google.genai.types as genai_types

from src.core.domain.models import Document, DocumentType
from src.adapters.outbound.document_readers.gemini_file_reader import GeminiFileReader


@pytest.fixture
def mock_genai_client():
    client = MagicMock()
    return client


def test_gemini_file_reader_upload_pdf_mime_type(mock_genai_client):
    mock_file = genai_types.File(name="files/test-pdf-id", state="ACTIVE")
    mock_genai_client.files.upload.return_value = mock_file

    reader = GeminiFileReader(client=mock_genai_client)
    doc = Document(path=Path("/tmp/lecture.pdf"), file_hash="hash_pdf", doc_type=DocumentType.SLIDES)

    result = reader.read(doc)

    assert result == mock_file
    mock_genai_client.files.upload.assert_called_once()
    _, kwargs = mock_genai_client.files.upload.call_args
    assert (kwargs.get("file") or kwargs.get("path")) == str(Path("/tmp/lecture.pdf"))
    assert kwargs["config"].mime_type == "application/pdf"


def test_gemini_file_reader_pptx_extracts_markdown_locally(mock_genai_client, monkeypatch):
    monkeypatch.setattr(
        "src.adapters.outbound.document_readers.gemini_file_reader.extract_pptx_to_markdown",
        lambda p: "## Slide 1\nExtracted PPTX Markdown content",
    )

    reader = GeminiFileReader(client=mock_genai_client)
    doc = Document(path=Path("/tmp/deck.pptx"), file_hash="hash_pptx", doc_type=DocumentType.SLIDES)

    result = reader.read(doc)

    assert result == "## Slide 1\nExtracted PPTX Markdown content"
    mock_genai_client.files.upload.assert_not_called()


def test_gemini_file_reader_upload_case_insensitive_pdf_extension(mock_genai_client):
    mock_file = genai_types.File(name="files/test-upper-id", state="ACTIVE")
    mock_genai_client.files.upload.return_value = mock_file

    reader = GeminiFileReader(client=mock_genai_client)
    doc = Document(path=Path("/tmp/PRESENTATION.PDF"), file_hash="hash_upper", doc_type=DocumentType.SLIDES)

    result = reader.read(doc)

    assert result == mock_file
    _, kwargs = mock_genai_client.files.upload.call_args
    assert kwargs["config"].mime_type == "application/pdf"


def test_gemini_file_reader_unsupported_extension_raises_value_error(mock_genai_client):
    reader = GeminiFileReader(client=mock_genai_client)
    doc = Document(path=Path("/tmp/notes.docx"), file_hash="hash_docx", doc_type=DocumentType.SLIDES)

    with pytest.raises(ValueError, match="Formato non supportato per GeminiFileReader"):
        reader.read(doc)

    mock_genai_client.files.upload.assert_not_called()


def test_gemini_file_reader_polling_processing_state(mock_genai_client, monkeypatch):
    initial_file = genai_types.File(name="files/async-file-id", state="PROCESSING")
    ready_file = genai_types.File(name="files/async-file-id", state="ACTIVE")

    mock_genai_client.files.upload.return_value = initial_file
    mock_genai_client.files.get.return_value = ready_file

    sleep_mock = MagicMock()
    monkeypatch.setattr("time.sleep", sleep_mock)

    reader = GeminiFileReader(client=mock_genai_client)
    doc = Document(path=Path("/tmp/slides.pdf"), file_hash="hash_async", doc_type=DocumentType.SLIDES)

    result = reader.read(doc)

    assert result == ready_file
    sleep_mock.assert_called_once_with(3)
    mock_genai_client.files.get.assert_called_once_with(name="files/async-file-id")


def test_gemini_file_reader_failed_state_raises_runtime_error(mock_genai_client):
    failed_file = genai_types.File(name="files/failed-id", state="FAILED")
    mock_genai_client.files.upload.return_value = failed_file

    reader = GeminiFileReader(client=mock_genai_client)
    doc = Document(path=Path("/tmp/corrupted.pdf"), file_hash="hash_fail", doc_type=DocumentType.SLIDES)

    with pytest.raises(RuntimeError, match="Gemini: elaborazione fallita"):
        reader.read(doc)


def test_gemini_file_reader_cleanup_deletes_file(mock_genai_client):
    file_to_delete = genai_types.File(name="files/to-delete", state="ACTIVE")

    reader = GeminiFileReader(client=mock_genai_client)
    reader.cleanup(file_to_delete)

    mock_genai_client.files.delete.assert_called_once_with(name="files/to-delete")


def test_gemini_file_reader_cleanup_ignores_non_file_payload(mock_genai_client):
    reader = GeminiFileReader(client=mock_genai_client)
    reader.cleanup("plain_text_payload")

    mock_genai_client.files.delete.assert_not_called()


def test_gemini_file_reader_upload_modern_sdk_file_param():
    mock_file = genai_types.File(name="files/modern", state="ACTIVE")

    def modern_upload(*, file, config):
        return mock_file

    client = MagicMock()
    client.files.upload = MagicMock(side_effect=modern_upload)
    # Give the mock function a signature with 'file' parameter
    import inspect
    sig = inspect.Signature([
        inspect.Parameter("file", inspect.Parameter.KEYWORD_ONLY),
        inspect.Parameter("config", inspect.Parameter.KEYWORD_ONLY),
    ])
    client.files.upload.__signature__ = sig

    reader = GeminiFileReader(client=client)
    doc = Document(path=Path("/tmp/modern.pdf"), file_hash="h1", doc_type=DocumentType.SLIDES)
    res = reader.read(doc)

    assert res == mock_file
    _, kwargs = client.files.upload.call_args
    assert "file" in kwargs
    assert kwargs["file"] == str(Path("/tmp/modern.pdf"))


def test_gemini_file_reader_upload_legacy_sdk_path_param():
    mock_file = genai_types.File(name="files/legacy", state="ACTIVE")

    def legacy_upload(*, path, config):
        return mock_file

    client = MagicMock()
    client.files.upload = MagicMock(side_effect=legacy_upload)
    import inspect
    sig = inspect.Signature([
        inspect.Parameter("path", inspect.Parameter.KEYWORD_ONLY),
        inspect.Parameter("config", inspect.Parameter.KEYWORD_ONLY),
    ])
    client.files.upload.__signature__ = sig

    reader = GeminiFileReader(client=client)
    doc = Document(path=Path("/tmp/legacy.pdf"), file_hash="h2", doc_type=DocumentType.SLIDES)
    res = reader.read(doc)

    assert res == mock_file
    _, kwargs = client.files.upload.call_args
    assert "path" in kwargs
    assert kwargs["path"] == str(Path("/tmp/legacy.pdf"))


def test_gemini_file_reader_upload_fallback_on_type_error():
    mock_file = genai_types.File(name="files/fallback", state="ACTIVE")

    def upload_func(**kwargs):
        if "file" in kwargs:
            raise TypeError("upload() got an unexpected keyword argument 'file'")
        if "path" in kwargs:
            return mock_file
        raise ValueError("neither path nor file")

    client = MagicMock()
    client.files.upload = MagicMock(side_effect=upload_func)

    reader = GeminiFileReader(client=client)
    doc = Document(path=Path("/tmp/fallback.pdf"), file_hash="h3", doc_type=DocumentType.SLIDES)
    res = reader.read(doc)

    assert res == mock_file
    assert client.files.upload.call_count == 2
    # First call attempted file=, second call succeeded with path=
    first_call_kwargs = client.files.upload.call_args_list[0][1]
    second_call_kwargs = client.files.upload.call_args_list[1][1]
    assert "file" in first_call_kwargs
    assert "path" in second_call_kwargs


def test_gemini_file_reader_upload_retry_on_timeout(monkeypatch):
    mock_file = genai_types.File(name="files/retry-timeout", state="ACTIVE")
    sleep_mock = MagicMock()
    monkeypatch.setattr("time.sleep", sleep_mock)

    attempts = 0

    def flaky_upload(**kwargs):
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise TimeoutError("The read operation timed out")
        return mock_file

    client = MagicMock()
    client.files.upload = MagicMock(side_effect=flaky_upload)

    reader = GeminiFileReader(client=client)
    doc = Document(path=Path("/tmp/deck.pdf"), file_hash="h4", doc_type=DocumentType.SLIDES)
    res = reader.read(doc)

    assert res == mock_file
    assert client.files.upload.call_count == 2
    sleep_mock.assert_called_with(5.0)


def test_gemini_file_reader_polling_retry_on_timeout(monkeypatch):
    proc_file = genai_types.File(name="files/poll-to", state="PROCESSING")
    ready_file = genai_types.File(name="files/poll-to", state="ACTIVE")
    sleep_mock = MagicMock()
    monkeypatch.setattr("time.sleep", sleep_mock)

    client = MagicMock()
    client.files.upload.return_value = proc_file

    get_attempts = 0

    def flaky_get(name):
        nonlocal get_attempts
        get_attempts += 1
        if get_attempts == 1:
            raise TimeoutError("The read operation timed out during get")
        return ready_file

    client.files.get = MagicMock(side_effect=flaky_get)

    reader = GeminiFileReader(client=client)
    doc = Document(path=Path("/tmp/deck.pdf"), file_hash="h5", doc_type=DocumentType.SLIDES)
    res = reader.read(doc)

    assert res == ready_file
    assert client.files.get.call_count == 2


def test_gemini_file_reader_pptx_dual_payload_when_converted_successfully(mock_genai_client, monkeypatch, tmp_path):
    monkeypatch.setattr(
        "src.adapters.outbound.document_readers.gemini_file_reader.extract_pptx_to_markdown",
        lambda p: "## Slide 1: Introduction\n* Point A\n\n**Note del relatore:**\nSpiegazione dettagliata.",
    )

    dummy_pptx = tmp_path / "deck.pptx"
    dummy_pptx.write_bytes(b"dummy_pptx_bytes")

    mock_pdf_file = genai_types.File(name="files/converted-deck-id", state="ACTIVE")
    mock_genai_client.files.upload.return_value = mock_pdf_file

    reader = GeminiFileReader(client=mock_genai_client, staging_dir=tmp_path)

    def fake_convert(pptx_path, out_pdf_path):
        out_pdf_path.write_bytes(b"%PDF-1.4 dummy content")
        return True

    monkeypatch.setattr(reader, "_convert_pptx_to_pdf", fake_convert)

    doc = Document(path=dummy_pptx, file_hash="deck_hash_123", doc_type=DocumentType.SLIDES)
    payload = reader.read(doc)

    assert isinstance(payload, list)
    assert len(payload) == 2
    assert "=== SLIDE SPEAKER NOTES & TEXT EXTRACTION ===" in payload[0]
    assert "Spiegazione dettagliata" in payload[0]
    assert payload[1] == mock_pdf_file

    mock_genai_client.files.upload.assert_called_once()
    _, kwargs = mock_genai_client.files.upload.call_args
    assert kwargs["config"].mime_type == "application/pdf"


def test_gemini_file_reader_pptx_reuses_cached_pdf_in_staging(mock_genai_client, monkeypatch, tmp_path):
    monkeypatch.setattr(
        "src.adapters.outbound.document_readers.gemini_file_reader.extract_pptx_to_markdown",
        lambda p: "## Slide 1\nCached content",
    )

    dummy_pptx = tmp_path / "deck.pptx"
    dummy_pptx.write_bytes(b"dummy_pptx_bytes")

    cached_pdf = tmp_path / "cached_hash_slides.pdf"
    cached_pdf.write_bytes(b"%PDF-1.4 cached pre-rendered slides")

    mock_pdf_file = genai_types.File(name="files/cached-deck-id", state="ACTIVE")
    mock_genai_client.files.upload.return_value = mock_pdf_file

    reader = GeminiFileReader(client=mock_genai_client, staging_dir=tmp_path)

    convert_mock = MagicMock(return_value=True)
    monkeypatch.setattr(reader, "_convert_pptx_to_pdf", convert_mock)

    doc = Document(path=dummy_pptx, file_hash="cached_hash", doc_type=DocumentType.SLIDES)
    payload = reader.read(doc)

    assert isinstance(payload, list)
    assert payload[1] == mock_pdf_file
    convert_mock.assert_not_called()
    mock_genai_client.files.upload.assert_called_once()


def test_gemini_file_reader_pptx_fallback_when_conversion_fails(mock_genai_client, monkeypatch, tmp_path):
    monkeypatch.setattr(
        "src.adapters.outbound.document_readers.gemini_file_reader.extract_pptx_to_markdown",
        lambda p: "## Slide 1\nFallback markdown text only",
    )

    dummy_pptx = tmp_path / "deck.pptx"
    dummy_pptx.write_bytes(b"dummy_pptx_bytes")

    reader = GeminiFileReader(client=mock_genai_client, staging_dir=tmp_path)
    monkeypatch.setattr(reader, "_convert_pptx_to_pdf", lambda p, o: False)

    doc = Document(path=dummy_pptx, file_hash="failed_conv_hash", doc_type=DocumentType.SLIDES)
    payload = reader.read(doc)

    assert payload == "## Slide 1\nFallback markdown text only"
    mock_genai_client.files.upload.assert_not_called()


def test_gemini_file_reader_cleanup_composite_payload(mock_genai_client):
    mock_file = genai_types.File(name="files/dual-payload-file", state="ACTIVE")
    reader = GeminiFileReader(client=mock_genai_client)

    composite_payload = ["Notes text string", mock_file]
    reader.cleanup(composite_payload)

    mock_genai_client.files.delete.assert_called_once_with(name="files/dual-payload-file")

