import sys
import time
import pathlib
from typing import List, Dict, Any, Tuple, Optional

from src.core.domain.models import Document, DocumentType, NotionTarget, CourseProfile
from src.core.domain.prompt_templates import get_prompt_template
from src.core.usecases.process_document import ProcessDocumentUseCase, compute_file_hash
from src.ports.outbound.notion_client_port import INotionClient
from src.ports.outbound.llm_client_port import ILlmClient
from src.ports.outbound.course_profile_repository_port import ICourseProfileRepository

SLEEP_BETWEEN_FILES = 5

SUPPORTED_EXTENSIONS = {".pdf", ".pptx"}

def scan_documents(folder: pathlib.Path) -> List[pathlib.Path]:
    if not folder.is_dir():
        return []
    return sorted([
        p for p in folder.iterdir()
        if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS
    ])

class CLIAdapter:
    """
    Inbound CLI Adapter.
    Guides the user through interactive setup, Notion course navigation, and batch execution.
    Supports both PDF and PPTX slide decks / documents and persistent course profiles.
    """
    def __init__(
        self,
        notion_client: INotionClient,
        llm_client: ILlmClient,
        usecase: ProcessDocumentUseCase,
        root_page_id: str,
        course_profile_repo: Optional[ICourseProfileRepository] = None,
    ):
        self.notion_client = notion_client
        self.llm_client = llm_client
        self.usecase = usecase
        self.root_page_id = root_page_id
        self.course_profile_repo = course_profile_repo

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

    def _validate_or_prompt_folder(self, initial_folder: pathlib.Path) -> Tuple[pathlib.Path, List[pathlib.Path]]:
        folder = initial_folder
        while True:
            if not folder.is_dir():
                print(f"  [!] Cartella '{folder}' non trovata.")
                raw = input("  Inserisci nuovo percorso cartella: ").strip()
                folder = pathlib.Path(raw).expanduser().resolve()
                continue
            docs = scan_documents(folder)
            if not docs:
                print(f"  [!] Nessun file supportato (.pdf / .pptx) in '{folder}'.")
                raw = input("  Inserisci un'altra cartella: ").strip()
                folder = pathlib.Path(raw).expanduser().resolve()
                continue
            return folder, docs

    def _modify_and_use_profile(self, chosen: CourseProfile) -> Tuple[pathlib.Path, DocumentType, NotionTarget, str]:
        print("\n  [Modifica Profilo Corso]")
        raw_subj = input(f"  Materia [{chosen.subject}]: ").strip()
        subject = raw_subj if raw_subj else chosen.subject

        raw_prof = input(f"  Tipo professore [{chosen.professor_type}]: ").strip()
        professor_type = raw_prof if raw_prof else chosen.professor_type

        default_dt = "1" if chosen.doc_type == DocumentType.SLIDES else "2"
        print("  Tipologia di documento:")
        print("    [1] Slide di lezione (Visual/Multimodale per PDF e PPTX — Gemini File API)")
        print("    [2] Paper / Libro / Dispensa (Estrazione analitica locale — sintesi rigorosa, dimostrazioni)")
        doc_type_choice = input(f"  Scelta [1/2, default: {default_dt}]: ").strip() or default_dt
        doc_type = DocumentType.PAPER_OR_BOOK if doc_type_choice == "2" else DocumentType.SLIDES

        raw_folder = input(f"  Cartella [{chosen.folder_path}]: ").strip()
        folder_cand = pathlib.Path(raw_folder).expanduser().resolve() if raw_folder else chosen.folder_path
        folder, docs = self._validate_or_prompt_folder(folder_cand)

        change_target = input("  Vuoi riconfigurare la destinazione Notion? [s/N]: ").strip().lower()
        if change_target in ("s", "si", "y", "yes"):
            target = self.navigate_to_target(subject)
        else:
            target = chosen.target

        prompt = get_prompt_template(doc_type.value, subject, professor_type)

        if self.course_profile_repo:
            save_change = input(f"\n  Salvare le modifiche nel profilo '{subject}'? [S/n]: ").strip().lower()
            if save_change in ("", "s", "si", "y", "yes"):
                updated = CourseProfile(
                    subject=subject,
                    professor_type=professor_type,
                    doc_type=doc_type,
                    folder_path=folder,
                    target=target,
                )
                self.course_profile_repo.save_profile(updated)
                print(f"  [OK] Profilo '{subject}' aggiornato.")

        print("\n" + "-" * 58)
        print(f"  Materia     : {subject}")
        print(f"  Professore  : {professor_type}")
        print(f"  Tipo Doc    : {doc_type.value.upper()}")
        print(f"  Cartella    : {folder}")
        print(f"  Corso Notion: {target.course_name}")
        print(f"  Database    : {target.database_title}")
        print(f"  File trovati: {len(docs)} file (.pdf / .pptx)")
        print("-" * 58)
        return folder, doc_type, target, prompt

    def _manual_setup(self) -> Tuple[pathlib.Path, DocumentType, NotionTarget, str]:
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
        print("    [1] Slide di lezione (Visual/Multimodale per PDF e PPTX — Gemini File API)")
        print("    [2] Paper / Libro / Dispensa (Estrazione analitica locale — sintesi rigorosa, dimostrazioni)")
        doc_type_choice = input("  Scelta [1/2, default: 1]: ").strip()
        if doc_type_choice == "2":
            doc_type = DocumentType.PAPER_OR_BOOK
        else:
            doc_type = DocumentType.SLIDES

        prompt = get_prompt_template(doc_type.value, subject, professor_type)

        print("\n" + "=" * 58)
        print("  CARTELLA DOCUMENTI (PDF / PPTX)")
        print("=" * 58)
        raw_folder = input("  Percorso (supporta ~): ").strip()
        folder_cand = pathlib.Path(raw_folder).expanduser().resolve()
        folder, docs = self._validate_or_prompt_folder(folder_cand)

        target = self.navigate_to_target(subject)

        if self.course_profile_repo:
            save_profile_choice = input(f"\n  Salvare questo profilo come predefinito per '{subject}'? [S/n]: ").strip().lower()
            if save_profile_choice in ("", "s", "si", "y", "yes"):
                new_profile = CourseProfile(
                    subject=subject,
                    professor_type=professor_type,
                    doc_type=doc_type,
                    folder_path=folder,
                    target=target,
                )
                self.course_profile_repo.save_profile(new_profile)
                print(f"  [OK] Profilo '{subject}' memorizzato con successo.")

        print("\n" + "-" * 58)
        print(f"  Materia     : {subject}")
        print(f"  Professore  : {professor_type}")
        print(f"  Tipo Doc    : {doc_type.value.upper()}")
        print(f"  Cartella    : {folder}")
        print(f"  Corso Notion: {target.course_name}")
        print(f"  Database    : {target.database_title}")
        print(f"  File trovati: {len(docs)} file (.pdf / .pptx)")
        print("-" * 58)

        return folder, doc_type, target, prompt

    def setup_session(self) -> Tuple[pathlib.Path, DocumentType, NotionTarget, str]:
        print("\n" + "=" * 58)
        print("  CONFIGURAZIONE PROMPT & DOCUMENTO")
        print("=" * 58)

        profiles = self.course_profile_repo.list_profiles() if self.course_profile_repo else []

        if profiles:
            print("\n  Profili memorizzati (invarianti corso salvati):")
            for i, p in enumerate(profiles, 1):
                status_str = f"{p.doc_type.value.upper()}"
                if p.folder_path.is_dir():
                    count = len(scan_documents(p.folder_path))
                    status_str += f" | {count} file"
                else:
                    status_str += " | cartella non trovata"
                print(f"    [{i:>2}] {p.subject} ({status_str})")
            print("    [ +] Nuovo corso / Inserimento manuale")

            choice = input(f"\n  Scelta [1-{len(profiles)} o +, default: 1]: ").strip()
            if not choice:
                choice = "1"

            if choice.isdigit() and 1 <= int(choice) <= len(profiles):
                chosen = profiles[int(choice) - 1]
                print(f"\n  -> Profilo selezionato: \"{chosen.subject}\"")
                print(f"     Professore  : {chosen.professor_type}")
                print(f"     Tipo Doc    : {chosen.doc_type.value.upper()}")
                print(f"     Cartella    : {chosen.folder_path}")
                print(f"     Corso Notion: {chosen.target.course_name} > {chosen.target.database_title}")

                confirm = input("\n  Usare questa configurazione? [Invio=Sì / m=Modifica / n=Nuovo]: ").strip().lower()
                if confirm == "m":
                    return self._modify_and_use_profile(chosen)
                elif confirm not in ("n", "no"):
                    folder, docs = self._validate_or_prompt_folder(chosen.folder_path)
                    prompt = get_prompt_template(chosen.doc_type.value, chosen.subject, chosen.professor_type)

                    print("\n" + "-" * 58)
                    print(f"  Materia     : {chosen.subject}")
                    print(f"  Professore  : {chosen.professor_type}")
                    print(f"  Tipo Doc    : {chosen.doc_type.value.upper()}")
                    print(f"  Cartella    : {folder}")
                    print(f"  Corso Notion: {chosen.target.course_name}")
                    print(f"  Database    : {chosen.target.database_title}")
                    print(f"  File trovati: {len(docs)} file (.pdf / .pptx)")
                    print("-" * 58)
                    return folder, chosen.doc_type, chosen.target, prompt

        # Manual / New Course setup
        return self._manual_setup()

    def run_batch(
        self,
        folder: pathlib.Path,
        doc_type: DocumentType,
        target: NotionTarget,
        prompt: str,
    ) -> Tuple[int, int]:
        doc_files = scan_documents(folder)
        total = len(doc_files)
        success = 0

        print(f"\n{'=' * 58}")
        print(f"  ELABORAZIONE: {total} file  |  {target.course_name} > {target.database_title}")
        print(f"{'=' * 58}\n")

        for index, doc_path in enumerate(doc_files, start=1):
            print(f"  [{index:>2}/{total}] {doc_path.name}")
            try:
                file_hash = compute_file_hash(doc_path)
                doc = Document(path=doc_path, file_hash=file_hash, doc_type=doc_type)

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

            doc_count = len(scan_documents(folder))
            remaining = self.llm_client.get_remaining_calls()
            if doc_count > remaining:
                print(
                    f"\n  Attenzione: {doc_count} file ma solo {remaining} chiamate "
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
