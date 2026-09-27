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
    assert kwargs["path"] == str(Path("/tmp/lecture.pdf"))
    assert kwargs["config"].mime_type == "application/pdf"


def test_gemini_file_reader_upload_pptx_mime_type(mock_genai_client):
    mock_file = genai_types.File(name="files/test-pptx-id", state="ACTIVE")
    mock_genai_client.files.upload.return_value = mock_file

    reader = GeminiFileReader(client=mock_genai_client)
    doc = Document(path=Path("/tmp/deck.pptx"), file_hash="hash_pptx", doc_type=DocumentType.SLIDES)

    result = reader.read(doc)

    assert result == mock_file
    mock_genai_client.files.upload.assert_called_once()
    _, kwargs = mock_genai_client.files.upload.call_args
    assert kwargs["path"] == str(Path("/tmp/deck.pptx"))
    assert kwargs["config"].mime_type == "application/vnd.openxmlformats-officedocument.presentationml.presentation"


def test_gemini_file_reader_upload_case_insensitive_extension(mock_genai_client):
    mock_file = genai_types.File(name="files/test-upper-id", state="ACTIVE")
    mock_genai_client.files.upload.return_value = mock_file

    reader = GeminiFileReader(client=mock_genai_client)
    doc = Document(path=Path("/tmp/PRESENTATION.PPTX"), file_hash="hash_upper", doc_type=DocumentType.SLIDES)

    result = reader.read(doc)

    assert result == mock_file
    _, kwargs = mock_genai_client.files.upload.call_args
    assert kwargs["config"].mime_type == "application/vnd.openxmlformats-officedocument.presentationml.presentation"


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
    doc = Document(path=Path("/tmp/corrupted.pptx"), file_hash="hash_fail", doc_type=DocumentType.SLIDES)

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
