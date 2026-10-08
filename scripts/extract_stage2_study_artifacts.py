"""
scripts/extract_stage2_study_artifacts.py
-----------------------------------------
Utility script to run Stage 2 (Study Artifact Extraction) on an existing staging markdown file.
Invokes Gemini 2.5 Flash on the compressed markdown notes, extracts Mermaid mindmaps,
flowcharts, active recall drills, and boundary conditions, saves the OPML for EdrawMind,
updates the staging file, and optionally appends the new blocks to Notion.
"""
import os
import sys
import argparse
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
load_dotenv(PROJECT_ROOT / ".env")

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from src.adapters.outbound.json_state_repository import JsonStateRepository
from src.adapters.outbound.gemini_llm_adapter import GeminiLlmAdapter
from src.adapters.outbound.study_schema_exporter_adapter import StudySchemaExporterAdapter
from src.adapters.outbound.notion_api_adapter import NotionApiAdapter
from src.adapters.outbound.notion_block_builder import build_notion_blocks
from src.core.domain.prompt_templates import get_artifacts_extraction_prompt

def main():
    parser = argparse.ArgumentParser(description="Run Stage 2 Study Artifact Extraction on staging markdown.")
    parser.add_argument(
        "--hash",
        default="b309101b9afaad45228dce54fee9dccb5cd4c0baa1225b16bcf2f2064b374c2f",
        help="SHA-256 hash of the target staging markdown file (default: Big Data Session 1)"
    )
    parser.add_argument(
        "--subject",
        default="Big Data Engineering & Distributed Systems",
        help="Subject name for prompt specialization (default: Big Data)"
    )
    parser.add_argument(
        "--title",
        default="Big Data Engineering - Session 1",
        help="Document title for OPML metadata"
    )
    parser.add_argument(
        "--notion",
        action="store_true",
        help="Append the extracted study artifacts directly to the existing Notion page"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-generation with Gemini even if artifacts already exist in staging"
    )
    args = parser.parse_args()

    file_hash = args.hash
    staging_file = PROJECT_ROOT / "staging" / f"{file_hash}.md"
    if not staging_file.exists():
        print(f"ERROR: File staging '{staging_file}' non trovato.")
        sys.exit(1)

    print(f"\n{'=' * 60}")
    print(f"  Stage 2 Study Artifacts Extractor: {args.title}")
    print(f"  Target File: staging/{file_hash}.md ({staging_file.stat().st_size:,} bytes)")
    print(f"{'=' * 60}\n")

    notes_markdown = staging_file.read_text(encoding="utf-8")
    print(f"  [1/4] Letto markdown di staging: {len(notes_markdown):,} caratteri, {len(notes_markdown.split()):,} parole.")

    state_repo = JsonStateRepository(
        state_file=PROJECT_ROOT / "sync_state.json",
        usage_file=PROJECT_ROOT / "gemini_usage.json"
    )

    # 2. Invocazione Stage 2 su Staging Markdown o riuso cache locale
    if "## 🧠 Conceptual Architecture" in notes_markdown and not args.force:
        print("  [2/4] [Local Cache] Sezione schemi già presente in staging. Riuso artefatti estratti (0 token sprecati).")
        artifacts_section = notes_markdown.split("## 🧠 Conceptual Architecture", 1)[1]
        artifacts_text = f"## 🧠 Conceptual Architecture{artifacts_section}"
    else:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("ERROR: GEMINI_API_KEY non trovata nell'ambiente.")
            sys.exit(1)

        gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        raw_timeout = os.getenv("GEMINI_TIMEOUT_SECONDS", "300")
        try:
            timeout = float(raw_timeout)
        except ValueError:
            timeout = 300.0

        llm_client = GeminiLlmAdapter(
            api_key=api_key,
            state_repo=state_repo,
            model=gemini_model,
            timeout=timeout
        )

        print(f"  [2/4] Invocazione Gemini ({gemini_model}) per estrazione artefatti di studio...")
        prompt = get_artifacts_extraction_prompt(subject=args.subject, notes_markdown=notes_markdown)
        artifacts_text = llm_client.generate_notes(prompt=prompt, content_payload=notes_markdown)
        print(f"  [OK] Ricevuti {len(artifacts_text):,} caratteri di artefatti concettuali.")

        updated_notes = f"{notes_markdown.rstrip()}\n\n{artifacts_text.lstrip()}"
        staging_file.write_text(updated_notes, encoding="utf-8")
        print(f"  [OK] File staging aggiornato con gli artefatti in append.")

    # 3. Parsing ed esportazione OPML (EdrawMind)
    print(f"  [3/4] Parsing artefatti ed esportazione OPML (EdrawMind)...")
    exporter = StudySchemaExporterAdapter()
    artifact = exporter.extract_artifacts(artifacts_text, file_hash, args.title)

    schemas_dir = PROJECT_ROOT / "staging" / "schemas"
    schemas_dir.mkdir(parents=True, exist_ok=True)
    opml_file = schemas_dir / f"{file_hash}.opml"
    opml_file.write_text(artifact.opml_content or "", encoding="utf-8")
    print(f"  [OK] File OPML salvato in: {opml_file.relative_to(PROJECT_ROOT)} ({len(artifact.opml_content or ''):,} caratteri).")


    # 4. Opzionale: Caricamento su Notion
    if args.notion:
        print(f"  [4/4] Caricamento blocchi su Notion...")
        entry = state_repo.get_entry(file_hash)
        if not entry or not entry.page_id:
            print(f"  [Warning] Page ID non trovato in sync_state.json per hash {file_hash}.")
        else:
            notion_token = os.getenv("NOTION_TOKEN")
            if not notion_token:
                print("  [Warning] NOTION_TOKEN non presente. Salto caricamento Notion.")
            else:
                notion_client = NotionApiAdapter(token=notion_token)
                blocks = build_notion_blocks(f"\n---\n{artifacts_text}")
                print(f"  [Notion] Generati {len(blocks)} blocchi Notion (inclusi grafi Mermaid). Appendo alla pagina {entry.page_id}...")
                notion_client.append_blocks(entry.page_id, blocks)
                print(f"  [OK] Blocchi aggiunti alla pagina Notion con successo.")
    else:
        print(f"  [4/4] Caricamento Notion non richiesto (usa --notion per aggiungere alla pagina).")

    print(f"\n{'=' * 60}")
    print("  ESTRAZIONE STAGE 2 COMPLETATA CON SUCCESSO!")
    print(f"{'=' * 60}\n")
    print("--- ANTEPRIMA ARTEFATTI ESTRATTI ---")
    if artifact.mindmap_mermaid:
        print("\n[Mermaid Mindmap]:")
        for line in artifact.mindmap_mermaid.splitlines()[:15]:
            print(" ", line)
        if len(artifact.mindmap_mermaid.splitlines()) > 15:
            print("  ...")
    if artifact.flowchart_mermaid:
        print("\n[Mermaid Flowchart]:")
        for line in artifact.flowchart_mermaid.splitlines()[:15]:
            print(" ", line)
        if len(artifact.flowchart_mermaid.splitlines()) > 15:
            print("  ...")
    if artifact.boundary_matrix_markdown:
        print("\n[Boundary Conditions Matrix]:")
        print(artifact.boundary_matrix_markdown[:300] + "...")

if __name__ == "__main__":
    main()
