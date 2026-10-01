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
from src.adapters.inbound.i18n import I18n

# Pacing delay between document processing to prevent Notion API rate limits (HTTP 429)
# and avoid tripping Gemini burst requests-per-minute (RPM) quotas.
SLEEP_BETWEEN_FILES = 5

SUPPORTED_EXTENSIONS = {".pdf", ".pptx"}

def scan_documents(folder: pathlib.Path) -> List[pathlib.Path]:
    """
    Scans for supported academic documents (.pdf, .pptx) sorted deterministically.
    Returns an empty list if directory is missing, preventing unhandled filesystem exceptions.
    """
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
    Supports bilingual presentation (IT vs EN), persistent course profiles, and multimodal slides.
    """
    def __init__(
        self,
        notion_client: INotionClient,
        llm_client: ILlmClient,
        usecase: ProcessDocumentUseCase,
        root_page_id: str,
        course_profile_repo: Optional[ICourseProfileRepository] = None,
        i18n: Optional[I18n] = None,
    ):
        self.notion_client = notion_client
        self.llm_client = llm_client
        self.usecase = usecase
        self.root_page_id = root_page_id
        self.course_profile_repo = course_profile_repo
        # Presentation layer localization: keeps UI text cleanly decoupled from core business domain
        self.i18n = i18n if i18n is not None else I18n("EN")

    def _is_yes(self, value: str, default: bool = True) -> bool:
        """
        Bilingual truth check: accepts Italian (s, si) and English (y, yes) affirmatives
        to prevent UX friction when users switch interface languages.
        """
        v = value.strip().lower()
        if not v:
            return default
        return v in ("s", "si", "y", "yes")

    def _is_no(self, value: str) -> bool:
        """Bilingual negation check (n, no)."""
        return value.strip().lower() in ("n", "no")

    def _pick(self, items: List[Dict[str, Any]], label: str) -> Dict[str, Any]:
        print(f"\n  {label} ({len(items)}):\n")
        for i, item in enumerate(items, 1):
            print(f"    [{i:>2}] {item['title']}")
        print()
        while True:
            raw = input(f"  {self.i18n.t('number_prompt', total=len(items))}").strip()
            if raw.isdigit() and 1 <= int(raw) <= len(items):
                chosen = items[int(raw) - 1]
                print(f"  -> \"{chosen['title']}\"")
                return chosen
            print(f"  [!] {self.i18n.t('invalid_choice')}")

    def navigate_to_target(self, subject: str = "") -> NotionTarget:
        print("\n" + "=" * 58)
        print(f"  {self.i18n.t('notion_nav_header')}")
        print("=" * 58)

        while True:
            print(f"\n  {self.i18n.t('fetching_courses')}")
            courses = self.notion_client.fetch_courses(self.root_page_id)
            if not courses:
                raise RuntimeError(self.i18n.t("no_courses_found"))

            # Heuristic match: skips redundant selection menu if user supplied subject partially matches
            auto_match = None
            if subject:
                subject_clean = subject.strip().lower()
                for c in courses:
                    if subject_clean in c["title"].strip().lower():
                        auto_match = c
                        break

            if auto_match:
                course = auto_match
                print(f"  {self.i18n.t('auto_matched_course', title=course['title'])}")
            else:
                course = self._pick(courses, self.i18n.t("available_courses"))

            print(f"\n  {self.i18n.t('fetching_sections', title=course['title'])}")
            targets = self.notion_client.fetch_targets_in_course(course["id"])

            if not targets:
                print(f"\n  [!] {self.i18n.t('no_sections_found', title=course['title'])}")
                if self._is_yes(input(f"  {self.i18n.t('pick_another_course')}"), default=False):
                    continue
                raise RuntimeError(self.i18n.t("op_cancelled"))

            # Auto-select standard 'Notes' database section to eliminate unnecessary CLI hops
            auto_db = next((t for t in targets if t["title"].strip().lower() == "notes"), None)
            if auto_db:
                target = auto_db
                print(f"  {self.i18n.t('auto_matched_section', title=target['title'])}")
            else:
                target = self._pick(targets, self.i18n.t("sections_in_course", course=course['title'].upper()))

            db_id = self.notion_client.resolve_database_id(target)
            return NotionTarget(
                database_id=db_id,
                course_name=course["title"],
                database_title=target["title"],
            )

    def _validate_or_prompt_folder(self, initial_folder: pathlib.Path) -> Tuple[pathlib.Path, List[pathlib.Path]]:
        """
        Validates folder existence and presence of documents (.pdf/.pptx).
        Prompts interactively until a valid folder with content is provided.
        """
        folder = initial_folder
        while True:
            if not folder.is_dir():
                print(f"  [!] {self.i18n.t('folder_not_found_err', folder=folder)}")
                raw = input(f"  {self.i18n.t('folder_reenter')}").strip()
                folder = pathlib.Path(raw).expanduser().resolve()
                continue
            docs = scan_documents(folder)
            if not docs:
                print(f"  [!] {self.i18n.t('no_supported_files', folder=folder)}")
                raw = input(f"  {self.i18n.t('folder_reenter_other')}").strip()
                folder = pathlib.Path(raw).expanduser().resolve()
                continue
            return folder, docs

    def _modify_and_use_profile(self, chosen: CourseProfile) -> Tuple[pathlib.Path, DocumentType, NotionTarget, str]:
        """
        Enables field-by-field overrides for an existing profile with bracketed defaults.
        Guarantees that a user can change a single parameter without re-typing the entire configuration.
        """
        print(f"\n  {self.i18n.t('modify_header')}")
        raw_subj = input(f"  {self.i18n.t('modify_subject', default=chosen.subject)}").strip()
        subject = raw_subj if raw_subj else chosen.subject

        raw_prof = input(f"  {self.i18n.t('modify_professor', default=chosen.professor_type)}").strip()
        professor_type = raw_prof if raw_prof else chosen.professor_type

        default_dt = "1" if chosen.doc_type == DocumentType.SLIDES else "2"
        print(f"  {self.i18n.t('doc_type_header')}")
        print(f"    [1] {self.i18n.t('doc_type_slides')}")
        print(f"    [2] {self.i18n.t('doc_type_paper')}")
        doc_type_choice = input(f"  {self.i18n.t('doc_type_choice', default=default_dt)}").strip() or default_dt
        doc_type = DocumentType.PAPER_OR_BOOK if doc_type_choice == "2" else DocumentType.SLIDES

        raw_folder = input(f"  {self.i18n.t('modify_folder', default=chosen.folder_path)}").strip()
        folder_cand = pathlib.Path(raw_folder).expanduser().resolve() if raw_folder else chosen.folder_path
        folder, docs = self._validate_or_prompt_folder(folder_cand)

        change_target = input(f"  {self.i18n.t('reconfigure_notion')}").strip()
        if self._is_yes(change_target, default=False):
            target = self.navigate_to_target(subject)
        else:
            target = chosen.target

        prompt = get_prompt_template(doc_type.value, subject, professor_type)

        if self.course_profile_repo:
            save_change = input(f"\n  {self.i18n.t('save_modifications', subject=subject)}").strip()
            if self._is_yes(save_change, default=True):
                updated = CourseProfile(
                    subject=subject,
                    professor_type=professor_type,
                    doc_type=doc_type,
                    folder_path=folder,
                    target=target,
                )
                self.course_profile_repo.save_profile(updated)
                print(f"  {self.i18n.t('profile_updated', subject=subject)}")

        self._print_recap(subject, professor_type, doc_type, folder, target, len(docs))
        return folder, doc_type, target, prompt

    def _manual_setup(self) -> Tuple[pathlib.Path, DocumentType, NotionTarget, str]:
        """Runs the standard interactive discovery setup for an unregistered course."""
        subject = input(f"  {self.i18n.t('prompt_subject')}").strip()
        while not subject:
            print(f"  [!] {self.i18n.t('required_field')}")
            subject = input(f"  {self.i18n.t('prompt_subject')}").strip()

        print()
        print(f"  {self.i18n.t('professor_desc')}")
        print(f"  {self.i18n.t('professor_default_hint', subject=subject)}")
        professor_type = input(f"  {self.i18n.t('prompt_professor')}").strip()
        if not professor_type:
            professor_type = f"PhD Professor in {subject}"

        print(f"\n  {self.i18n.t('doc_type_header')}")
        print(f"    [1] {self.i18n.t('doc_type_slides')}")
        print(f"    [2] {self.i18n.t('doc_type_paper')}")
        doc_type_choice = input(f"  {self.i18n.t('doc_type_choice', default='1')}").strip()
        if doc_type_choice == "2":
            doc_type = DocumentType.PAPER_OR_BOOK
        else:
            doc_type = DocumentType.SLIDES

        prompt = get_prompt_template(doc_type.value, subject, professor_type)

        print("\n" + "=" * 58)
        print(f"  {self.i18n.t('folder_header')}")
        print("=" * 58)
        raw_folder = input(f"  {self.i18n.t('prompt_folder')}").strip()
        folder_cand = pathlib.Path(raw_folder).expanduser().resolve()
        folder, docs = self._validate_or_prompt_folder(folder_cand)

        target = self.navigate_to_target(subject)

        if self.course_profile_repo:
            save_profile_choice = input(f"\n  {self.i18n.t('save_new_profile', subject=subject)}").strip()
            if self._is_yes(save_profile_choice, default=True):
                new_profile = CourseProfile(
                    subject=subject,
                    professor_type=professor_type,
                    doc_type=doc_type,
                    folder_path=folder,
                    target=target,
                )
                self.course_profile_repo.save_profile(new_profile)
                print(f"  {self.i18n.t('profile_saved', subject=subject)}")

        self._print_recap(subject, professor_type, doc_type, folder, target, len(docs))
        return folder, doc_type, target, prompt

    def _print_recap(
        self,
        subject: str,
        professor_type: str,
        doc_type: DocumentType,
        folder: pathlib.Path,
        target: NotionTarget,
        file_count: int,
    ) -> None:
        print("\n" + "-" * 58)
        print(f"  {self.i18n.t('label_subject'):<12}: {subject}")
        print(f"  {self.i18n.t('label_professor'):<12}: {professor_type}")
        print(f"  {self.i18n.t('label_doc_type'):<12}: {doc_type.value.upper()}")
        print(f"  {self.i18n.t('label_folder'):<12}: {folder}")
        print(f"  {self.i18n.t('label_notion_course'):<12}: {target.course_name}")
        print(f"  {self.i18n.t('label_database'):<12}: {target.database_title}")
        print(f"  {self.i18n.t('label_files_found'):<12}: {file_count} file (.pdf / .pptx)")
        print("-" * 58)

    def setup_session(self) -> Tuple[pathlib.Path, DocumentType, NotionTarget, str]:
        print("\n" + "=" * 58)
        print(f"  {self.i18n.t('config_header')}")
        print("=" * 58)

        profiles = self.course_profile_repo.list_profiles() if self.course_profile_repo else []

        if profiles:
            print(f"\n  {self.i18n.t('saved_profiles_title')}")
            for i, p in enumerate(profiles, 1):
                status_str = f"{p.doc_type.value.upper()}"
                if p.folder_path.is_dir():
                    count = len(scan_documents(p.folder_path))
                    status_str += f" | {self.i18n.t('file_count', count=count)}"
                else:
                    status_str += f" | {self.i18n.t('folder_not_found')}"
                print(f"    [{i:>2}] {p.subject} ({status_str})")
            print(f"    [ +] {self.i18n.t('new_course_option')}")

            choice = input(f"\n  {self.i18n.t('choice_prompt', total=len(profiles))}").strip()
            if not choice:
                choice = "1"

            if choice.isdigit() and 1 <= int(choice) <= len(profiles):
                chosen = profiles[int(choice) - 1]
                print(f"\n  -> {self.i18n.t('profile_selected', subject=chosen.subject)}")
                print(f"     {self.i18n.t('label_professor'):<12}: {chosen.professor_type}")
                print(f"     {self.i18n.t('label_doc_type'):<12}: {chosen.doc_type.value.upper()}")
                print(f"     {self.i18n.t('label_folder'):<12}: {chosen.folder_path}")
                print(f"     {self.i18n.t('label_notion_course'):<12}: {chosen.target.course_name} > {chosen.target.database_title}")

                confirm = input(f"\n  {self.i18n.t('confirm_profile')}").strip().lower()
                if confirm == "m":
                    return self._modify_and_use_profile(chosen)
                elif not self._is_no(confirm):
                    folder, docs = self._validate_or_prompt_folder(chosen.folder_path)
                    prompt = get_prompt_template(chosen.doc_type.value, chosen.subject, chosen.professor_type)
                    self._print_recap(chosen.subject, chosen.professor_type, chosen.doc_type, folder, chosen.target, len(docs))
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
        print(f"  {self.i18n.t('batch_header', total=total, course=target.course_name, db=target.database_title)}")
        print(f"{'=' * 58}\n")

        for index, doc_path in enumerate(doc_files, start=1):
            print(f"  [{index:>2}/{total}] {doc_path.name}")
            result = None
            try:
                file_hash = compute_file_hash(doc_path)
                doc = Document(path=doc_path, file_hash=file_hash, doc_type=doc_type)

                result = self.usecase.execute(doc, target, prompt)
                if result.success:
                    success += 1

                # Checkpoint confirmation after first item: gives the user a chance to inspect Notion before processing entire queue
                if index == 1 and total > 1 and not result.skipped:
                    print(f"\n  {self.i18n.t('first_file_done')}")
                    print(f"  {self.i18n.t('remaining_files', count=total - 1)}")
                    go = input(f"  {self.i18n.t('continue_prompt')}").strip()
                    if not self._is_yes(go, default=True):
                        print(f"  {self.i18n.t('aborted_by_user')}")
                        break

            except RuntimeError as exc:
                print(f"\n  [STOP] {exc}")
                break
            except Exception as exc:
                print(f"    [ERRORE] {exc}\n")

            if index < total and (result is not None and not result.skipped):
                print(f"    {self.i18n.t('pause_seconds', seconds=SLEEP_BETWEEN_FILES)}")
                time.sleep(SLEEP_BETWEEN_FILES)
                print()

        return success, total

    def start(self) -> None:
        remaining = self.llm_client.get_remaining_calls()
        print(f"\n  [LLM] {self.i18n.t('remaining_calls', count=remaining)}")
        if remaining <= 0:
            print(f"  [!] {self.i18n.t('quota_exceeded')}")
            sys.exit(1)

        session_success = 0
        session_total = 0

        while True:
            try:
                folder, doc_type, target, prompt = self.setup_session()
            except (RuntimeError, KeyboardInterrupt) as exc:
                print(f"\n  {self.i18n.t('setup_cancelled', err=exc)}")
                break

            doc_count = len(scan_documents(folder))
            remaining = self.llm_client.get_remaining_calls()
            if doc_count > remaining:
                print(f"\n  {self.i18n.t('quota_warning', count=doc_count, remaining=remaining)}")

            s, t = self.run_batch(folder, doc_type, target, prompt)
            session_success += s
            session_total += t

            print(f"\n  {self.i18n.t('batch_summary', success=s, total=t)}")
            print("\n" + "-" * 58)
            again = input(f"  {self.i18n.t('process_another_course')}").strip()
            if not self._is_yes(again, default=False):
                break
            print()

        print(f"\n{'=' * 58}")
        print(f"  {self.i18n.t('session_terminated')}")
        print(f"  {self.i18n.t('session_archived', success=session_success, total=session_total)}")
        print(f"  {self.i18n.t('session_remaining_calls', remaining=self.llm_client.get_remaining_calls())}")
        print(f"{'=' * 58}\n")
