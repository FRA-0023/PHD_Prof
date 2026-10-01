"""
pdf_to_notion.py
----------------
Composition Root / Dependency Injection bootstrapping for PHD_Prof.
Loads environment configuration, instantiates ports and adapters, and starts the CLI adapter.
"""
import os
import sys
import pathlib
from dotenv import load_dotenv

from src.core.domain.models import DocumentType
from src.core.usecases.process_document import ProcessDocumentUseCase
from src.adapters.outbound.json_state_repository import JsonStateRepository
from src.adapters.outbound.filesystem_staging import FileSystemStaging
from src.adapters.outbound.gemini_llm_adapter import GeminiLlmAdapter
from src.adapters.outbound.notion_api_adapter import NotionApiAdapter
from src.adapters.outbound.document_readers.gemini_file_reader import GeminiFileReader
from src.adapters.outbound.document_readers.text_pdf_reader import TextPdfReader
import argparse
from src.adapters.outbound.json_course_profile_repository import JsonCourseProfileRepository
from src.adapters.inbound.i18n import I18n
from src.adapters.inbound.cli_adapter import CLIAdapter
from src.adapters.inbound.web.web_adapter import WebAdapter

def validate_env(env_vars: dict) -> None:
    missing = [k for k, v in env_vars.items() if not v]
    if missing:
        raise EnvironmentError(f"Mancanti nel .env: {', '.join(missing)}")

def main() -> None:
    if sys.platform == "win32":
        # RATIONALE (Console Encoding Resilience): Windows command prompts default to OEM codepages
        # (CP850/CP437) which corrupt Unicode accents. Forcing UTF-8 on standard streams guarantees clean rendering.
        try:
            sys.stdout.reconfigure(encoding="utf-8")
            sys.stderr.reconfigure(encoding="utf-8")
        except Exception:
            pass

    load_dotenv(override=True)

    # Interaction mode & language resolution: CLI args take precedence over defaults
    parser = argparse.ArgumentParser(description="PHD Prof: Academic Document ETL Pipeline")
    parser.add_argument("--mode", choices=["web", "cli"], default="web", help="Interface mode (web vs cli)")
    parser.add_argument("--port", type=int, default=8000, help="Web server port (default: 8000)")
    parser.add_argument("--no-browser", action="store_true", help="Do not open browser automatically")
    parser.add_argument("--lang", choices=["IT", "EN", "it", "en"], help="Interaction language (IT vs EN)")
    args, _ = parser.parse_known_args()

    cli_lang = args.lang.upper() if args.lang else os.getenv("CLI_LANGUAGE", "EN").upper()
    i18n = I18n(lang=cli_lang)

    print("\n" + "=" * 58)
    print(f"  {i18n.t('banner_title')}")
    print(f"  {i18n.t('banner_subtitle')} [{i18n.lang}]")
    print("=" * 58)

    gemini_api_key = os.getenv("GEMINI_API_KEY")
    notion_token = os.getenv("NOTION_TOKEN")
    notion_root_page_id = os.getenv("NOTION_ROOT_PAGE_ID")

    validate_env({
        "GEMINI_API_KEY": gemini_api_key,
        "NOTION_TOKEN": notion_token,
        "NOTION_ROOT_PAGE_ID": notion_root_page_id,
    })

    root_dir = pathlib.Path(__file__).parent
    state_file = root_dir / "sync_state.json"
    usage_file = root_dir / "gemini_usage.json"
    profiles_file = root_dir / "course_profiles.json"
    staging_dir = root_dir / "staging"

    # RATIONALE (Zero-setup onboarding): If the local profiles file is absent, seeding it
    # from the tracked example template guarantees the CLI immediately renders the fast-path
    # profile selection menu rather than silently falling back to raw discovery questions.
    example_profiles_file = root_dir / "course_profiles.example.json"
    if not profiles_file.exists() and example_profiles_file.exists():
        import shutil
        try:
            shutil.copyfile(example_profiles_file, profiles_file)
        except OSError:
            pass

    # Timeout configuration (default: 300s to avoid socket read timeouts on large uploads)
    raw_timeout = os.getenv("GEMINI_TIMEOUT_SECONDS")
    try:
        gemini_timeout = float(raw_timeout) if raw_timeout else 300.0
    except ValueError:
        gemini_timeout = 300.0

    # Gemini model configuration (default: gemini-2.5-flash with auto-fallback to gemini-2.0-flash)
    gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    # Dependency Injection: Wiring Adapters to Ports
    state_repo = JsonStateRepository(state_file=state_file, usage_file=usage_file)
    course_profile_repo = JsonCourseProfileRepository(file_path=profiles_file)
    staging_storage = FileSystemStaging(staging_dir=staging_dir)
    llm_client = GeminiLlmAdapter(
        api_key=gemini_api_key,
        state_repo=state_repo,
        model=gemini_model,
        timeout=gemini_timeout,
    )
    notion_client = NotionApiAdapter(token=notion_token)

    readers = {
        DocumentType.SLIDES: GeminiFileReader(
            api_key=gemini_api_key,
            timeout=gemini_timeout,
            staging_dir=staging_dir,
        ),
        DocumentType.PAPER_OR_BOOK: TextPdfReader(),
    }

    usecase = ProcessDocumentUseCase(
        readers=readers,
        llm_client=llm_client,
        notion_client=notion_client,
        state_repo=state_repo,
        staging_storage=staging_storage,
    )

    if args.mode == "web":
        web = WebAdapter(
            notion_client=notion_client,
            llm_client=llm_client,
            usecase=usecase,
            root_page_id=notion_root_page_id,
            course_profile_repo=course_profile_repo,
            state_repo=state_repo,
            host="127.0.0.1",
            port=args.port,
        )
        if not args.no_browser:
            import webbrowser
            import threading
            threading.Timer(0.8, lambda: webbrowser.open(f"http://127.0.0.1:{args.port}")).start()
        print(f"\n  [Web] Cockpit avviato su http://127.0.0.1:{args.port}\n")
        web.start()
    else:
        cli = CLIAdapter(
            notion_client=notion_client,
            llm_client=llm_client,
            usecase=usecase,
            root_page_id=notion_root_page_id,
            course_profile_repo=course_profile_repo,
            i18n=i18n,
        )
        cli.start()

if __name__ == "__main__":
    main()
