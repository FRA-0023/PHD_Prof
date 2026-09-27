import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.core.domain.models import Document, DocumentType
from src.adapters.outbound.document_readers.text_pdf_reader import TextPdfReader


def test_text_pdf_reader_unsupported_format_raises_runtime_error():
    reader = TextPdfReader()
    doc = Document(path=Path("/tmp/data.csv"), file_hash="hash_csv", doc_type=DocumentType.PAPER_OR_BOOK)

    with pytest.raises(RuntimeError, match="Impossibile convertire il documento"):
        reader.read(doc)


def test_text_pdf_reader_pptx_fallback_with_python_pptx():
    reader = TextPdfReader()
    # Force markitdown to fail or be bypassed to test fallback
    reader._has_markitdown = False

    doc = Document(path=Path("/tmp/presentation.pptx"), file_hash="hash_pptx", doc_type=DocumentType.PAPER_OR_BOOK)

    mock_shape1 = MagicMock()
    mock_shape1.has_text_frame = True
    p1 = MagicMock()
    p1.text = "Introduction to Econometrics"
    mock_shape1.text_frame.paragraphs = [p1]

    mock_slide = MagicMock()
    mock_slide.shapes = [mock_shape1]
    mock_slide.has_notes_slide = True
    mock_slide.notes_slide.notes_text_frame.text = "Emphasize Gauss-Markov assumptions"

    mock_presentation = MagicMock()
    mock_presentation.slides = [mock_slide]

    with patch("pptx.Presentation", return_value=mock_presentation):
        result = reader.read(doc)

    assert "Introduction to Econometrics" in result
    assert "Note del relatore" in result
    assert "Emphasize Gauss-Markov assumptions" in result
