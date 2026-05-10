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
    pip install google-genai python-dotenv requests

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
import re
import google.genai as genai
import google.genai.types as genai_types
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# CONFIGURAZIONE FISSA
# ---------------------------------------------------------------------------

load_dotenv()

GEMINI_API_KEY      = os.getenv("GEMINI_API_KEY")
NOTION_TOKEN        = os.getenv("NOTION_TOKEN")
NOTION_ROOT_PAGE_ID = os.getenv("NOTION_ROOT_PAGE_ID")

GEMINI_MODEL       = "gemini-2.5-flash"
GEMINI_DAILY_LIMIT = 200
USAGE_FILE         = pathlib.Path(__file__).parent / "gemini_usage.json"

NOTION_API_BASE        = "https://api.notion.com/v1"
NOTION_VERSION         = "2022-06-28"
NOTION_MAX_BLOCK_CHARS = 1900
SLEEP_NOTION_BATCH     = 0.4   # secondi tra batch di blocchi Notion
SLEEP_BETWEEN_FILES    = 5     # secondi di pausa tra un PDF e il successivo

# Client Gemini — inizializzato in main() dopo validate_env().
gemini_client = genai.Client(
        api_key=GEMINI_API_KEY, 
        http_options={"timeout": 20.0} 
    )

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
Provide necessary background information and deep-dive explanations, but keep the output concise and highly dense with information. Avoid dispersive verbosity, fluff, or overly long text.

# FORMATTING & EXPORT RULES (OPTIMIZED FOR NOTION)
- Absolute Heading Limit: MAXIMUM HEADING DEPTH IS 3 (`###`). If you need deeper nesting, use bold text within the paragraph instead of `####` (NO HEADINGS 4).
- Readability & Flow: Break lines immediately after each sentence.
- Zero Blank Lines: DO NOT output any empty lines between paragraphs, headings, or list items. Every single line of your output must contain text.
- At the end of each h2 section and before a new h1 (except the first), add a line (---) to visually separate it from the next one. 
- No Bullet-Point Spam: Use lists ONLY for sequential steps or raw itemized data. Use narrative paragraphs for explanations.
- Emphasis: Use **bold** text strategically.
- Emojis: Prefix every `##` and `###` heading with a single relevant emoji. Do NOT add emojis to `#` top-level headings.
- Formulas and Math: Extract and explain EVERY formula. Format for Notion: inline math within `$` (e.g., $E=mc^2$) and display/block math on its own line within `$$` (e.g., $$\hat{{y}} = \sigma(Wx+b)$$). Never use code blocks for math.
- Citations: Place ALL citations exclusively at the very end in a "References" section, NOT in the middle of the notes. Do NOT include any in-line citations or bibliography entries within the main content.
- Output Constraints: Output ONLY the study notes in British English. Do not print tags like "[inference]".

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

    # 3. Navigazione Notion (il subject viene usato per auto-selezionare il corso)
    database_id, course_name, db_title = navigate_to_database(subject)

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


def _fetch_database_title(database_id: str) -> str:
    """Recupera il titolo reale di un database tramite GET /databases/{id}."""
    try:
        r = requests.get(
            f"{NOTION_API_BASE}/databases/{database_id}",
            headers=_notion_headers(),
            timeout=30,
        )
        r.raise_for_status()
        data = r.json()
        parts = data.get("title", [])
        return parts[0].get("plain_text", "") if parts else ""
    except Exception:
        return ""


# Tipi di blocco che possono contenere altri blocchi (ricerca ricorsiva).
_CONTAINER_TYPES = {
    "column_list", "column", "toggle", "callout",
    "bulleted_list_item", "numbered_list_item", "quote",
    "synced_block", "template", "table",
}

def fetch_children_as_targets(parent_id: str, _depth: int = 0) -> list[dict]:
    """
    Cerca ricorsivamente child_database e child_page dentro la pagina corso,
    attraversando blocchi contenitore (column_list, column, toggle, ecc.).
    I tab Notion sono spesso annidati in strutture a colonne.
    Ogni elemento ha: id, title, kind ("database" | "page").
    """
    if _depth > 4:          # limite di sicurezza alla ricorsione
        return []
    items = []
    for b in _fetch_children(parent_id):
        btype = b.get("type")
        if btype == "child_database":
            db_id = b["id"]
            title = b.get("child_database", {}).get("title", "").strip()
            if not title:
                title = _fetch_database_title(db_id)
            items.append({"id": db_id, "title": title or "Senza titolo", "kind": "database"})
        elif btype == "child_page":
            items.append({
                "id": b["id"],
                "title": b.get("child_page", {}).get("title", "Senza titolo"),
                "kind": "page",
            })
        elif btype in _CONTAINER_TYPES and b.get(btype, {}).get("has_children") is not False:
            # Scende nei blocchi contenitore per trovare pagine/database annidati.
            nested = fetch_children_as_targets(b["id"], _depth + 1)
            items.extend(nested)
    return items


def resolve_database_id(target: dict) -> str:
    """
    Dato un target (database o pagina), restituisce l'ID del database da usare.
    - Se è già un database → usa l'ID direttamente.
    - Se è una pagina (es. tab "Notes") → cerca il primo child_database al suo interno.
    """
    if target["kind"] == "database":
        return target["id"]
    # È una pagina: cerca il database al suo interno.
    inner = [
        b for b in _fetch_children(target["id"])
        if b.get("type") == "child_database"
    ]
    if not inner:
        raise RuntimeError(
            f"Nessun database trovato dentro la pagina '{target['title']}'. "
            "Assicurati che contenga un database inline."
        )
    return inner[0]["id"]


def fetch_database_entries(database_id: str) -> list[dict]:
    """
    Legge le pagine contenute in un database Notion (es. il database 'Courses').
    Usa POST /databases/{id}/query invece di /blocks/{id}/children.
    """
    results, payload = [], {"page_size": 100}
    url = f"{NOTION_API_BASE}/databases/{database_id}/query"
    while url:
        r = requests.post(url, headers=_notion_headers(), json=payload, timeout=30)
        r.raise_for_status()
        data = r.json()
        for page in data.get("results", []):
            title = "Senza titolo"
            for prop in page.get("properties", {}).values():
                if prop.get("type") == "title":
                    parts = prop.get("title", [])
                    if parts:
                        title = parts[0].get("plain_text", "Senza titolo")
                    break
            results.append({"id": page["id"], "title": title})
        if data.get("has_more"):
            payload = {"page_size": 100, "start_cursor": data["next_cursor"]}
        else:
            url = None
    return results


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


def navigate_to_database(subject: str = "") -> tuple[str, str, str]:
    """
    Navigazione interattiva: Courses > Corso > Database.
    Se `subject` corrisponde esattamente (case-insensitive) a un corso Notion,
    lo seleziona automaticamente senza mostrare la lista.

    Returns:
        (database_id, course_name, database_title)
    """
    print("\n" + "="*58)
    print("  SELEZIONE CORSO E DATABASE NOTION")
    print("="*58)

    while True:
        print("\n  Recupero corsi...")
        # Courses è un database: si interroga con /databases/{id}/query.
        courses = fetch_database_entries(NOTION_ROOT_PAGE_ID)
        if not courses:
            raise RuntimeError(
                "Nessun corso trovato nel database Courses. "
                "Controlla che l'integrazione abbia accesso alla pagina."
            )

        # Auto-selezione: match parziale (substring) e case-insensitive
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
            course = _pick(courses, "CORSI DISPONIBILI")

        print(f"\n  Recupero sezioni in '{course['title']}'...")
        targets = fetch_children_as_targets(course["id"])

        if not targets:
            print(f"\n  [!] Nessuna sezione trovata in '{course['title']}'.")
            if input("  Scegli un altro corso? [s/n]: ").strip().lower() == "s":
                continue
            raise RuntimeError("Nessuna sezione trovata. Operazione annullata.")

        # Auto-selezione se esiste una sezione chiamata "Notes".
        auto_db = next((t for t in targets if t["title"].strip().lower() == "notes"), None)
        if auto_db:
            target = auto_db
            print(f"  Sezione selezionata automaticamente: \"{target['title']}\"")
        else:
            target = _pick(targets, f"SEZIONI IN '{course['title'].upper()}'")

        db_id = resolve_database_id(target)
        return db_id, course["title"], target["title"]

# ---------------------------------------------------------------------------
# GEMINI
# ---------------------------------------------------------------------------

def upload_pdf_to_gemini(pdf_path: str) -> genai_types.File:
    uploaded = gemini_client.files.upload(
        file=pdf_path,
        config=genai_types.UploadFileConfig(mime_type="application/pdf"),
    )
    while uploaded.state.name == "PROCESSING":
        time.sleep(3)
        uploaded = gemini_client.files.get(name=uploaded.name)
    if uploaded.state.name == "FAILED":
        raise RuntimeError(f"Gemini: elaborazione fallita per '{pdf_path}'.")
    return uploaded


def generate_notes(uploaded: genai_types.File, prompt: str) -> str:
    check_and_increment_usage()
    max_retries = 5   
    base_delay = 15   

    for attempt in range(max_retries):
        try:
            response = gemini_client.models.generate_content(
                model=GEMINI_MODEL,
                contents=[prompt, uploaded],
            )
            return response.text
        except Exception as exc:
            # Se l'errore è un 429 (Quota esaurita), blocca tutto istantaneamente
            if "429" in str(exc) or "RESOURCE_EXHAUSTED" in str(exc):
                raise RuntimeError(f"Quota API esaurita (Errore 429). Elaborazione bloccata. Dettagli: {exc}")

            if attempt == max_retries - 1:
                # Se fallisce anche l'ultimo tentativo, alza l'errore per fermare/gestire
                raise exc
            
            # Backoff: 15s, 30s, 60s, 120s...
            delay = base_delay * (2 ** attempt)  
            print(f"    [ATTENZIONE] Rete/Server instabile ({exc}). Ritento tra {delay}s... ({attempt + 1}/{max_retries})")
            time.sleep(delay)


def delete_gemini_file(uploaded: genai_types.File) -> None:
    try:
        gemini_client.files.delete(name=uploaded.name)
    except Exception:
        pass  # I file Gemini scadono automaticamente dopo 48h.

# ---------------------------------------------------------------------------
# NOTION — CREAZIONE PAGINA E BLOCCHI
# ---------------------------------------------------------------------------

def page_exists(database_id: str, title: str) -> bool:
    """Controlla se una pagina con quel titolo esiste già nel database Notion."""
    r = requests.post(
        f"{NOTION_API_BASE}/databases/{database_id}/query",
        headers=_notion_headers(),
        json={"filter": {"property": "Name", "title": {"equals": title}}},
        timeout=30,
    )
    r.raise_for_status()
    return len(r.json().get("results", [])) > 0


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


def _parse_rich_text(line: str) -> list[dict]:
    """
    Converte una riga Markdown in una lista di rich_text Notion gestendo:
      - **bold** → testo con annotazione bold
      - $formula$ → oggetto equation inline
      - testo normale → oggetto text
    Tronca ogni segmento a NOTION_MAX_BLOCK_CHARS.
    """
    parts = []
    # Tokenizza per **bold** e $math$ (in quest'ordine, bold ha precedenza).
    pattern = re.compile(r'(\*\*(.+?)\*\*|\$(?!\$)(.+?)(?<!\$)\$)')
    cursor = 0
    for m in pattern.finditer(line):
        # Testo normale prima del match
        if m.start() > cursor:
            seg = line[cursor:m.start()][:NOTION_MAX_BLOCK_CHARS]
            if seg:
                parts.append({"type": "text", "text": {"content": seg}})
        if m.group(0).startswith("**"):
            # Bold
            seg = m.group(2)[:NOTION_MAX_BLOCK_CHARS]
            parts.append({
                "type": "text",
                "text": {"content": seg},
                "annotations": {"bold": True},
            })
        else:
            # Inline math
            expr = m.group(3)[:NOTION_MAX_BLOCK_CHARS]
            parts.append({"type": "equation", "equation": {"expression": expr}})
        cursor = m.end()
    # Testo rimanente
    if cursor < len(line):
        seg = line[cursor:][:NOTION_MAX_BLOCK_CHARS]
        if seg:
            parts.append({"type": "text", "text": {"content": seg}})
    # Fallback: riga vuota
    return parts or [{"type": "text", "text": {"content": ""}}]


def _build_blocks(text: str) -> list[dict]:
    """
    Converte il testo Markdown di Gemini in blocchi Notion.
    Gestisce:
      # h1, ## h2 (con emoji), ### h3 (con emoji)
      - /* bullet, 1. numbered list
      $$...$$ → equation block nativo Notion
      $...$ inline → equation rich_text inline
      **bold** → annotazione bold
      testo normale
    """
    blocks = []

    # Gestione $$...$$ multiriga: raccoglie le righe tra $$ apertura e chiusura.
    display_math_buf: list[str] = []
    in_display_math = False

    for line in text.splitlines():
        s = line.strip()

        # ── Apertura/chiusura blocco $$ ──────────────────────────────────────
        if s == "$$":
            if in_display_math:
                # Chiude il blocco e crea un equation block
                expr = "\n".join(display_math_buf).strip()
                blocks.append({
                    "object": "block", "type": "equation",
                    "equation": {"expression": expr},
                })
                display_math_buf = []
                in_display_math = False
            else:
                in_display_math = True
            continue

        if in_display_math:
            display_math_buf.append(s)
            continue

        # $$ su una sola riga: $$formula$$
        if s.startswith("$$") and s.endswith("$$") and len(s) > 4:
            expr = s[2:-2].strip()
            blocks.append({
                "object": "block", "type": "equation",
                "equation": {"expression": expr},
            })
            continue

        if not s:
            blocks.append({
                "object": "block", "type": "paragraph",
                "paragraph": {"rich_text": []},
            })
            continue

        # Linea di divisione (Divider)
        if s == "---":
            blocks.append({
                "object": "block", "type": "divider",
                "divider": {}
            })
            continue

        # Heading 1
        if s.startswith("# ") and not s.startswith("## "):
            content = s[2:].strip()
            blocks.append({
                "object": "block", "type": "heading_1",
                "heading_1": {"rich_text": _parse_rich_text(content[:NOTION_MAX_BLOCK_CHARS])},
            })
            continue

        # Heading 2
        if s.startswith("## ") and not s.startswith("### "):
            content = s[3:].strip()
            blocks.append({
                "object": "block", "type": "heading_2",
                "heading_2": {"rich_text": _parse_rich_text(content[:NOTION_MAX_BLOCK_CHARS])},
            })
            continue

        # Heading 3
        if s.startswith("### "):
            content = s[4:].strip()
            blocks.append({
                "object": "block", "type": "heading_3",
                "heading_3": {"rich_text": _parse_rich_text(content[:NOTION_MAX_BLOCK_CHARS])},
            })
            continue

        # Bullet point
        if s.startswith(("- ", "* ")):
            content = s[2:].strip()
            blocks.append({
                "object": "block", "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": _parse_rich_text(content)},
            })
            continue

        # Numbered list (1. 2. ecc.)
        if len(s) > 2 and s[0].isdigit() and s[1] in ".)" and s[2] == " ":
            content = s[3:].strip()
            blocks.append({
                "object": "block", "type": "numbered_list_item",
                "numbered_list_item": {"rich_text": _parse_rich_text(content)},
            })
            continue

        # Paragrafo normale
        blocks.append({
            "object": "block", "type": "paragraph",
            "paragraph": {"rich_text": _parse_rich_text(s)},
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
            print("    [Notion] Controllo duplicati...")
            if page_exists(database_id, file_name):
                print("    [Notion] Pagina già esistente — skip.\n")
                continue  # Passa subito al prossimo file senza pause inutili

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

            # Dopo il primo file chiede conferma prima di continuare.
            if index == 1 and total > 1:
                print(f"\n  Primo file completato. Controlla la pagina su Notion.")
                print(f"  Rimangono {total - 1} file da elaborare.")
                go = input("  Continuare con gli altri? [s/n]: ").strip().lower()
                if go != "s":
                    print("  Elaborazione interrotta dall'utente.")
                    break

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
    global gemini_client
    gemini_client = genai.Client(api_key=GEMINI_API_KEY)

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
