import sys
import time
import pathlib
from typing import List, Dict, Any, Tuple

from src.core.domain.models import Document, DocumentType, NotionTarget
from src.core.domain.prompt_templates import get_prompt_template
from src.core.usecases.process_document import ProcessDocumentUseCase, compute_file_hash
from src.ports.outbound.notion_client_port import INotionClient
from src.ports.outbound.llm_client_port import ILlmClient

SLEEP_BETWEEN_FILES = 5

class CLIAdapter:
    """
    Inbound CLI Adapter.
    Guides the user through interactive setup, Notion course navigation, and batch execution.
    """
    def __init__(
        self,
        notion_client: INotionClient,
        llm_client: ILlmClient,
        usecase: ProcessDocumentUseCase,
        root_page_id: str,
    ):
        self.notion_client = notion_client
        self.llm_client = llm_client
        self.usecase = usecase
        self.root_page_id = root_page_id

    def _pick(self, items: List[Dict[str, Any]], label: str) -> Dict[str, Any]:
        print(f"\n  {label} ({len(items)}):\n")
        for i, item in enumerate(items, 1):
            print(f"    [{i:>2}] {item['title']}")
        print()
        while True:
            raw = input(f"  Numero [1-{len(items)}]: ").strip()
            if raw.isdigit() and 1 <= int(raw) <= len(items):
                chosen = items[int(raw) - 1]
                print(f"  -> \"{chosen['title']}\"")
                return chosen
            print("  [!] Valore non valido.")

    def navigate_to_target(self, subject: str = "") -> NotionTarget:
        print("\n" + "=" * 58)
        print("  SELEZIONE CORSO E DATABASE NOTION")
        print("=" * 58)

        while True:
            print("\n  Recupero corsi...")
            courses = self.notion_client.fetch_courses(self.root_page_id)
            if not courses:
                raise RuntimeError(
                    "Nessun corso trovato nel database Courses. "
                    "Controlla che l'integrazione abbia accesso alla pagina."
                )

            # Auto-selection by partial match
            auto_match = None
            if subject:
                subject_clean = subject.strip().lower()
                for c in courses:
                    if subject_clean in c["title"].strip().lower():
                        auto_match = c
                        break

            if auto_match:
                course = auto_match
                print(f"  Corso selezionato automaticamente: \"{course['title']}\"")
            else:
                course = self._pick(courses, "CORSI DISPONIBILI")

            print(f"\n  Recupero sezioni in '{course['title']}'...")
            targets = self.notion_client.fetch_targets_in_course(course["id"])

            if not targets:
                print(f"\n  [!] Nessuna sezione trovata in '{course['title']}'.")
                if input("  Scegli un altro corso? [s/n]: ").strip().lower() == "s":
                    continue
                raise RuntimeError("Nessuna sezione trovata. Operazione annullata.")

            # Auto-select 'Notes' section if present
            auto_db = next((t for t in targets if t["title"].strip().lower() == "notes"), None)
            if auto_db:
                target = auto_db
                print(f"  Sezione selezionata automaticamente: \"{target['title']}\"")
            else:
                target = self._pick(targets, f"SEZIONI IN '{course['title'].upper()}'")

            db_id = self.notion_client.resolve_database_id(target)
            return NotionTarget(
                database_id=db_id,
                course_name=course["title"],
                database_title=target["title"],
            )

    def setup_session(self) -> Tuple[pathlib.Path, DocumentType, NotionTarget, str]:
        print("\n" + "=" * 58)
        print("  CONFIGURAZIONE PROMPT & DOCUMENTO")
        print("=" * 58)

        subject = input("  Materia del corso (es. Statistical Modelling): ").strip()
        while not subject:
            print("  [!] Campo obbligatorio.")
            subject = input("  Materia del corso: ").strip()

        print()
        print("  Tipo di professore — descrive il ruolo accademico del modello.")
        print(f"  Lascia vuoto per usare il default: 'PhD Professor in {subject}'")
        professor_type = input("  Tipo professore: ").strip()
        if not professor_type:
            professor_type = f"PhD Professor in {subject}"

        print("\n  Tipologia di documento:")
        print("    [1] Slide di lezione (Visual/Multimodale — grafici, diagrammi, espansione pedagogica)")
        print("    [2] Paper / Libro / Dispensa (Estrazione analitica locale — sintesi rigorosa, dimostrazioni)")
        doc_type_choice = input("  Scelta [1/2, default: 1]: ").strip()
        if doc_type_choice == "2":
            doc_type = DocumentType.PAPER_OR_BOOK
        else:
            doc_type = DocumentType.SLIDES

        prompt = get_prompt_template(doc_type.value, subject, professor_type)

        print("\n" + "=" * 58)
        print("  CARTELLA PDF")
        print("=" * 58)
        while True:
            raw = input("  Percorso (supporta ~): ").strip()
            folder = pathlib.Path(raw).expanduser().resolve()
            if not folder.is_dir():
                print(f"  [!] '{folder}' non trovata. Riprova.")
                continue
            pdfs = sorted(folder.glob("*.pdf"))
            if not pdfs:
                print(f"  [!] Nessun PDF in '{folder}'. Riprova.")
                continue
            print(f"  Trovati {len(pdfs)} PDF.")
            break

        target = self.navigate_to_target(subject)

        print("\n" + "-" * 58)
        print(f"  Materia     : {subject}")
        print(f"  Professore  : {professor_type}")
        print(f"  Tipo Doc    : {doc_type.value.upper()}")
        print(f"  Cartella    : {folder}")
        print(f"  Corso Notion: {target.course_name}")
        print(f"  Database    : {target.database_title}")
        print(f"  PDF         : {len(pdfs)} file")
        print("-" * 58)

        return folder, doc_type, target, prompt

    def run_batch(
        self,
        folder: pathlib.Path,
        doc_type: DocumentType,
        target: NotionTarget,
        prompt: str,
    ) -> Tuple[int, int]:
        pdf_files = sorted(folder.glob("*.pdf"))
        total = len(pdf_files)
        success = 0

        print(f"\n{'=' * 58}")
        print(f"  ELABORAZIONE: {total} file  |  {target.course_name} > {target.database_title}")
        print(f"{'=' * 58}\n")

        for index, pdf_path in enumerate(pdf_files, start=1):
            print(f"  [{index:>2}/{total}] {pdf_path.stem}.pdf")
            try:
                file_hash = compute_file_hash(pdf_path)
                doc = Document(path=pdf_path, file_hash=file_hash, doc_type=doc_type)

                result = self.usecase.execute(doc, target, prompt)
                if result.success:
                    success += 1

                if index == 1 and total > 1:
                    print(f"\n  Primo file completato. Controlla la pagina su Notion.")
                    print(f"  Rimangono {total - 1} file da elaborare.")
                    go = input("  Continuare con gli altri? [s/n]: ").strip().lower()
                    if go != "s":
                        print("  Elaborazione interrotta dall'utente.")
                        break

            except RuntimeError as exc:
                print(f"\n  [STOP] {exc}")
                break
            except Exception as exc:
                print(f"    [ERRORE] {exc}\n")

            if index < total:
                print(f"    Pausa {SLEEP_BETWEEN_FILES}s...")
                time.sleep(SLEEP_BETWEEN_FILES)
                print()

        return success, total

    def start(self) -> None:
        remaining = self.llm_client.get_remaining_calls()
        print(f"\n  [LLM] Chiamate disponibili oggi: {remaining}")
        if remaining <= 0:
            print("  [!] Limite giornaliero raggiunto. Riprova domani.")
            sys.exit(1)

        session_success = 0
        session_total = 0

        while True:
            try:
                folder, doc_type, target, prompt = self.setup_session()
            except (RuntimeError, KeyboardInterrupt) as exc:
                print(f"\n  Setup annullato: {exc}")
                break

            pdf_count = len(sorted(folder.glob("*.pdf")))
            remaining = self.llm_client.get_remaining_calls()
            if pdf_count > remaining:
                print(
                    f"\n  Attenzione: {pdf_count} PDF ma solo {remaining} chiamate "
                    f"disponibili oggi.\n  Lo script si fermerà al raggiungimento del limite."
                )

            s, t = self.run_batch(folder, doc_type, target, prompt)
            session_success += s
            session_total += t

            print(f"\n  Risultato: {s}/{t} file archiviati su Notion.")
            print("\n" + "-" * 58)
            again = input("  Elaborare un altro corso? [s/n]: ").strip().lower()
            if again != "s":
                break
            print()

        print(f"\n{'=' * 58}")
        print(f"  Sessione terminata.")
        print(f"  File archiviati     : {session_success}/{session_total}")
        print(f"  Chiamate residue    : {self.llm_client.get_remaining_calls()}")
        print(f"{'=' * 58}\n")
