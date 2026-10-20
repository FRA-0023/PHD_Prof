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


def test_pymupdf_visual_extractor_pptx_resolves_cached_slides_pdf(sample_pdf: Path, tmp_path: Path):
    # ARCHITETTURA: Verifica che per un documento .pptx l'estrattore non apra il .pptx grezzo
    # (che in MuPDF produce testo reflowed su pagina bianca), ma il PDF vettoriale in staging.
    dummy_pptx = tmp_path / "lecture.pptx"
    dummy_pptx.write_bytes(b"not_a_real_pdf_or_pptx")

    cached_pdf = tmp_path / "pptx_hash_123_slides.pdf"
    cached_pdf.write_bytes(sample_pdf.read_bytes())

    extractor = PyMuPdfVisualExtractor(staging_dir=tmp_path)
    doc = Document(path=dummy_pptx, file_hash="pptx_hash_123", doc_type=DocumentType.SLIDES)

    output_img = tmp_path / "figures" / "slide_1.png"
    extractor.extract_figure(doc, page_number=1, crop_box=None, output_path=output_img)

    assert output_img.exists()
    assert output_img.stat().st_size > 0


def test_pymupdf_visual_extractor_pptx_raises_when_no_pdf_available(tmp_path: Path, monkeypatch):
    # TRADE-OFF: Se per un .pptx non esiste il PDF in staging e la conversione fallisce,
    # deve sollevare RuntimeError anziché fare fallback silenzioso sul reflow corrotto di MuPDF.
    dummy_pptx = tmp_path / "unconvertible.pptx"
    dummy_pptx.write_bytes(b"dummy_pptx")

    extractor = PyMuPdfVisualExtractor(staging_dir=tmp_path)
    doc = Document(path=dummy_pptx, file_hash="missing_pdf_hash", doc_type=DocumentType.SLIDES)

    from src.adapters.outbound.document_readers.gemini_file_reader import GeminiFileReader
    monkeypatch.setattr(GeminiFileReader, "_convert_pptx_to_pdf", lambda self, p, o: False)

    output_img = tmp_path / "figures" / "out.png"
    with pytest.raises(RuntimeError, match="Impossibile estrarre figure vettoriali"):
        extractor.extract_figure(doc, page_number=1, crop_box=None, output_path=output_img)


def test_pymupdf_visual_extractor_out_of_range_page_raises_value_error(sample_pdf: Path, tmp_path: Path):
    # ARCHITETTURA: Impedisce che indici di slide superiori al numero di pagine vengano
    # bloccati sull'ultima pagina generando N copie della stessa immagine.
    extractor = PyMuPdfVisualExtractor(staging_dir=tmp_path)
    doc = Document(path=sample_pdf, file_hash="dummy_hash", doc_type=DocumentType.SLIDES)

    output_img = tmp_path / "out_oob.png"
    with pytest.raises(ValueError, match="fuori range valido"):
        extractor.extract_figure(doc, page_number=99, crop_box=None, output_path=output_img)

