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

from src.core.domain.models import DocumentType, GenerationMode
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
    parser.add_argument(
        "--generation-mode", "--gen-mode",
        choices=["both", "notes_only", "graphs_only"],
        default="both",
        help="Artifact generation mode: both (notes + graphs), notes_only, or graphs_only",
    )
    parser.add_argument("--port", type=int, default=None, help="Web server port (default: 80, or from WEB_PORT)")
    parser.add_argument("--host", type=str, default=None, help="Web server host (default: 127.0.0.1, or from WEB_HOST)")
    parser.add_argument("--domain", type=str, default=None, help="Local domain name (default: phdprof.test, or from WEB_DOMAIN)")
    parser.add_argument("--ssl", action="store_true", default=None, help="Enable HTTPS mode (auto-detected if certs exist)")
    parser.add_argument("--no-ssl", dest="ssl", action="store_false", help="Disable HTTPS mode")
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

    # Optional Configuration: Cloudflare R2 / S3 Image Hosting
    r2_endpoint = os.getenv("R2_ENDPOINT_URL")
    r2_access = os.getenv("R2_ACCESS_KEY")
    r2_secret = os.getenv("R2_SECRET_KEY")
    r2_bucket = os.getenv("R2_BUCKET_NAME")
    r2_domain = os.getenv("R2_PUBLIC_DOMAIN")
    
    image_host_client = None
    if all([r2_endpoint, r2_access, r2_secret, r2_bucket, r2_domain]):
        from src.adapters.outbound.s3_image_adapter import S3ImageAdapter
        image_host_client = S3ImageAdapter(r2_endpoint, r2_access, r2_secret, r2_bucket, r2_domain)

    # High-DPI Visual Diagram Extractor Configuration
    from src.adapters.outbound.pymupdf_visual_extractor import PyMuPdfVisualExtractor
    visual_extractor = PyMuPdfVisualExtractor()

    # Study Schema Exporter (EdrawMind OPML, Mermaid, Active Recall)
    from src.adapters.outbound.study_schema_exporter_adapter import StudySchemaExporterAdapter
    schema_exporter = StudySchemaExporterAdapter()

    # Adaptive Dispatcher threshold (default: 30.000 chars, calibrated to prevent 8k output token saturation)
    raw_split_threshold = os.getenv("SPLIT_THRESHOLD_CHARS")
    try:
        split_threshold = int(raw_split_threshold) if raw_split_threshold else 30000
    except ValueError:
        split_threshold = 30000

    usecase = ProcessDocumentUseCase(
        readers=readers,
        llm_client=llm_client,
        notion_client=notion_client,
        state_repo=state_repo,
        staging_storage=staging_storage,
        visual_extractor=visual_extractor,
        image_host_client=image_host_client,
        schema_exporter=schema_exporter,
        split_threshold_chars=split_threshold,
    )

    if args.mode == "web":
        import socket
        import webbrowser
        import threading

        # Certificate detection & HTTPS mode resolution
        certs_dir = root_dir / "certs"
        server_crt = certs_dir / "server.crt"
        server_key = certs_dir / "server.key"
        certs_available = server_crt.exists() and server_key.exists()
        use_ssl = args.ssl if args.ssl is not None else certs_available

        # Resolve networking parameters (CLI takes precedence over .env)
        raw_env_port = os.getenv("WEB_PORT")
        default_port = int(raw_env_port) if raw_env_port and raw_env_port.isdigit() else (443 if use_ssl else 80)
        web_port = args.port if args.port is not None else default_port
        web_host = args.host if args.host is not None else os.getenv("WEB_HOST", "127.0.0.1")
        web_domain = args.domain if args.domain is not None else os.getenv("WEB_DOMAIN", "phdprof.test")

        # Port binding resilience: check if privileged/standard ports are available
        def _check_port(h: str, p: int) -> bool:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    s.bind((h, p))
                    return True
            except OSError:
                return False

        if use_ssl and web_port == 443 and not _check_port(web_host, web_port):
            print("\n  [Web] Notice: Port 443 unavailable or in use. Falling back to port 8443...")
            web_port = 8443
        elif not use_ssl and web_port == 80 and not _check_port(web_host, web_port):
            print("\n  [Web] Notice: Port 80 unavailable or in use. Falling back to port 8000...")
            web_port = 8000

        # Check local domain resolution
        resolves_domain = False
        try:
            socket.gethostbyname(web_domain)
            resolves_domain = True
        except socket.error:
            resolves_domain = False

        protocol = "https" if use_ssl else "http"
        is_standard_port = (use_ssl and web_port == 443) or (not use_ssl and web_port == 80)
        port_suffix = "" if is_standard_port else f":{web_port}"

        if resolves_domain:
            target_url = f"{protocol}://{web_domain}{port_suffix}"
        else:
            target_url = f"{protocol}://127.0.0.1{port_suffix}"
            if web_domain not in ("127.0.0.1", "localhost"):
                print(f"\n  [!] Notice: '{web_domain}' is not yet configured in your hosts file.")
                print(f"      Run 'Configure_Local_Domain.bat' as Administrator to enable it.")
                print(f"      Temporary fallback access: {target_url}\n")

        web = WebAdapter(
            notion_client=notion_client,
            llm_client=llm_client,
            usecase=usecase,
            root_page_id=notion_root_page_id,
            course_profile_repo=course_profile_repo,
            state_repo=state_repo,
            host=web_host,
            port=web_port,
            ssl_keyfile=str(server_key) if use_ssl else None,
            ssl_certfile=str(server_crt) if use_ssl else None,
        )
        if not args.no_browser:
            threading.Timer(0.8, lambda: webbrowser.open(target_url)).start()
        print(f"\n  [Web] Cockpit started at {target_url} (listening on {web_host}:{web_port}, SSL={use_ssl})\n")
        web.start()
    else:
        try:
            gen_mode = GenerationMode(args.generation_mode.lower())
        except ValueError:
            gen_mode = GenerationMode.BOTH

        cli = CLIAdapter(
            notion_client=notion_client,
            llm_client=llm_client,
            usecase=usecase,
            root_page_id=notion_root_page_id,
            course_profile_repo=course_profile_repo,
            i18n=i18n,
            default_generation_mode=gen_mode,
        )
        cli.start()

if __name__ == "__main__":
    main()
