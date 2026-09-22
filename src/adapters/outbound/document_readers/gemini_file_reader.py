import time
import google.genai as genai
import google.genai.types as genai_types
from typing import Any
from src.core.domain.models import Document
from src.ports.outbound.document_reader_port import IDocumentReader

class GeminiFileReader(IDocumentReader):
    """
    Multimodal document reader that uploads PDFs to the Gemini File API.
    Essential for lecture slides where charts, figures, and spatial layouts convey meaning.
    """
    def __init__(self, api_key: str, timeout: float = 20.0):
        self.client = genai.Client(api_key=api_key, http_options={"timeout": timeout})

    def read(self, document: Document) -> genai_types.File:
        pdf_path = str(document.path)
        print(f"    [Gemini File API] Uploading '{document.path.name}'...")
        uploaded = self.client.files.upload(
            file=pdf_path,
            config=genai_types.UploadFileConfig(mime_type="application/pdf"),
        )

        while uploaded.state.name == "PROCESSING":
            time.sleep(3)
            uploaded = self.client.files.get(name=uploaded.name)

        if uploaded.state.name == "FAILED":
            raise RuntimeError(f"Gemini: elaborazione fallita per '{pdf_path}'.")

        return uploaded

    def cleanup(self, payload: Any) -> None:
        if isinstance(payload, genai_types.File):
            try:
                self.client.files.delete(name=payload.name)
            except Exception:
                pass  # Gemini files expire automatically after 48 hours
