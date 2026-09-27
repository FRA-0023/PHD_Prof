import time
from typing import Any, Optional, Union
import google.genai as genai
import google.genai.types as genai_types
from src.core.domain.models import Document
from src.ports.outbound.document_reader_port import IDocumentReader
from src.adapters.outbound.document_readers.pptx_extractor import extract_pptx_to_markdown

class GeminiFileReader(IDocumentReader):
    """
    Multimodal document reader for presentation slides and documents.
    - PDF: Uploads to Google Gemini File API to preserve charts, formulas, and visual spatial layout.
    - PPTX: Extracts structured Markdown (headers, bullet points, tables, speaker notes) locally
      via MarkItDown and python-pptx, preventing socket upload timeouts and remote API failures.
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

    def read(self, document: Document) -> Union[genai_types.File, str]:
        ext = document.path.suffix.lower()
        if ext not in self.SUPPORTED_MIME_TYPES:
            raise ValueError(
                f"Formato non supportato per GeminiFileReader: '{ext}'. "
                f"Formati supportati: {', '.join(sorted(self.SUPPORTED_MIME_TYPES.keys()))}"
            )

        # PPTX files: convert locally via MarkItDown / python-pptx to prevent upload timeouts
        if ext == ".pptx":
            print(f"    [MarkItDown / python-pptx] Estrazione locale slide e note da '{document.path.name}'...")
            text = extract_pptx_to_markdown(document.path)
            print(f"    [MarkItDown / python-pptx] Estratti {len(text)} caratteri in Markdown strutturato.")
            return text

        file_path = str(document.path)
        mime_type = self.SUPPORTED_MIME_TYPES[ext]
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

