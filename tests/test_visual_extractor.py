from pathlib import Path
import fitz
import pytest

from src.core.domain.models import Document, DocumentType
from src.adapters.outbound.pymupdf_visual_extractor import PyMuPdfVisualExtractor


@pytest.fixture
def sample_pdf(tmp_path: Path) -> Path:
    # ARCHITETTURA: Creazione deterministica di un file PDF vettoriale minimale in-memory
    # per testare il rendering PyMuPDF e i meccanismi di crop senza fixture binarie esterne.
    pdf_path = tmp_path / "sample.pdf"
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)  # A4 standard
    page.draw_rect(fitz.Rect(50, 50, 200, 200), color=(1, 0, 0), fill=(0, 0, 1))
    doc.save(str(pdf_path))
    doc.close()
    return pdf_path


def test_pymupdf_visual_extractor_with_document_path(sample_pdf: Path, tmp_path: Path):
    extractor = PyMuPdfVisualExtractor()
    doc = Document(path=sample_pdf, file_hash="dummy_hash", doc_type=DocumentType.SLIDES)

    output_img = tmp_path / "out" / "fig1.png"
    # Estrazione intera pagina
    extractor.extract_figure(doc, page_number=1, crop_box=None, output_path=output_img)

    assert output_img.exists()
    assert output_img.stat().st_size > 0


def test_pymupdf_visual_extractor_with_crop_box(sample_pdf: Path, tmp_path: Path):
    extractor = PyMuPdfVisualExtractor()
    doc = Document(path=sample_pdf, file_hash="dummy_hash", doc_type=DocumentType.SLIDES)

    output_img = tmp_path / "cropped.png"
    # ymin, xmin, ymax, xmax in scala 0..1000
    crop = (100.0, 100.0, 500.0, 500.0)
    extractor.extract_figure(doc, page_number=1, crop_box=crop, output_path=output_img)

    assert output_img.exists()
    assert output_img.stat().st_size > 0


def test_pymupdf_visual_extractor_file_not_found(tmp_path: Path):
    extractor = PyMuPdfVisualExtractor()
    doc = Document(path=tmp_path / "nonexistent.pdf", file_hash="dummy_hash", doc_type=DocumentType.SLIDES)

    output_img = tmp_path / "out.png"
    with pytest.raises(FileNotFoundError):
        extractor.extract_figure(doc, page_number=1, crop_box=None, output_path=output_img)


def test_document_file_path_property_backward_compatibility(sample_pdf: Path):
    doc = Document(path=sample_pdf, file_hash="dummy_hash", doc_type=DocumentType.SLIDES)
    assert hasattr(doc, "file_path")
    assert doc.file_path == doc.path
