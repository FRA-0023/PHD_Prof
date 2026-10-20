import fitz  # PyMuPDF
from typing import Optional, Tuple
from pathlib import Path
from src.core.domain.models import Document
from src.ports.outbound.visual_extractor_port import IVisualExtractor

class PyMuPdfVisualExtractor(IVisualExtractor):
    """
    Implementazione di IVisualExtractor utilizzando PyMuPDF per renderizzare 
    le pagine PDF e applicare il crop.
    """

    def __init__(self, staging_dir: Optional[Path] = None):
        self.staging_dir = Path(staging_dir) if staging_dir is not None else Path("staging")

    def _resolve_renderable_pdf_path(self, document: Document, target_path: Path, output_path: Path) -> Path:
        """
        # ARCHITETTURA: Risoluzione deterministica del sorgente vettoriale PDF per file PPTX.
        # TRADE-OFF: Il motore interno di MuPDF (`fitz.open("...pptx")`) non renderizza la grafica
        # delle slide ma esegue un reflow del solo testo grezzo su pagine verticali bianche,
        # producendo immagini corrotte e disallineate rispetto alla numerazione delle slide.
        # Per i file .pptx risolviamo obbligatoriamente il PDF vettoriale prerenderizzato in staging
        # (`{file_hash}_slides.pdf`), innescando la conversione COM/LibreOffice on-demand se assente.
        """
        if target_path.suffix.lower() != ".pptx":
            return target_path

        file_hash = getattr(document, "file_hash", "") or target_path.stem
        candidate_pdfs = [
            self.staging_dir / f"{file_hash}_slides.pdf",
            output_path.parent.parent / f"{file_hash}_slides.pdf",
            Path("staging") / f"{file_hash}_slides.pdf",
        ]

        for candidate in candidate_pdfs:
            if candidate.exists() and candidate.stat().st_size > 0:
                return candidate

        # Tentativo di conversione on-demand tramite pipeline COM / LibreOffice
        primary_cache = self.staging_dir / f"{file_hash}_slides.pdf"
        try:
            from src.adapters.outbound.document_readers.gemini_file_reader import GeminiFileReader
            converter = GeminiFileReader(client=object(), staging_dir=self.staging_dir)
            if converter._convert_pptx_to_pdf(target_path, primary_cache):
                if primary_cache.exists() and primary_cache.stat().st_size > 0:
                    return primary_cache
        except Exception:
            pass

        raise RuntimeError(
            f"Impossibile estrarre figure vettoriali da '{target_path.name}': "
            f"PDF prerenderizzato '{primary_cache.name}' assente e conversione PPTX->PDF non disponibile."
        )

    def extract_figure(self, document: Document, page_number: int, crop_box: Optional[Tuple[float, float, float, float]], output_path: Path) -> None:
        # ARCHITETTURA: Risoluzione polimorfica di path/file_path per disaccoppiare l'adapter
        # da eventuali alias o variazioni del modello di dominio Document.
        target_path = getattr(document, "path", None) or getattr(document, "file_path", None)
        if not target_path or not target_path.exists():
            raise FileNotFoundError(f"Il documento {target_path} non esiste.")

        render_path = self._resolve_renderable_pdf_path(document, target_path, output_path)

        # PERFORMANCE: Assicura la presenza della cartella di output prima del rendering
        output_path.parent.mkdir(parents=True, exist_ok=True)

        doc = fitz.open(str(render_path))
        try:
            # ARCHITETTURA: Validazione rigorosa dei limiti di pagina (1-based).
            # Evita il clamping silenzioso sull'ultima pagina che generava duplicati identici
            # quando un indice di slide superava il numero di pagine del documento.
            if page_number < 1 or page_number > len(doc):
                raise ValueError(
                    f"Numero di slide/pagina {page_number} fuori range valido (1..{len(doc)}) per '{render_path.name}'."
                )

            idx = page_number - 1
            page = doc[idx]

            # Coordinate base della pagina
            rect = page.rect

            if crop_box:
                # ymin, xmin, ymax, xmax in [0, 1000]
                ymin, xmin, ymax, xmax = crop_box

                # Trasformazione da [0, 1000] a [0, width]/[0, height]
                x0 = (xmin / 1000.0) * rect.width
                y0 = (ymin / 1000.0) * rect.height
                x1 = (xmax / 1000.0) * rect.width
                y1 = (ymax / 1000.0) * rect.height

                clip_rect = fitz.Rect(x0, y0, x1, y1)
            else:
                clip_rect = rect

            # DPI alto (300) per chiarezza di schemi/testo nelle immagini
            mat = fitz.Matrix(300 / 72.0, 300 / 72.0)

            pix = page.get_pixmap(matrix=mat, clip=clip_rect, alpha=False)
            pix.save(str(output_path))
        finally:
            doc.close()
