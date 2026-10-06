from abc import ABC, abstractmethod
from typing import Optional, Tuple
from pathlib import Path
from src.core.domain.models import Document

class IVisualExtractor(ABC):
    """
    Porta outbound per l'estrazione visiva (screenshot/crop) di porzioni di documento.
    """
    @abstractmethod
    def extract_figure(self, document: Document, page_number: int, crop_box: Optional[Tuple[float, float, float, float]], output_path: Path) -> None:
        """
        Estrae una figura dal documento e la salva sul filesystem.
        
        :param document: Il documento sorgente.
        :param page_number: Indice della pagina (1-based).
        :param crop_box: Coordinate del crop (ymin, xmin, ymax, xmax) normalizzate in [0, 1000] o None per pagina intera.
        :param output_path: Percorso in cui salvare l'immagine (es. PNG).
        """
        pass
