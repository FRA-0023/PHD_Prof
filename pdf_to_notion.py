"""
pdf_to_notion.py
----------------
Flusso:
  1. Chiede materia e tipo di professore (una volta sola per sessione).
  2. Inietta i valori nel prompt dinamico.
  3. Naviga Notion (Courses > Corso > Database) e seleziona la destinazione.
  4. Elabora tutti i PDF in automatico, senza interruzioni.
  5. Al termine chiede se processare un altro corso.

Requisiti:
    pip install google-generativeai python-dotenv requests

File .env (stessa cartella dello script):
    GEMINI_API_KEY=...
    NOTION_TOKEN=...
    NOTION_ROOT_PAGE_ID=...   # ID della pagina "Courses" su Notion
"""

import os
import sys
import json
import time
import pathlib
import textwrap
import datetime
import requests
import google.generativeai as genai
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# CONFIGURAZIONE FISSA
# ---------------------------------------------------------------------------

load_dotenv()

GEMINI_API_KEY      = os.getenv("GEMINI_API_KEY")
NOTION_TOKEN        = os.getenv("NOTION_TOKEN")
NOTION_ROOT_PAGE_ID = os.getenv("NOTION_ROOT_PAGE_ID")

GEMINI_MODEL       = "gemini-2.5-pro-preview-05-06"
GEMINI_DAILY_LIMIT = 50
USAGE_FILE         = pathlib.Path(__file__).parent / "gemini_usage.json"

NOTION_API_BASE        = "https://api.notion.com/v1"
NOTION_VERSION         = "2022-06-28"
NOTION_MAX_BLOCK_CHARS = 1900
SLEEP_NOTION_BATCH     = 0.4   # secondi tra batch di blocchi Notion
SLEEP_BETWEEN_FILES    = 5     # secondi di pausa tra un PDF e il successivo

# ---------------------------------------------------------------------------
# PROMPT DINAMICO
#
# I placeholder {subject} e {professor_type} vengono sostituiti a runtime
# con i valori inseriti dall'utente all'inizio di ogni sessione.
# ---------------------------------------------------------------------------

PROMPT_TEMPLATE = """
# ROLE
Act as a professional {professor_type} with a Master's degree in Science Communication.
Your goal is to explain the provided lecture slides on **{subject}** so clearly, comprehensively, and pedagogically that a student with absolute zero prior context can perfectly understand the topic without needing further clarification.

# CONTEXT & INPUT
You are analyzing a single PDF file containing the slides for a **{subject}** lecture.
Your output must match the high-quality baseline structure established in our previous ideal notes.

# TASK
Extract the core concepts from the slides and transform them into exceptional, highly readable study notes.
Do not merely summarize; expand the original text by adding necessary background information, deep-dive explanations, and practical examples to maximize understanding (aim to expand the content to roughly 1.3x its original length where useful).
Organize the topics logically, separating distinct semantic groups.

# FORMATTING & EXPORT RULES (OPTIMIZED FOR NOTION)
- Markdown Hierarchy: Organize the notes using strict Markdown headings:
  # Main title for the section
  [Body text]
  ## Subsection title
  [Body text]
  ### Sub-subsection title
  [Body text]
- Readability (No Walls of Text): Go to the next line immediately each time a sentence finishes.
- Lists: Use standard Markdown bullet points (`*` or `-`) and numbered lists (`1.`). Keep all text for a single list item on the exact same line as its bullet or number marker. Do not add hard line breaks within a list item.
- Emphasis: Use **bold** text strategically to highlight important notations, keywords, and core concepts.
- Formulas and Math: You must explain and extract EVERY formula present in the slides. Format them explicitly for Notion using standard LaTeX: enclose inline math within `$` (e.g., $E=mc^2$) and display math within `$$` on a separate line.
- Strict Citation Rule: Place ALL citations exclusively at the very end of the final document in a dedicated "References" section. Do NOT insert any citation numbers, names, or references in the middle of the notes.
- Output Constraints: Output ONLY the requested study notes. Do not print tags like "[inference]", "[unverified]", or provide any conversational filler or meta-commentary about the prompt instructions.

# DATA INPUT
Please process the following {subject} lecture content:
"""


def build_prompt(subject: str, professor_type: str) -> str:
    """
    Sostituisce i placeholder nel template con i valori della sessione.

    Args:
        subject:        Materia del corso (es. "Statistical Modelling").
        professor_type: Tipo/titolo del professore (es. "Statistical Modelling PhD Professor").

    Returns:
        Prompt pronto da inviare a Gemini.
    """
    return PROMPT_TEMPLATE.format(
        subject=subject,
        professor_type=professor_type,
    ).strip()

# ---------------------------------------------------------------------------
# VALIDAZIONE .ENV
# ---------------------------------------------------------------------------

def validate_env() -> None:
    missing = [k for k, v in {
        "GEMINI_API_KEY":      GEMINI_API_KEY,
        "NOTION_TOKEN":        NOTION_TOKEN,
        "NOTION_ROOT_PAGE_ID": NOTION_ROOT_PAGE_ID,
    }.items() if not v]
    if missing:
        raise EnvironmentError(f"Mancanti nel .env: {', '.join(missing)}")

# ---------------------------------------------------------------------------
# TRACCIAMENTO UTILIZZO GEMINI
# ---------------------------------------------------------------------------

def _load_usage() -> dict:
    if USAGE_FILE.exists():
        try:
            with open(USAGE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"date": "", "count": 0}


def _save_usage(data: dict) -> None:
    with open(USAGE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def get_remaining_calls() -> int:
    usage = _load_usage()
    today = datetime.date.today().isoformat()
    used  = usage.get("count", 0) if usage.get("date") == today else 0
    return GEMINI_DAILY_LIMIT - used


def check_and_increment_usage() -> None:
    today = datetime.date.today().isoformat()
    usage = _load_usage()
    if usage.get("date") != today:
        usage = {"date": today, "count": 0}
    if usage["count"] >= GEMINI_DAILY_LIMIT:
        raise RuntimeError(
            f"Limite giornaliero Gemini raggiunto ({GEMINI_DAILY_LIMIT} RPD). "
            "Riprova domani."
        )
    usage["count"] += 1
    _save_usage(usage)
    remaining = GEMINI_DAILY_LIMIT - usage["count"]
    print(f"    [Gemini] Chiamata {usage['count']}/{GEMINI_DAILY_LIMIT} "
          f"— rimaste oggi: {remaining}")

# ---------------------------------------------------------------------------
# SETUP SESSIONE
# ---------------------------------------------------------------------------

def setup_session() -> tuple[pathlib.Path, str, str, str, str]:
    """
    Raccoglie tutti i parametri necessari per la sessione:
      - Materia e tipo di professore  → costruisce il prompt.
      - Cartella PDF locale.
      - Corso e database Notion.

    Returns:
        (pdf_folder, database_id, course_name, db_title, prompt)
    """

    # 1. Parametri del prompt
    print("\n" + "="*58)
    print("  CONFIGURAZIONE PROMPT")
    print("="*58)
    print("  Questi valori vengono iniettati nel prompt inviato a Gemini.")
    print()

    subject = input("  Materia del corso (es. Statistical Modelling): ").strip()
    while not subject:
        print("  [!] Campo obbligatorio.")
        subject = input("  Materia del corso: ").strip()

    print()
    print(f"  Tipo di professore — descrive il ruolo accademico del modello.")
    print(f"  Lascia vuoto per usare il default: 'PhD Professor in {subject}'")
    professor_type = input("  Tipo professore: ").strip()
    if not professor_type:
        professor_type = f"PhD Professor in {subject}"

    prompt = build_prompt(subject, professor_type)

    # 2. Cartella PDF
    print("\n" + "="*58)
    print("  CARTELLA PDF")
    print("="*58)
    print("  Percorso assoluto (supporta ~).")
    print()
    while True:
        raw    = input("  Percorso: ").strip()
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

    # 3. Navigazione Notion
    database_id, course_name, db_title = navigate_to_database()

    # 4. Riepilogo
    print("\n" + "-"*58)
    print(f"  Materia     : {subject}")
    print(f"  Professore  : {professor_type}")
    print(f"  Cartella    : {folder}")
    print(f"  Corso Notion: {course_name}")
    print(f"  Database    : {db_title}")
    print(f"  PDF         : {len(pdfs)} file")
    print("-"*58)

    return folder, database_id, course_name, db_title, prompt

# ---------------------------------------------------------------------------
# NAVIGAZIONE NOTION
# ---------------------------------------------------------------------------

def _notion_headers() -> dict:
    return {
        "Authorization":  f"Bearer {NOTION_TOKEN}",
        "Content-Type":   "application/json",
        "Notion-Version": NOTION_VERSION,
    }


def _fetch_children(parent_id: str) -> list[dict]:
    results, params = [], {"page_size": 100}
    url = f"{NOTION_API_BASE}/blocks/{parent_id}/children"
    while url:
        r = requests.get(url, headers=_notion_headers(), params=params, timeout=30)
        r.raise_for_status()
        data = r.json()
        results.extend(data.get("results", []))
        if data.get("has_more"):
            params = {"page_size": 100, "start_cursor": data["next_cursor"]}
        else:
            url = None
    return results


def fetch_child_pages(parent_id: str) -> list[dict]:
    return [
        {"id": b["id"], "title": b.get("child_page", {}).get("title", "Senza titolo")}
        for b in _fetch_children(parent_id) if b.get("type") == "child_page"
    ]


def fetch_child_databases(parent_id: str) -> list[dict]:
    return [
        {"id": b["id"], "title": b.get("child_database", {}).get("title", "Senza titolo")}
        for b in _fetch_children(parent_id) if b.get("type") == "child_database"
    ]


def _pick(items: list[dict], label: str) -> dict:
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


def navigate_to_database() -> tuple[str, str, str]:
    """
    Navigazione interattiva: Courses > Corso > Database.

    Returns:
        (database_id, course_name, database_title)
    """
    print("\n" + "="*58)
    print("  SELEZIONE CORSO E DATABASE NOTION")
    print("="*58)

    while True:
        print("\n  Recupero corsi...")
        courses = fetch_child_pages(NOTION_ROOT_PAGE_ID)
        if not courses:
            raise RuntimeError(
                "Nessuna pagina-corso trovata nella root Notion. "
                "Controlla i permessi dell'integrazione."
            )

        course = _pick(courses, "CORSI DISPONIBILI")

        print(f"\n  Recupero database in '{course['title']}'...")
        dbs = fetch_child_databases(course["id"])

        if not dbs:
            print(f"\n  [!] Nessun database in '{course['title']}'.")
            if input("  Scegli un altro corso? [s/n]: ").strip().lower() == "s":
                continue
            raise RuntimeError("Nessun database trovato. Operazione annullata.")

        db = _pick(dbs, f"DATABASE IN '{course['title'].upper()}'")
        return db["id"], course["title"], db["title"]

# ---------------------------------------------------------------------------
# GEMINI
# ---------------------------------------------------------------------------

def upload_pdf_to_gemini(pdf_path: str) -> genai.types.File:
    uploaded = genai.upload_file(path=pdf_path, mime_type="application/pdf")
    while uploaded.state.name == "PROCESSING":
        time.sleep(3)
        uploaded = genai.get_file(uploaded.name)
    if uploaded.state.name == "FAILED":
        raise RuntimeError(f"Gemini: elaborazione fallita per '{pdf_path}'.")
    return uploaded


def generate_notes(uploaded: genai.types.File, prompt: str) -> str:
    check_and_increment_usage()
    model    = genai.GenerativeModel(model_name=GEMINI_MODEL)
    response = model.generate_content([prompt, uploaded])
    return response.text


def delete_gemini_file(uploaded: genai.types.File) -> None:
    try:
        genai.delete_file(uploaded.name)
    except Exception:
        pass  # I file Gemini scadono automaticamente dopo 48h.

# ---------------------------------------------------------------------------
# NOTION — CREAZIONE PAGINA E BLOCCHI
# ---------------------------------------------------------------------------

def create_notion_page(database_id: str, title: str) -> str:
    r = requests.post(
        f"{NOTION_API_BASE}/pages",
        headers=_notion_headers(),
        json={
            "parent": {"database_id": database_id},
            "properties": {
                "Name": {"title": [{"type": "text", "text": {"content": title}}]}
            },
        },
        timeout=30,
    )
    r.raise_for_status()
    return r.json()["id"]


def _build_blocks(text: str) -> list[dict]:
    """
    Converte il testo Markdown di Gemini in blocchi Notion.
    Gestisce: # h1, ## h2, ### h3, - /* bullet, testo normale.
    I blocchi LaTeX ($$...$$) vengono passati come codice inline
    in attesa del supporto nativo equazioni su Notion.
    """
    blocks = []

    for line in text.splitlines():
        s = line.strip()

        if not s:
            blocks.append({
                "object": "block", "type": "paragraph",
                "paragraph": {"rich_text": []},
            })
            continue

        # Heading 1
        if s.startswith("# ") and not s.startswith("## "):
            content = s[2:].strip()
            blocks.append({
                "object": "block", "type": "heading_1",
                "heading_1": {"rich_text": [
                    {"type": "text", "text": {"content": content[:NOTION_MAX_BLOCK_CHARS]}}
                ]},
            })
            continue

        # Heading 2
        if s.startswith("## ") and not s.startswith("### "):
            content = s[3:].strip()
            blocks.append({
                "object": "block", "type": "heading_2",
                "heading_2": {"rich_text": [
                    {"type": "text", "text": {"content": content[:NOTION_MAX_BLOCK_CHARS]}}
                ]},
            })
            continue

        # Heading 3
        if s.startswith("### "):
            content = s[4:].strip()
            blocks.append({
                "object": "block", "type": "heading_3",
                "heading_3": {"rich_text": [
                    {"type": "text", "text": {"content": content[:NOTION_MAX_BLOCK_CHARS]}}
                ]},
            })
            continue

        # Bullet point
        if s.startswith(("- ", "* ")):
            content = s[2:].strip()
            for chunk in textwrap.wrap(content, NOTION_MAX_BLOCK_CHARS, break_long_words=True):
                blocks.append({
                    "object": "block", "type": "bulleted_list_item",
                    "bulleted_list_item": {"rich_text": [
                        {"type": "text", "text": {"content": chunk}}
                    ]},
                })
            continue

        # Numbered list (1. 2. ecc.)
        if len(s) > 2 and s[0].isdigit() and s[1] in ".)" and s[2] == " ":
            content = s[3:].strip()
            for chunk in textwrap.wrap(content, NOTION_MAX_BLOCK_CHARS, break_long_words=True):
                blocks.append({
                    "object": "block", "type": "numbered_list_item",
                    "numbered_list_item": {"rich_text": [
                        {"type": "text", "text": {"content": chunk}}
                    ]},
                })
            continue

        # Blocco formula display ($$...$$) → blocco codice
        if s.startswith("$$") and s.endswith("$$") and len(s) > 4:
            formula = s[2:-2].strip()
            blocks.append({
                "object": "block", "type": "code",
                "code": {
                    "language": "plain text",
                    "rich_text": [{"type": "text", "text": {"content": formula}}],
                },
            })
            continue

        # Paragrafo normale (con chunking se troppo lungo)
        for chunk in textwrap.wrap(s, NOTION_MAX_BLOCK_CHARS, break_long_words=True):
            blocks.append({
                "object": "block", "type": "paragraph",
                "paragraph": {"rich_text": [
                    {"type": "text", "text": {"content": chunk}}
                ]},
            })

    return blocks


def append_blocks(page_id: str, blocks: list[dict]) -> None:
    for i in range(0, len(blocks), 100):
        batch = blocks[i:i+100]
        r = requests.patch(
            f"{NOTION_API_BASE}/blocks/{page_id}/children",
            headers=_notion_headers(),
            json={"children": batch},
            timeout=30,
        )
        r.raise_for_status()
        time.sleep(SLEEP_NOTION_BATCH)

# ---------------------------------------------------------------------------
# ELABORAZIONE BATCH (completamente automatica)
# ---------------------------------------------------------------------------

def run_batch(
    pdf_folder:  pathlib.Path,
    database_id: str,
    prompt:      str,
    course_name: str,
    db_title:    str,
) -> tuple[int, int]:
    """
    Processa tutti i PDF nella cartella in modo completamente automatico.

    Returns:
        (n_success, n_total)
    """
    pdf_files = sorted(pdf_folder.glob("*.pdf"))
    total     = len(pdf_files)
    success   = 0

    print(f"\n{'='*58}")
    print(f"  ELABORAZIONE: {total} file  |  {course_name} > {db_title}")
    print(f"{'='*58}\n")

    for index, pdf_path in enumerate(pdf_files, start=1):
        file_name = pdf_path.stem
        print(f"  [{index:>2}/{total}] {file_name}.pdf")

        try:
            print("    [Gemini] Upload PDF...")
            uploaded = upload_pdf_to_gemini(str(pdf_path))

            print("    [Gemini] Generazione note...")
            text = generate_notes(uploaded, prompt)
            print(f"    [Gemini] Ricevuti {len(text)} caratteri.")
            delete_gemini_file(uploaded)

            print("    [Notion] Creazione pagina...")
            page_id = create_notion_page(database_id, file_name)
            blocks  = _build_blocks(text)
            append_blocks(page_id, blocks)
            print(f"    [Notion] OK — {len(blocks)} blocchi archiviati.\n")

            success += 1

        except RuntimeError as exc:
            # Limite giornaliero Gemini: blocca il batch immediatamente.
            print(f"\n  [STOP] {exc}")
            break
        except requests.HTTPError as exc:
            # Errore HTTP non critico: logga e continua col prossimo file.
            print(f"    [ERRORE HTTP {exc.response.status_code}] "
                  f"{exc.response.text[:200]}\n")
        except Exception as exc:
            print(f"    [ERRORE] {exc}\n")

        if index < total:
            print(f"    Pausa {SLEEP_BETWEEN_FILES}s...")
            time.sleep(SLEEP_BETWEEN_FILES)
            print()

    return success, total

# ---------------------------------------------------------------------------
# ENTRY POINT
# ---------------------------------------------------------------------------

def main() -> None:
    print("\n" + "="*58)
    print("  PDF -> GEMINI -> NOTION  |  Automazione note")
    print("="*58)

    validate_env()
    genai.configure(api_key=GEMINI_API_KEY)

    # Stato iniziale utilizzo Gemini.
    remaining = get_remaining_calls()
    print(f"\n  [Gemini] Chiamate disponibili oggi: {remaining}/{GEMINI_DAILY_LIMIT}")
    if remaining <= 0:
        print("  [!] Limite giornaliero raggiunto. Riprova domani.")
        sys.exit(1)

    session_success = 0
    session_total   = 0

    while True:
        # Configurazione (una volta per corso).
        try:
            pdf_folder, database_id, course_name, db_title, prompt = setup_session()
        except (RuntimeError, KeyboardInterrupt) as exc:
            print(f"\n  Setup annullato: {exc}")
            break

        # Avviso se i PDF superano le chiamate residue.
        pdf_count = len(sorted(pdf_folder.glob("*.pdf")))
        remaining = get_remaining_calls()
        if pdf_count > remaining:
            print(
                f"\n  Attenzione: {pdf_count} PDF ma solo {remaining} chiamate "
                f"disponibili oggi.\n  Lo script si fermera al raggiungimento del limite."
            )

        # Avvio elaborazione automatica.
        success, total = run_batch(pdf_folder, database_id, prompt, course_name, db_title)
        session_success += success
        session_total   += total

        print(f"\n  Risultato: {success}/{total} file archiviati su Notion.")

        # Proposta di nuovo corso.
        print("\n" + "-"*58)
        again = input("  Elaborare un altro corso? [s/n]: ").strip().lower()
        if again != "s":
            break
        print()

    # Riepilogo finale.
    usage     = _load_usage()
    today     = datetime.date.today().isoformat()
    used_oggi = usage.get("count", 0) if usage.get("date") == today else 0

    print(f"\n{'='*58}")
    print(f"  Sessione terminata.")
    print(f"  File archiviati     : {session_success}/{session_total}")
    print(f"  Chiamate Gemini oggi: {used_oggi}/{GEMINI_DAILY_LIMIT}")
    print(f"{'='*58}\n")


if __name__ == "__main__":
    main()
