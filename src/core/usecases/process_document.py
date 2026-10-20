import hashlib
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

from src.core.domain.models import (
    Document,
    DocumentType,
    SyncStatus,
    SyncEntry,
    ProcessingResult,
    NotionTarget,
    GenerationMode,
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
        split_threshold_chars: int = 25000,
        split_threshold_slides: Optional[int] = 35,
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
        # ARCHITETTURA: Intercettore universale antifragile di marker visivi `figure://slide_X`.
        # Cattura sia la sintassi formale standalone (`![Alt](figure://...)`), sia riferimenti
        # parentetici inline allucinati dall'LLM (`(figure://...)` o `figure://...`).
        # Risolve l'impedance mismatch con il Block Model di Notion:
        # in Notion le immagini non possono vivere inline dentro `rich_text`, pertanto
        # le figure inline vengono referenziate in modo pulito nel testo e sollevate come blocchi
        # immagine autonomi a livello radice (`type: "image"`).
        """
        import re

        # Regex modulare con named groups per intercettare qualsiasi variante sintattica di figure://
        figure_pattern = re.compile(
            r'(?:'
            r'!?\[(?P<alt>[^\]]*)\]\(figure://slide_(?P<slide1>\d+)(?:\?crop=(?P<c1_ymin>[\d.]+),(?P<c1_xmin>[\d.]+),(?P<c1_ymax>[\d.]+),(?P<c1_xmax>[\d.]+))?\)'
            r'|'
            r'\(\s*figure://slide_(?P<slide2>\d+)(?:\?crop=(?P<c2_ymin>[\d.]+),(?P<c2_xmin>[\d.]+),(?P<c2_ymax>[\d.]+),(?P<c2_xmax>[\d.]+))?\s*\)'
            r'|'
            r'figure://slide_(?P<slide3>\d+)(?:\?crop=(?P<c3_ymin>[\d.]+),(?P<c3_xmin>[\d.]+),(?P<c3_ymax>[\d.]+),(?P<c3_xmax>[\d.]+))?'
            r')'
        )

        def parse_figure_match(m: re.Match) -> Tuple[str, int, Optional[Tuple[float, float, float, float]]]:
            alt = m.group("alt")
            slide = m.group("slide1") or m.group("slide2") or m.group("slide3")
            page_num = int(slide)

            ymin = m.group("c1_ymin") or m.group("c2_ymin") or m.group("c3_ymin")
            xmin = m.group("c1_xmin") or m.group("c2_xmin") or m.group("c3_xmin")
            ymax = m.group("c1_ymax") or m.group("c2_ymax") or m.group("c3_ymax")
            xmax = m.group("c1_xmax") or m.group("c2_xmax") or m.group("c3_xmax")

            crop_box = None
            if ymin and xmin and ymax and xmax:
                try:
                    crop_box = (float(ymin), float(xmin), float(ymax), float(xmax))
                except ValueError:
                    crop_box = None

            if not alt or not alt.strip():
                alt = f"Figura slide {page_num}"

            return alt.strip(), page_num, crop_box

        def resolve_figure_url(page_num: int, crop_box: Optional[Tuple[float, float, float, float]]) -> Optional[str]:
            if not self.visual_extractor or not self.image_host_client:
                return None

            # ARCHITETTURA: Prevenzione immagini tagliate su presentazioni slide.
            # Sulle slide, coordinate arbitrarie di crop ipotizzate dall'LLM tagliano frequentemente
            # assi cartesiani, anni e note a piè di pagina (es. confronti prima/dopo su slide 8).
            # L'estrazione a slide intera a 300 DPI garantisce la totale integrità e completezza visiva.
            if document.doc_type == DocumentType.SLIDES:
                crop_box = None

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
                return public_url

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
                return public_url
            except Exception as e:
                print(f"    [Errore] Fallita estrazione/caricamento figura slide {page_num}: {e}")
                return None

        lines = markdown_text.splitlines()
        processed_lines = []

        for line in lines:
            matches = list(figure_pattern.finditer(line))
            if not matches:
                processed_lines.append(line)
                continue

            s = line.strip()
            # TRADE-OFF: Se la riga intera è ESCLUSIVAMENTE un riferimento alla figura,
            # preserviamo la semantica di blocco Markdown standard senza didascalie boilerplate.
            if figure_pattern.fullmatch(s):
                alt, page_num, crop_box = parse_figure_match(matches[0])
                url = resolve_figure_url(page_num, crop_box)
                if url:
                    processed_lines.append(f"![]({url})")
                continue

            # Se la riga contiene testo discorsivo con uno o più marker di figura inline
            standalone_figures = []
            seen_slides = set()

            def inline_replacer(m: re.Match) -> str:
                alt, page_num, crop_box = parse_figure_match(m)
                if page_num not in seen_slides:
                    url = resolve_figure_url(page_num, crop_box)
                    if url:
                        seen_slides.add(page_num)
                        standalone_figures.append(url)
                # Rimuove integralmente qualsiasi dicitura o citazione dal testo
                return ""

            cleaned_line = figure_pattern.sub(inline_replacer, line)
            # Rimuove eventuali diciture residue orfane nel testo (es. "(figura 8)", "*(Slide 8)*", ecc.)
            cleaned_line = re.sub(r"\*?\*?\((?:slide|figura)\s*\d+\)\*?\*?", "", cleaned_line, flags=re.IGNORECASE)
            # Preserva l'indentazione originale rimuovendo doppi spazi e spazi pre-punteggiatura
            indent = len(cleaned_line) - len(cleaned_line.lstrip(" "))
            body = re.sub(r"[ \t]+", " ", cleaned_line.lstrip(" "))
            body = re.sub(r"\s+([,.;:!?])", r"\1", body)
            cleaned_line = (" " * indent) + body.rstrip()
            processed_lines.append(cleaned_line)

            # Solleviamo ogni figura a blocco immagine autonomo Notion compatibile
            # Senza alt-text/caption per eliminare qualsiasi dicitura al di sotto dell'immagine
            for url in standalone_figures:
                processed_lines.append("")
                processed_lines.append(f"![]({url})")

        res = "\n".join(processed_lines)
        if markdown_text.endswith("\n"):
            res += "\n"
        return res

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

    @staticmethod
    def _split_notes_and_artifacts(markdown_text: str) -> Tuple[str, str]:
        """
        # ARCHITETTURA: Scomposizione deterministica tra corpo del testo accademico
        # e schemi concettuali relazionali (Mermaid mindmap/flowchart, active recall, boundary matrix).
        """
        import re
        pattern = r"(?:\n|^)(?:---\s*\n)?(##\s*[^\n]*(?:Conceptual Architecture|Relational Graphs|Active Recall|Model Boundary)[\s\S]*)"
        m = re.search(pattern, markdown_text, re.IGNORECASE)
        if m:
            idx = m.start(1)
            notes = markdown_text[:idx].rstrip()
            notes = re.sub(r"\n---\s*$", "", notes).rstrip()
            artifacts = markdown_text[idx:].lstrip()
            return notes, artifacts
        return markdown_text.strip(), ""

    def _count_slides(self, document: Document) -> int:
        """
        # PERFORMANCE: Rilevamento istantaneo (<10ms) del conteggio totale slide.
        # Ispeziona PDF tramite PyMuPDF o PPTX tramite python-pptx / rendering staging.
        """
        if not document.path.exists():
            return 0

        ext = document.path.suffix.lower()
        if ext == ".pdf":
            try:
                import fitz
                with fitz.open(document.path) as doc_pdf:
                    return len(doc_pdf)
            except Exception:
                pass
        elif ext == ".pptx":
            try:
                from pptx import Presentation
                prs = Presentation(document.path)
                return len(prs.slides)
            except Exception:
                pass
        return 0

    def _get_slide_character_counts(self, document: Document) -> List[int]:
        """
        # PERFORMANCE: Estrazione rapida (<20ms) del volume testuale per singola slide.
        # STATISTICA: Consente la misurazione della densità informativa non uniforme lungo il mazzo,
        # separando slide sparse (titoli/separatori, <100 car) da slide dense (codice/formule, >1500 car).
        """
        if not document.path.exists():
            return []

        ext = document.path.suffix.lower()
        if ext == ".pdf":
            try:
                import fitz
                with fitz.open(document.path) as doc_pdf:
                    return [len(page.get_text().strip()) for page in doc_pdf]
            except Exception:
                pass
        elif ext == ".pptx":
            cached_pdf = Path("staging") / f"{document.file_hash}_slides.pdf"
            if cached_pdf.exists():
                try:
                    import fitz
                    with fitz.open(cached_pdf) as doc_pdf:
                        return [len(page.get_text().strip()) for page in doc_pdf]
                except Exception:
                    pass
            try:
                from pptx import Presentation
                prs = Presentation(document.path)
                counts: List[int] = []
                from src.adapters.outbound.document_readers.pptx_extractor import _iter_shapes_recursive
                for slide in prs.slides:
                    text_parts = []
                    for shape in _iter_shapes_recursive(slide.shapes):
                        if getattr(shape, "has_text_frame", False) and shape.text_frame:
                            text_parts.append(shape.text_frame.text)
                        elif getattr(shape, "has_table", False) and shape.table:
                            for row in shape.table.rows:
                                text_parts.extend(cell.text for cell in row.cells)
                    counts.append(len(" ".join(text_parts).strip()))
                return counts
            except Exception:
                pass
        return []

    def _partition_slides_by_character_budget(
        self,
        slide_char_counts: List[int],
        max_chunk_chars: int,
    ) -> List[Tuple[int, int]]:
        """
        # ARCHITETTURA: Partizionamento bilanciato delle slide basato sulla densità informativa (caratteri).
        # STATISTICA: Minimizza la varianza del carico informativo tra le tranche di slide,
        # raggruppando slide contigue fino al raggiungimento di un volume bilanciato (~target_per_chunk).
        # Previene la saturazione dell'output token envelope (8.192 token) allocando budget omogenei.
        """
        import math
        total_slides = len(slide_char_counts)
        if total_slides <= 1:
            return [(1, total_slides)]

        total_chars = sum(slide_char_counts)
        # Fallback per mazzi puramente grafici o scansionati privi di testo vettoriale
        if total_chars == 0:
            half = math.ceil(total_slides / 2)
            return [(1, half), (half + 1, total_slides)]

        num_chunks = max(2, math.ceil(total_chars / max_chunk_chars))
        num_chunks = min(num_chunks, total_slides)
        target_per_chunk = total_chars / num_chunks

        chunk_ranges: List[Tuple[int, int]] = []
        current_start = 1
        current_chars = 0

        for slide_idx, count in enumerate(slide_char_counts):
            slide_num = slide_idx + 1
            current_chars += count
            remaining_slides = total_slides - slide_num
            chunks_left = num_chunks - len(chunk_ranges)

            must_cut = (remaining_slides == chunks_left - 1)
            reached_target = (current_chars >= target_per_chunk and remaining_slides >= (chunks_left - 1))

            if chunks_left > 1 and (reached_target or must_cut):
                if must_cut:
                    chunk_ranges.append((current_start, slide_num))
                    current_start = slide_num + 1
                    current_chars = 0
                else:
                    prev_diff = abs((current_chars - count) - target_per_chunk)
                    curr_diff = abs(current_chars - target_per_chunk)
                    if prev_diff < curr_diff and (slide_num - 1) >= current_start and (total_slides - (slide_num - 1)) >= chunks_left:
                        chunk_ranges.append((current_start, slide_num - 1))
                        current_start = slide_num
                        current_chars = count
                    else:
                        chunk_ranges.append((current_start, slide_num))
                        current_start = slide_num + 1
                        current_chars = 0

        chunk_ranges.append((current_start, total_slides))
        return chunk_ranges

    @staticmethod
    def _extract_chunk_symbolic_anchor(notes_markdown: str) -> str:
        """
        # ARCHITETTURA: Estrazione rapida (<1ms) dello stato concettuale e notazionale attivo (Zero-Slop Anchor).
        # STATISTICA: Isola i modelli formalizzati (H2/H3) e le equazioni chiave ($$...$$) per passarli
        # come invarianti vincolanti al chunk successivo.
        # TRADE-OFF: Mantiene il contesto a meno di 10-12 righe, prevenendo sia il notational drift sia la
        # proliferazione di rispiegazioni e preamboli tautologici.
        """
        import re
        if not notes_markdown or not notes_markdown.strip():
            return ""

        headers = []
        for line in notes_markdown.splitlines():
            line_str = line.strip()
            if line_str.startswith("## ") or line_str.startswith("### "):
                clean_title = re.sub(r"^#{2,3}\s*([^\w\s]+\s*)?", "", line_str).strip()
                if clean_title and clean_title not in headers and not clean_title.lower().startswith("references"):
                    headers.append(clean_title)

        eq_pattern = re.compile(r"\$\$([^\$]+)\$\$")
        equations = []
        for match in eq_pattern.finditer(notes_markdown):
            eq = match.group(1).strip()
            eq_clean = " ".join(eq.split())
            if eq_clean and eq_clean not in equations and len(eq_clean) <= 120:
                equations.append(eq_clean)

        lines = []
        if headers:
            recent_headers = headers[-6:]
            lines.append(f"- Established Models/Topics: {', '.join(recent_headers)}")
        if equations:
            recent_eqs = equations[-4:]
            eqs_formatted = " | ".join(f"${e}$" for e in recent_eqs)
            lines.append(f"- Active Parameter Formulations: {eqs_formatted}")

        return "\n".join(lines)

    @staticmethod
    def _slice_pdf_pages(input_path: Path, pages: List[int], output_path: Path) -> None:
        """
        # PERFORMANCE: Estrazione vettoriale lossless di un range di pagine tramite PyMuPDF (<20ms).
        """
        import fitz
        doc = fitz.open(str(input_path))
        new_doc = fitz.open()
        for p in pages:
            new_doc.insert_pdf(doc, from_page=p - 1, to_page=p - 1)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        new_doc.save(str(output_path))
        new_doc.close()
        doc.close()

    def _process_windowed_slides(
        self,
        document: Document,
        target: NotionTarget,
        prompt: str,
        slide_char_counts: List[int],
        generation_mode: GenerationMode,
    ) -> str:
        """
        # ARCHITETTURA: Windowed Multi-Call Slide Chunker Character-Driven.
        # TRADE-OFF: Risolve definitivamente la saturazione dell'output token budget (8.192 token).
        # Suddivide presentazioni massive in K segmenti bilanciati sul volume reale di caratteri, allocando
        # un intero budget di output dedicato per ogni tranche di slide per garantire
        # massima profondità analitica, formule, codici e zero omissioni o salti di slide.
        """
        reader = self.readers.get(document.doc_type) or self.readers[DocumentType.SLIDES]
        total_slides = len(slide_char_counts) if slide_char_counts else self._count_slides(document)
        total_chars = sum(slide_char_counts) if slide_char_counts else self._calculate_payload_density(document, None)

        chunk_ranges = self._partition_slides_by_character_budget(
            slide_char_counts=slide_char_counts,
            max_chunk_chars=self.split_threshold_chars,
        )

        print(
            f"    [Adaptive Character Chunker] Rilevati {total_chars} caratteri distribuiti su {total_slides} slide. "
            f"Partizionamento pesato sui caratteri in {len(chunk_ranges)} tranche bilanciate..."
        )

        # Determina il PDF sorgente per il slicing vettoriale
        source_pdf = document.path
        if document.path.suffix.lower() == ".pptx":
            cached_pdf = Path("staging") / f"{document.file_hash}_slides.pdf"
            if cached_pdf.exists():
                source_pdf = cached_pdf

        chunk_results = []
        chunks_dir = Path("staging/chunks")
        chunks_dir.mkdir(parents=True, exist_ok=True)
        cumulative_anchor = ""

        for chunk_idx, (start_p, end_p) in enumerate(chunk_ranges):
            chunk_chars = sum(slide_char_counts[start_p - 1:end_p]) if slide_char_counts else 0
            print(f"    [LLM Chunk {chunk_idx + 1}/{len(chunk_ranges)}] Generazione note per slide {start_p}-{end_p} ({chunk_chars} caratteri)...")
            chunk_pdf = chunks_dir / f"{document.file_hash}_chunk_{chunk_idx + 1}_{start_p}_{end_p}.pdf"

            if not chunk_pdf.exists() or chunk_pdf.stat().st_size == 0:
                self._slice_pdf_pages(source_pdf, list(range(start_p, end_p + 1)), chunk_pdf)

            chunk_doc = Document(
                path=chunk_pdf,
                file_hash=f"{document.file_hash}_c{chunk_idx + 1}_{start_p}_{end_p}",
                doc_type=DocumentType.SLIDES,
            )
            chunk_payload = reader.read(chunk_doc)

            try:
                continuity_directive = ""
                if chunk_idx > 0 and cumulative_anchor:
                    continuity_directive = (
                        f"\n=== ACTIVE NOTATIONAL & CONCEPTUAL STATE (DO NOT RE-EXPLAIN) ===\n"
                        f"The following models, parameters, and notation were established in prior slides:\n"
                        f"{cumulative_anchor}\n"
                        f"- ASSUME all notation, variables, and properties listed above are already proven and active. Do NOT re-define them.\n"
                        f"- Advance concepts strictly via DIRECT TECHNICAL DELTAS (stating in 1 direct sentence the exact formal limit or failure of the preceding model this new model resolves). Zero rhetorical or conversational transition padding.\n"
                        f"- Maintain identical analytical, mathematical, and computational caliber (formal hypotheses, structural parameters, test statistics).\n"
                        f"- Preserve full pedagogical depth: anchor newly introduced diagnostics or empirical tests to the statistical mechanisms established in prior chunks, explaining the exact econometric reason for any parameter transformations, circular dilemmas, or distributional shifts.\n"
                        f"- Progressive Narrative Threading (Zero Alienation): Do NOT isolate or detach this chunk from prior material. Weave it seamlessly into the cumulative analytical thread by referencing established outcomes as active, proven premises in a single concise clause, advancing immediately to the new technical delta without duplicating definitions or re-explaining established models.\n"
                    )

                chunk_prompt = (
                    f"{prompt}\n\n"
                    f"=== SLIDE RANGE DIRECTIVE (CHUNK {chunk_idx + 1}/{len(chunk_ranges)}) ===\n"
                    f"This document slice contains slides {start_p} to {end_p} of the complete lecture deck.\n"
                    f"- Synthesize ALL topics, code snippets, hardware/mathematical mechanisms, and empirical examples from slides {start_p} to {end_p} with maximum academic rigor.\n"
                    f"- When inserting visual diagrams (e.g. ![](figure://slide_N)), ALWAYS use the absolute original slide number N (between {start_p} and {end_p}) visible on the slide footer, NEVER the relative page index of this slice.\n"
                    f"- Do NOT generate final global closing artifacts (no Conceptual Architecture Mermaid trees, no Active Recall drills, no Boundary Conditions table); these will be synthesized globally across the entire lecture at the end.\n"
                    f"- Output ONLY the substantive study sections (## and ###) for slides {start_p} through {end_p} without conversational padding."
                    f"{continuity_directive}"
                )

                chunk_text = self.llm_client.generate_notes(chunk_prompt, chunk_payload)
                notes_part, _ = self._split_notes_and_artifacts(chunk_text)
                chunk_results.append(notes_part.strip())
                cumulative_anchor = self._extract_chunk_symbolic_anchor("\n\n".join(chunk_results))
            finally:
                reader.cleanup(chunk_payload)

        combined_notes = "\n\n---\n\n".join(chunk_results)

        # Stage 2: Estrazione unificata di schemi concettuali e drills sull'intero materiale aggregato
        if generation_mode != GenerationMode.NOTES_ONLY:
            print("    [LLM Unified Stage 2] Estrazione schemi concettuali e drills da note aggregate...")
            artifacts_prompt = get_artifacts_extraction_prompt(target.course_name, combined_notes)
            artifacts_text = self.llm_client.generate_notes(artifacts_prompt, combined_notes)
            markdown_text = f"{combined_notes.rstrip()}\n\n{artifacts_text.lstrip()}"
        else:
            markdown_text = combined_notes

        return markdown_text

    def execute(
        self,
        document: Document,
        target: NotionTarget,
        prompt: str,
        generation_mode: GenerationMode = GenerationMode.BOTH,
        force: bool = False,
    ) -> ProcessingResult:
        file_hash = document.file_hash
        entry = self.state_repo.get_entry(file_hash)

        # 1. Idempotency Check
        if entry and entry.status == SyncStatus.SYNCED and not force:
            print("    [Local] File già sincronizzato (Hash invariato) — skip.\n")
            return ProcessingResult(document=document, success=True, page_id=entry.page_id, skipped=True)

        # 2. Self-Healing Rollback
        if entry and entry.status == SyncStatus.SYNCING:
            if entry.page_id:
                print(f"    [Rollback] Rilevato caricamento incompleto. Archiviazione pagina orfana ({entry.page_id})...")
                self.notion_client.archive_page(entry.page_id)
            self.state_repo.remove_entry(file_hash)

        if force and entry and entry.page_id:
            try:
                print(f"    [Force] Archiviazione pagina precedente ({entry.page_id})...")
                self.notion_client.archive_page(entry.page_id)
            except Exception:
                pass
            self.state_repo.remove_entry(file_hash)

        # 3. Extraction & Inference (Staging Cache)
        if self.staging_storage.exists(file_hash):
            print("    [Local] Markdown già presente in staging. Salto inference LLM.")
            markdown_text = self.staging_storage.read(file_hash) or ""
            # Se siamo in GRAPHS_ONLY o BOTH e lo staging non contiene ancora gli artefatti concettuali, li estraiamo on-demand
            notes, artifacts = self._split_notes_and_artifacts(markdown_text)
            if generation_mode in (GenerationMode.GRAPHS_ONLY, GenerationMode.BOTH) and not artifacts:
                print("    [LLM] Staging privo di artefatti concettuali. Estrazione schemi da staging markdown...")
                artifacts_prompt = get_artifacts_extraction_prompt(target.course_name, markdown_text)
                artifacts_text = self.llm_client.generate_notes(artifacts_prompt, markdown_text)
                markdown_text = f"{markdown_text.rstrip()}\n\n{artifacts_text.lstrip()}"
                self.staging_storage.save(file_hash, markdown_text)
        else:
            reader = self.readers.get(document.doc_type) or self.readers[DocumentType.SLIDES]
            slide_char_counts = self._get_slide_character_counts(document)
            total_chars = sum(slide_char_counts) if slide_char_counts else self._calculate_payload_density(document, None)
            total_slides = len(slide_char_counts) if slide_char_counts else self._count_slides(document)

            # ARCHITETTURA: Windowed Slide Chunker Character-Driven.
            # STATISTICA: Il controllo opera prioritariamente sul volume totale di caratteri effettivi (substance-driven).
            # Se la presentazione supera la soglia di caratteri (split_threshold_chars, default: 25.000),
            # si attiva il partizionamento delle slide bilanciato sul volume dei caratteri per prevenire
            # la saturazione dell'output token budget LLM (8.192 token).
            should_chunk_slides = (
                document.doc_type == DocumentType.SLIDES
                and total_slides > 1
                and (
                    total_chars > self.split_threshold_chars
                    or (total_chars == 0 and self.split_threshold_slides and total_slides > self.split_threshold_slides)
                )
            )

            if should_chunk_slides:
                markdown_text = self._process_windowed_slides(
                    document=document,
                    target=target,
                    prompt=prompt,
                    slide_char_counts=slide_char_counts,
                    generation_mode=generation_mode,
                )
                print(f"    [LLM] Assemblati {len(markdown_text)} caratteri totali dai chunk. Salvataggio in staging...")
                self.staging_storage.save(file_hash, markdown_text)
            else:
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

                        # In NOTES_ONLY evitiamo Stage 2 per risparmiare token e latenza
                        if generation_mode != GenerationMode.NOTES_ONLY:
                            print("    [LLM Stage 2/2] Estrazione schemi concettuali e drills da staging markdown...")
                            artifacts_prompt = get_artifacts_extraction_prompt(target.course_name, markdown_text)
                            artifacts_text = self.llm_client.generate_notes(artifacts_prompt, markdown_text)
                            markdown_text = f"{markdown_text.rstrip()}\n\n{artifacts_text.lstrip()}"
                    else:
                        print(f"    [LLM Single-Call] Volume moderato ({density_chars} caratteri < soglia {self.split_threshold_chars}). Generazione note...")
                        markdown_text = self.llm_client.generate_notes(prompt, payload)

                    print(f"    [LLM] Ricevuti {len(markdown_text)} caratteri. Salvataggio in staging...")
                    self.staging_storage.save(file_hash, markdown_text)
                finally:
                    reader.cleanup(payload)

        notes, artifacts = self._split_notes_and_artifacts(markdown_text)

        # 3.1 Esportazione Schemi Concettuali & Mappe Mentali (EdrawMind / OPML)
        # In NOTES_ONLY l'esportazione OPML è disattivata (richieste solo note)
        if self.schema_exporter and generation_mode != GenerationMode.NOTES_ONLY:
            try:
                schema_source = markdown_text if artifacts else markdown_text
                artifact = self.schema_exporter.extract_artifacts(schema_source, file_hash, document.stem)
                schema_dir = Path("staging/schemas")
                schema_dir.mkdir(parents=True, exist_ok=True)
                opml_file = schema_dir / f"{file_hash}.opml"
                opml_file.write_text(artifact.opml_content or "", encoding="utf-8")
                print(f"    [EdrawMind] Mappa OPML esportata in {opml_file}")
            except Exception as e:
                print(f"    [EdrawMind] Warning: esportazione OPML non riuscita: {e}")

        # Risoluzione payload markdown in base alla modalità scelta
        if generation_mode == GenerationMode.NOTES_ONLY:
            target_markdown = notes
        elif generation_mode == GenerationMode.GRAPHS_ONLY:
            if artifacts:
                if not artifacts.startswith("#"):
                    target_markdown = f"# {document.stem}\n\n{artifacts}"
                else:
                    target_markdown = artifacts
            else:
                target_markdown = markdown_text
        else:
            target_markdown = markdown_text

        # Nuova Fase Intermedia: Sostituzione dinamica figure (con path gerarchico)
        target_markdown = self._process_figures(target_markdown, document, target)

        # 4. Notion Loading
        print(f"    [Notion] Creazione pagina ({generation_mode.value})...")
        page_id = self.notion_client.create_page(target.database_id, document.stem)

        # Mark as SYNCING
        self.state_repo.set_entry(SyncEntry(file_hash=file_hash, status=SyncStatus.SYNCING, page_id=page_id))

        # Build and append blocks
        blocks = build_notion_blocks(target_markdown)
        self.notion_client.append_blocks(page_id, blocks)

        # Mark as SYNCED
        self.state_repo.set_entry(SyncEntry(file_hash=file_hash, status=SyncStatus.SYNCED, page_id=page_id))
        print(f"    [Notion] OK — {len(blocks)} blocchi archiviati ({generation_mode.value}).\n")

        return ProcessingResult(document=document, success=True, page_id=page_id, skipped=False)

