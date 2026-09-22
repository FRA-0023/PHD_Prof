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
from src.adapters.inbound.cli_adapter import CLIAdapter

def validate_env(env_vars: dict) -> None:
    missing = [k for k, v in env_vars.items() if not v]
    if missing:
        raise EnvironmentError(f"Mancanti nel .env: {', '.join(missing)}")

def main() -> None:
    print("\n" + "=" * 58)
    print("  PHD PROF: THE ANTIFRAGILE DOCUMENT ETL")
    print("  Hexagonal Architecture & Crash-Only Pipeline")
    print("=" * 58)

    load_dotenv(override=True)

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
    staging_dir = root_dir / "staging"

    # Dependency Injection: Wiring Adapters to Ports
    state_repo = JsonStateRepository(state_file=state_file, usage_file=usage_file)
    staging_storage = FileSystemStaging(staging_dir=staging_dir)
    llm_client = GeminiLlmAdapter(api_key=gemini_api_key, state_repo=state_repo)
    notion_client = NotionApiAdapter(token=notion_token)

    readers = {
        DocumentType.SLIDES: GeminiFileReader(api_key=gemini_api_key),
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
    )

    cli.start()

if __name__ == "__main__":
    main()
