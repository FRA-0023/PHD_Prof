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
    
    def extract_figure(self, document: Document, page_number: int, crop_box: Optional[Tuple[float, float, float, float]], output_path: Path) -> None:
        # ARCHITETTURA: Risoluzione polimorfica di path/file_path per disaccoppiare l'adapter
        # da eventuali alias o variazioni del modello di dominio Document.
        target_path = getattr(document, "path", None) or getattr(document, "file_path", None)
        if not target_path or not target_path.exists():
            raise FileNotFoundError(f"Il documento {target_path} non esiste.")
            
        # PERFORMANCE: Assicura la presenza della cartella di output prima del rendering
        output_path.parent.mkdir(parents=True, exist_ok=True)

        doc = fitz.open(str(target_path))
        
        # Gli LLM (come Gemini) restituiscono page 1-based, PyMuPDF è 0-based.
        # Dobbiamo assicurarci di non sforare.
        idx = max(0, min(page_number - 1, len(doc) - 1))
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
            
        # DPI alto (200 o 300) per chiarezza di schemi/testo nelle immagini
        mat = fitz.Matrix(300 / 72.0, 300 / 72.0)
        
        pix = page.get_pixmap(matrix=mat, clip=clip_rect, alpha=False)
        pix.save(str(output_path))
        
        doc.close()
