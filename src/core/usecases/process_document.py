import hashlib
from pathlib import Path
from typing import Dict, Any, Optional

from src.core.domain.models import (
    Document,
    DocumentType,
    SyncStatus,
    SyncEntry,
    ProcessingResult,
    NotionTarget,
)
from src.ports.outbound.document_reader_port import IDocumentReader
from src.ports.outbound.llm_client_port import ILlmClient
from src.ports.outbound.notion_client_port import INotionClient
from src.ports.outbound.state_repository_port import IStateRepository
from src.ports.outbound.staging_storage_port import IStagingStorage
from src.ports.outbound.study_schema_exporter_port import IStudySchemaExporter
from src.core.domain.prompt_templates import get_artifacts_extraction_prompt
from src.adapters.outbound.notion_block_builder import build_notion_blocks

def compute_file_hash(file_path: Path) -> str:
    """Computes SHA-256 hash of a file on disk."""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

class ProcessDocumentUseCase:
    """
    Crash-Only ETL Pipeline Use Case.
    Orchestrates:
      1. Cryptographic state check (idempotency)
      2. Self-healing rollback of orphaned pages
      3. Decoupled extraction & LLM inference (staging disk cache)
      4. Safe loading into Notion with batching and state finalization
    """
    def __init__(
        self,
        readers: Dict[DocumentType, IDocumentReader],
        llm_client: ILlmClient,
        notion_client: INotionClient,
        state_repo: IStateRepository,
        staging_storage: IStagingStorage,
        visual_extractor: Optional[Any] = None,
        image_host_client: Optional[Any] = None,
        schema_exporter: Optional[IStudySchemaExporter] = None,
        split_threshold_chars: int = 30000,
        split_threshold_slides: int = 50,
    ):
        self.readers = readers
        self.llm_client = llm_client
        self.notion_client = notion_client
        self.state_repo = state_repo
        self.staging_storage = staging_storage
        self.visual_extractor = visual_extractor
        self.image_host_client = image_host_client
        self.schema_exporter = schema_exporter
        self.split_threshold_chars = split_threshold_chars
        self.split_threshold_slides = split_threshold_slides

    def _process_figures(self, markdown_text: str, document: Document, target: NotionTarget) -> str:
        """
        Intercetta i marker `figure://slide_X` nel markdown testuale,
        esegue l'estrazione visiva, carica su R2 in gerarchia e sostituisce l'URL.
        """
        import re
        import uuid
        
        # Pattern: ![alt](figure://slide_X) o ![alt](figure://slide_X?crop=ymin,xmin,ymax,xmax)
        pattern = re.compile(r'!\[([^\]]*)\]\(figure://slide_(\d+)(?:\?crop=([\d.]+),([\d.]+),([\d.]+),([\d.]+))?\)')
        
        if not self.visual_extractor or not self.image_host_client:
            # Fallback antifragile: convertiamo in testo se manca il setup
            return pattern.sub(r'> 📷 **\1** *(Figura alla slide \2)*', markdown_text)
            
        def replacer(match):
            alt_text = match.group(1)
            page_num = int(match.group(2))
            
            crop_box = None
            if match.group(3):
                try:
                    crop_box = (
                        float(match.group(3)),
                        float(match.group(4)),
                        float(match.group(5)),
                        float(match.group(6)),
                    )
                except ValueError:
                    pass
            
            # ARCHITETTURA: Identificatore crittografico deterministico della figura.
            # Rende il processo 100% idempotente legando l'asset al file_hash, numero slide e crop box.
            crop_sig = f"{crop_box}" if crop_box else "full"
            raw_sig = f"{document.file_hash}_{page_num}_{crop_sig}"
            img_id = hashlib.sha256(raw_sig.encode("utf-8")).hexdigest()[:16]

            # Sanitizzazione del nome corso per URL safe (rimozione spazi, lower)
            course_slug = target.course_name.lower().replace(" ", "_").replace("/", "-")
            remote_name = f"notion/universita/{course_slug}/{img_id}.png"

            # PERFORMANCE: Controllo esistenza su Storage remoto (Cloudflare R2 / S3)
            if hasattr(self.image_host_client, "image_exists") and self.image_host_client.image_exists(remote_name):
                public_url = self.image_host_client.get_public_url(remote_name)
                print(f"    [Cloudflare R2] Figura {img_id[:8]}... già presente su storage — skip upload.")
                return f"![{alt_text}]({public_url})"

            # Controllo cache su disco locale (staging/figures/)
            tmp_dir = Path("staging/figures")
            tmp_dir.mkdir(parents=True, exist_ok=True)
            tmp_path = tmp_dir / f"{img_id}.png"

            try:
                if tmp_path.exists() and tmp_path.stat().st_size > 0:
                    print(f"    [Local] Figura {img_id[:8]}... già presente in staging — skip rendering.")
                else:
                    print(f"    [Local] Estrazione visiva {img_id[:8]}... da slide {page_num}")
                    self.visual_extractor.extract_figure(document, page_num, crop_box, tmp_path)

                # Upload su Storage con path gerarchico: notion/universita/{course_name}/
                print(f"    [Cloudflare R2] Caricamento {remote_name}...")
                public_url = self.image_host_client.upload_image(tmp_path, remote_name)

                return f"![{alt_text}]({public_url})"
            except Exception as e:
                print(f"    [Errore] Fallita estrazione/caricamento figura slide {page_num}: {e}")
                return f"> 📷 **{alt_text}** *(Errore estrazione slide {page_num})*"
                
        return pattern.sub(replacer, markdown_text)

    def _calculate_payload_density(self, document: Document, payload: Any) -> int:
        """
        # ARCHITETTURA: Calcolo deterministico della densità testuale effettiva (Substance-Driven).
        # STATISTICA: Il numero grezzo di slide è un proxy fallace (es. 80 slide da 15 parole = 1.200 parole totali,
        # un volume leggero che non giustifica una seconda chiamata API né rischia saturazione output).
        # Calcoliamo i caratteri testuali reali estratti per misurare la reale complessità cognitiva.
        """
        if isinstance(payload, str):
            return len(payload.strip())

        if isinstance(payload, list):
            # Somma il testo da liste di stringhe o dal dual-payload PPTX [notes_markdown, uploaded_pdf]
            total_chars = sum(len(x.strip()) for x in payload if isinstance(x, str))
            if total_chars > 0:
                return total_chars

        # Per PDF caricati via File API (dove payload è genai_types.File), ispezioniamo il PDF locale con PyMuPDF (<20ms)
        if document.path.exists() and document.path.suffix.lower() == ".pdf":
            try:
                import fitz
                with fitz.open(document.path) as doc:
                    return sum(len(page.get_text().strip()) for page in doc)
            except Exception:
                pass

        return 0

    def execute(self, document: Document, target: NotionTarget, prompt: str) -> ProcessingResult:
        file_hash = document.file_hash
        entry = self.state_repo.get_entry(file_hash)

        # 1. Idempotency Check
        if entry and entry.status == SyncStatus.SYNCED:
            print("    [Local] File già sincronizzato (Hash invariato) — skip.\n")
            return ProcessingResult(document=document, success=True, page_id=entry.page_id, skipped=True)

        # 2. Self-Healing Rollback
        if entry and entry.status == SyncStatus.SYNCING:
            if entry.page_id:
                print(f"    [Rollback] Rilevato caricamento incompleto. Archiviazione pagina orfana ({entry.page_id})...")
                self.notion_client.archive_page(entry.page_id)
            self.state_repo.remove_entry(file_hash)

        # 3. Extraction & Inference (Staging Cache)
        if self.staging_storage.exists(file_hash):
            print("    [Local] Markdown già presente in staging. Salto inference LLM.")
            markdown_text = self.staging_storage.read(file_hash) or ""
        else:
            reader = self.readers.get(document.doc_type) or self.readers[DocumentType.SLIDES]
            payload = reader.read(document)
            try:
                # ARCHITETTURA: Adaptive Dispatcher (Single-Call vs Two-Stage)
                # Trade-off: Garantisce 1 sola chiamata per documenti standard (<40k caratteri di sostanza reale),
                # attivando 2 chiamate solo per documenti massivi per prevenire la saturazione del limite
                # di output tokens (8k) di Gemini ed evitare la diluizione della qualità analitica.
                density_chars = self._calculate_payload_density(document, payload)
                is_heavy = density_chars >= self.split_threshold_chars

                if is_heavy:
                    print(f"    [Adaptive LLM] Rilevato volume elevato ({density_chars} caratteri >= soglia {self.split_threshold_chars}). Attivazione Two-Stage antifragile...")
                    print("    [LLM Stage 1/2] Sintesi capitolo ad alta risoluzione...")
                    markdown_text = self.llm_client.generate_notes(prompt, payload)

                    print("    [LLM Stage 2/2] Estrazione schemi concettuali e drills da staging markdown...")
                    artifacts_prompt = get_artifacts_extraction_prompt(target.course_name, markdown_text)
                    artifacts_text = self.llm_client.generate_notes(artifacts_prompt, markdown_text)

                    # Unione deterministica dei blocchi
                    markdown_text = f"{markdown_text.rstrip()}\n\n{artifacts_text.lstrip()}"
                else:
                    print(f"    [LLM Single-Call] Volume moderato ({density_chars} caratteri < soglia {self.split_threshold_chars}). Generazione note unificate (1 sola chiamata)...")
                    markdown_text = self.llm_client.generate_notes(prompt, payload)

                print(f"    [LLM] Ricevuti {len(markdown_text)} caratteri. Salvataggio in staging...")
                self.staging_storage.save(file_hash, markdown_text)
            finally:
                reader.cleanup(payload)

        # 3.1 Esportazione Schemi Concettuali & Mappe Mentali (EdrawMind / OPML)
        # PERFORMANCE: Esecuzione deterministica a costo zero token su CPU locale
        if self.schema_exporter:
            try:
                artifact = self.schema_exporter.extract_artifacts(markdown_text, file_hash, document.stem)
                schema_dir = Path("staging/schemas")
                schema_dir.mkdir(parents=True, exist_ok=True)
                opml_file = schema_dir / f"{file_hash}.opml"
                opml_file.write_text(artifact.opml_content or "", encoding="utf-8")
                print(f"    [EdrawMind] Mappa OPML esportata in {opml_file}")
            except Exception as e:
                print(f"    [EdrawMind] Warning: esportazione OPML non riuscita: {e}")

        # Nuova Fase Intermedia: Sostituzione dinamica figure (con path gerarchico)
        markdown_text = self._process_figures(markdown_text, document, target)

        # 4. Notion Loading
        print("    [Notion] Creazione pagina...")
        page_id = self.notion_client.create_page(target.database_id, document.stem)

        # Mark as SYNCING
        self.state_repo.set_entry(SyncEntry(file_hash=file_hash, status=SyncStatus.SYNCING, page_id=page_id))

        # Build and append blocks
        blocks = build_notion_blocks(markdown_text)
        self.notion_client.append_blocks(page_id, blocks)

        # Mark as SYNCED
        self.state_repo.set_entry(SyncEntry(file_hash=file_hash, status=SyncStatus.SYNCED, page_id=page_id))
        print(f"    [Notion] OK — {len(blocks)} blocchi archiviati.\n")

        return ProcessingResult(document=document, success=True, page_id=page_id, skipped=False)

