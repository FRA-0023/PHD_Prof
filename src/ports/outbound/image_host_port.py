from abc import ABC, abstractmethod
from pathlib import Path

class IImageHostClient(ABC):
    """
    Porta outbound per il caricamento di asset grafici (immagini, screenshot) su uno storage cloud.
    """
    @abstractmethod
    def upload_image(self, file_path: Path, object_name: str) -> str:
        """
        Carica un file locale sullo storage remoto e restituisce l'URL pubblico.
        
        :param file_path: Percorso locale del file da caricare.
        :param object_name: Nome del file remoto (es. un hash).
        :return: URL pubblico accessibile in sola lettura (HTTPS).
        """
        pass
