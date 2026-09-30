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

def validate_env(env_vars: dict) -> None:
    missing = [k for k, v in env_vars.items() if not v]
    if missing:
        raise EnvironmentError(f"Mancanti nel .env: {', '.join(missing)}")

def main() -> None:
    load_dotenv(override=True)

    # CLI Language flag resolution: command line arg takes precedence over .env setting
    parser = argparse.ArgumentParser(description="PHD Prof: Academic Document ETL Pipeline")
    parser.add_argument("--lang", choices=["IT", "EN", "it", "en"], help="Interaction language (IT vs EN)")
    args, _ = parser.parse_known_args()

    cli_lang = args.lang.upper() if args.lang else os.getenv("CLI_LANGUAGE", "IT").upper()
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
