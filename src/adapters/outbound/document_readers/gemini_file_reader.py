import time
from typing import Any, Optional
import google.genai as genai
import google.genai.types as genai_types
from src.core.domain.models import Document
from src.ports.outbound.document_reader_port import IDocumentReader

class GeminiFileReader(IDocumentReader):
    """
    Multimodal document reader that uploads presentation slide decks and documents (PDF, PPTX)
    to the Gemini File API.

    Preserves multimodal visual context (charts, diagrams, equations, and spatial layouts)
    by delegating parsing and rendering directly to Gemini's native document vision pipeline.
    """

    SUPPORTED_MIME_TYPES = {
        ".pdf": "application/pdf",
        ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    }

    def __init__(self, api_key: str = "", timeout: float = 60.0, client: Optional[Any] = None):
        if client is not None:
            self.client = client
        else:
            self.client = genai.Client(api_key=api_key, http_options={"timeout": timeout})

    def _upload_file(self, file_path: str, config: genai_types.UploadFileConfig) -> genai_types.File:
        # Cross-version compatibility: modern google-genai SDK uses 'file=', legacy v0.6.0 used 'path='
        try:
            import inspect
            sig = inspect.signature(self.client.files.upload)
            if "file" in sig.parameters:
                return self.client.files.upload(file=file_path, config=config)
            if "path" in sig.parameters:
                return self.client.files.upload(path=file_path, config=config)
        except Exception:
            pass

        try:
            return self.client.files.upload(file=file_path, config=config)
        except TypeError as exc:
            if "unexpected keyword argument" in str(exc) and "file" in str(exc):
                return self.client.files.upload(path=file_path, config=config)
            raise

    def read(self, document: Document) -> genai_types.File:
        ext = document.path.suffix.lower()
        mime_type = self.SUPPORTED_MIME_TYPES.get(ext)
        if not mime_type:
            raise ValueError(
                f"Formato non supportato per GeminiFileReader: '{ext}'. "
                f"Formati supportati: {', '.join(sorted(self.SUPPORTED_MIME_TYPES.keys()))}"
            )

        file_path = str(document.path)
        print(f"    [Gemini File API] Uploading '{document.path.name}' ({mime_type})...")
        config = genai_types.UploadFileConfig(mime_type=mime_type)
        uploaded = self._upload_file(file_path=file_path, config=config)

        while uploaded.state.name == "PROCESSING":
            time.sleep(3)
            uploaded = self.client.files.get(name=uploaded.name)

        if uploaded.state.name == "FAILED":
            raise RuntimeError(f"Gemini: elaborazione fallita per '{file_path}'.")

        return uploaded

    def cleanup(self, payload: Any) -> None:
        if isinstance(payload, genai_types.File):
            try:
                self.client.files.delete(name=payload.name)
            except Exception:
                pass  # Gemini files expire automatically after 48 hours

