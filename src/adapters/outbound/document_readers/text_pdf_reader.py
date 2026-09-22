from typing import Any
from src.core.domain.models import Document
from src.ports.outbound.document_reader_port import IDocumentReader

class TextPdfReader(IDocumentReader):
    """
    Extracts structured text/markdown from dense academic documents (papers, book chapters, lecture notes).
    Uses MarkItDown if available; falls back to PyMuPDF (fitz) for fast, zero-dependency extraction.
    Trade-off: Bypasses Gemini File API upload latency and remote file limits entirely,
    injecting extracted text directly into the LLM context.
    """
    def __init__(self):
        self._has_markitdown = False
        try:
            from markitdown import MarkItDown
            self._md = MarkItDown()
            self._has_markitdown = True
        except ImportError:
            self._has_markitdown = False

    def read(self, document: Document) -> str:
        pdf_path = str(document.path)
        print(f"    [Local Parser] Extracting text/markdown from '{document.path.name}'...")

        if self._has_markitdown:
            try:
                result = self._md.convert(pdf_path)
                text = result.text_content.strip()
                if text:
                    print(f"    [MarkItDown] Extracted {len(text)} characters.")
                    return text
            except Exception as exc:
                print(f"    [MarkItDown Warning] Conversion failed ({exc}), falling back to PyMuPDF...")

        # Fallback to PyMuPDF (fitz)
        try:
            import fitz
            doc = fitz.open(pdf_path)
            pages_text = []
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                txt = page.get_text("text").strip()
                if txt:
                    pages_text.append(f"--- PAGE {page_num + 1} ---\n{txt}")
            doc.close()
            full_text = "\n\n".join(pages_text).strip()
            print(f"    [PyMuPDF] Extracted {len(full_text)} characters across {len(pages_text)} pages.")
            return full_text
        except Exception as exc:
            raise RuntimeError(f"Impossibile estrarre testo dal PDF '{pdf_path}': {exc}")

    def cleanup(self, payload: Any) -> None:
        # No remote resources to clean up for local text extraction
        pass
