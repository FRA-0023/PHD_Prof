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


def test_pptx_extractor_stdlib_fallback_when_dependencies_missing(tmp_path, monkeypatch):
    import io
    import zipfile
    from src.adapters.outbound.document_readers.pptx_extractor import extract_pptx_to_markdown

    # Create a synthetic minimal OpenXML PPTX
    pptx_path = tmp_path / "synthetic.pptx"
    slide_xml = b"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
    <p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
        <p:cSld>
            <p:spTree>
                <p:sp>
                    <p:txBody>
                        <a:p><a:r><a:t>Pure Stdlib Heading</a:t></a:r></a:p>
                        <a:p><a:r><a:t>Body line without third party packages</a:t></a:r></a:p>
                    </p:txBody>
                </p:sp>
            </p:spTree>
        </p:cSld>
    </p:sld>"""

    note_xml = b"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
    <p:notes xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
        <p:cSld>
            <p:spTree>
                <p:sp>
                    <p:txBody>
                        <a:p><a:r><a:t>Critical presenter remark</a:t></a:r></a:p>
                    </p:txBody>
                </p:sp>
            </p:spTree>
        </p:cSld>
    </p:notes>"""

    with zipfile.ZipFile(pptx_path, "w") as z:
        z.writestr("ppt/slides/slide1.xml", slide_xml)
        z.writestr("ppt/notesSlides/notesSlide1.xml", note_xml)

    # Force Tier 1 and Tier 2 to be skipped by raising ImportError
    import sys
    monkeypatch.setitem(sys.modules, "markitdown", None)
    monkeypatch.setitem(sys.modules, "pptx", None)

    result = extract_pptx_to_markdown(pptx_path)

    assert "## Slide 1" in result
    assert "Pure Stdlib Heading" in result
    assert "Body line without third party packages" in result
    assert "Note del relatore" in result
    assert "Critical presenter remark" in result

