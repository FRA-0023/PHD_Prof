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

    def __init__(self, api_key: str = "", timeout: float = 300.0, client: Optional[Any] = None):
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
        try:
            size_mb = document.path.stat().st_size / (1024 * 1024)
            size_str = f", {size_mb:.1f} MB"
        except Exception:
            size_str = ""

        print(f"    [Gemini File API] Uploading '{document.path.name}' ({mime_type}{size_str})...")
        config = genai_types.UploadFileConfig(mime_type=mime_type)

        max_upload_retries = 3
        base_delay = 5.0
        uploaded = None
        for attempt in range(max_upload_retries):
            try:
                uploaded = self._upload_file(file_path=file_path, config=config)
                break
            except Exception as exc:
                is_timeout = "timed out" in str(exc).lower() or "timeout" in str(exc).lower()
                is_conn = "connection" in str(exc).lower() or "reset" in str(exc).lower()
                if (is_timeout or is_conn) and attempt < max_upload_retries - 1:
                    delay = base_delay * (2 ** attempt)
                    print(
                        f"    [Gemini File API Warning] Upload interrotto ({exc}). "
                        f"Nuovo tentativo tra {delay:.0f}s... ({attempt + 1}/{max_upload_retries})"
                    )
                    time.sleep(delay)
                else:
                    raise

        poll_attempts = 0
        max_poll_attempts = 100
        while uploaded.state.name == "PROCESSING" and poll_attempts < max_poll_attempts:
            time.sleep(3)
            poll_attempts += 1
            try:
                uploaded = self.client.files.get(name=uploaded.name)
            except Exception as exc:
                if ("timed out" in str(exc).lower() or "timeout" in str(exc).lower()) and poll_attempts < max_poll_attempts:
                    print(f"    [Gemini File API Warning] Polling timeout temporaneo ({exc}), ritento...")
                    continue
                raise

        if uploaded.state.name == "FAILED":
            raise RuntimeError(f"Gemini: elaborazione fallita per '{file_path}'.")

        return uploaded

    def cleanup(self, payload: Any) -> None:
        if isinstance(payload, genai_types.File):
            try:
                self.client.files.delete(name=payload.name)
            except Exception:
                pass  # Gemini files expire automatically after 48 hours

