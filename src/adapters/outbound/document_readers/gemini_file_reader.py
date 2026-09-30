import time
from pathlib import Path
from typing import Any, List, Optional, Union
import google.genai as genai
import google.genai.types as genai_types
from src.core.domain.models import Document
from src.ports.outbound.document_reader_port import IDocumentReader
from src.adapters.outbound.document_readers.pptx_extractor import extract_pptx_to_markdown

class GeminiFileReader(IDocumentReader):
    """
    Multimodal document reader for presentation slides and documents.
    - PDF: Uploads to Google Gemini File API to preserve charts, formulas, and visual spatial layout.
    - PPTX (Dual-Payload Multimodal):
        1. Visual: Converts PPTX slides to a high-resolution PDF via PowerPoint COM automation on Windows,
           uploading it to Gemini File API so vision models see all diagrams, charts, and architectural schematics.
        2. Textual: Extracts slide titles, body bullet points, and speaker notes via python-pptx / MarkItDown.
        3. Returns a composite dual payload [speaker_notes_markdown, uploaded_pdf].
        4. Gracefully falls back to pure Markdown text if PowerPoint COM is unavailable.
    """

    SUPPORTED_MIME_TYPES = {
        ".pdf": "application/pdf",
        ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    }

    def __init__(
        self,
        api_key: str = "",
        timeout: float = 300.0,
        client: Optional[Any] = None,
        staging_dir: Optional[Path] = None,
    ):
        if client is not None:
            self.client = client
        else:
            if timeout and timeout > 0:
                timeout_ms = max(10_000, int(timeout * 1000 if timeout < 1000 else timeout))
                self.client = genai.Client(api_key=api_key, http_options={"timeout": timeout_ms})
            else:
                self.client = genai.Client(api_key=api_key)
        self.staging_dir = Path(staging_dir) if staging_dir is not None else Path("staging")
        try:
            self.staging_dir.mkdir(parents=True, exist_ok=True)
        except OSError:
            pass

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

    def _upload_and_poll_file(self, file_path: Path, mime_type: str, display_name: str) -> genai_types.File:
        str_path = str(file_path)
        try:
            size_mb = file_path.stat().st_size / (1024 * 1024)
            size_str = f", {size_mb:.1f} MB"
        except Exception:
            size_str = ""

        print(f"    [Gemini File API] Uploading '{display_name}' ({mime_type}{size_str})...")
        config = genai_types.UploadFileConfig(mime_type=mime_type)

        max_upload_retries = 3
        base_delay = 5.0
        uploaded = None
        for attempt in range(max_upload_retries):
            try:
                uploaded = self._upload_file(file_path=str_path, config=config)
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
            raise RuntimeError(f"Gemini: elaborazione fallita per '{str_path}'.")

        return uploaded

    def _convert_pptx_to_pdf(self, pptx_path: Path, output_pdf_path: Path) -> bool:
        """
        Converts a PPTX presentation to PDF via PowerPoint COM automation on Windows.
        Returns True if conversion succeeded and output PDF exists, False otherwise.
        """
        if not pptx_path.exists():
            return False

        try:
            import win32com.client
        except ImportError:
            return False

        try:
            import pythoncom
            pythoncom.CoInitialize()
        except Exception:
            pass

        app = None
        pres = None
        try:
            output_pdf_path.parent.mkdir(parents=True, exist_ok=True)
            abs_pptx = str(pptx_path.resolve())
            abs_pdf = str(output_pdf_path.resolve())

            # Format 32 is ppSaveAsPDF
            app = win32com.client.Dispatch("PowerPoint.Application")
            pres = app.Presentations.Open(abs_pptx, WithWindow=False)
            pres.SaveAs(abs_pdf, 32)
            return output_pdf_path.exists() and output_pdf_path.stat().st_size > 0
        except Exception as exc:
            print(f"    [PPTX to PDF Warning] Conversione COM fallita ({exc}).")
            return False
        finally:
            if pres is not None:
                try:
                    pres.Close()
                except Exception:
                    pass
            if app is not None:
                try:
                    if app.Presentations.Count == 0:
                        app.Quit()
                except Exception:
                    try:
                        app.Quit()
                    except Exception:
                        pass
            try:
                import pythoncom
                pythoncom.CoUninitialize()
            except Exception:
                pass

    def read(self, document: Document) -> Union[genai_types.File, str, List[Any]]:
        ext = document.path.suffix.lower()
        if ext not in self.SUPPORTED_MIME_TYPES:
            raise ValueError(
                f"Formato non supportato per GeminiFileReader: '{ext}'. "
                f"Formati supportati: {', '.join(sorted(self.SUPPORTED_MIME_TYPES.keys()))}"
            )

        # PPTX files: Dual-Payload Multimodal (PDF for visual layout + Markdown for speaker notes)
        if ext == ".pptx":
            print(f"    [MarkItDown / python-pptx] Estrazione locale slide e note da '{document.path.name}'...")
            notes_text = extract_pptx_to_markdown(document.path)
            print(f"    [MarkItDown / python-pptx] Estratti {len(notes_text)} caratteri in Markdown strutturato.")

            pdf_cached_path = self.staging_dir / f"{document.file_hash}_slides.pdf"
            pdf_ready = False

            if pdf_cached_path.exists() and pdf_cached_path.stat().st_size > 0:
                print(f"    [PPTX Cache] Trovato PDF prerenderizzato in staging: '{pdf_cached_path.name}'.")
                pdf_ready = True
            else:
                print(f"    [PowerPoint COM] Rendering visivo di '{document.path.name}' in PDF vettoriale...")
                pdf_ready = self._convert_pptx_to_pdf(document.path, pdf_cached_path)

            if pdf_ready:
                print("    [Dual-Payload] Modalità multimodale attiva: invio visuale (PDF) + note a piè di pagina.")
                uploaded_pdf = self._upload_and_poll_file(
                    file_path=pdf_cached_path,
                    mime_type="application/pdf",
                    display_name=f"{document.path.stem} (Visual Slides)",
                )
                notes_payload = (
                    "=== SLIDE SPEAKER NOTES & TEXT EXTRACTION ===\n"
                    "Below is the textual content and speaker notes extracted directly from the slide deck presentation. "
                    "Cross-reference this text with the visual slides attached in the PDF.\n\n"
                    f"{notes_text}"
                )
                return [notes_payload, uploaded_pdf]

            print("    [Fallback] Conversione PDF non disponibile. Procedo con la sola estrazione testuale.")
            return notes_text

        # Standard PDF
        return self._upload_and_poll_file(
            file_path=document.path,
            mime_type=self.SUPPORTED_MIME_TYPES[ext],
            display_name=document.path.name,
        )

    def cleanup(self, payload: Any) -> None:
        items = payload if isinstance(payload, list) else [payload]
        for item in items:
            if isinstance(item, genai_types.File):
                try:
                    self.client.files.delete(name=item.name)
                except Exception:
                    pass  # Gemini files expire automatically after 48 hours

