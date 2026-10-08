import re
from typing import List, Dict, Any, Tuple, Optional

NOTION_MAX_BLOCK_CHARS = 1900

# Notion-supported languages for code blocks
NOTION_SUPPORTED_LANGUAGES = {
    "abap", "arduino", "bash", "basic", "c", "clojure", "coffeescript", "c++", "c#",
    "css", "dart", "diff", "docker", "elixir", "elm", "erlang", "flow", "fortran",
    "f#", "gherkin", "glsl", "go", "graphql", "groovy", "haskell", "html", "java",
    "javascript", "json", "julia", "kotlin", "latex", "less", "lisp", "livescript",
    "lua", "makefile", "markdown", "markup", "matlab", "mermaid", "nix", "objective-c",
    "ocaml", "pascal", "perl", "php", "plain text", "powershell", "prolog", "protobuf",
    "python", "r", "reason", "ruby", "rust", "sass", "scala", "scheme", "scss",
    "shell", "sql", "swift", "typescript", "vb.net", "verilog", "vhdl", "visual basic",
    "webassembly", "xml", "yaml", "java/c/c++/c#"
}

def normalize_sentence_spacing(text: str) -> str:
    """
    Ensures a single space exists after sentence-ending punctuation
    when followed immediately by a letter (e.g. 'concept.Next' -> 'concept. Next').
    Avoids altering numbers ('3.14') or valid LaTeX.
    """
    text = re.sub(r'([a-zA-Z0-9\)])\.([A-Z])', r'\1. \2', text)
    text = re.sub(r'([a-zA-Z0-9\)]):([A-Za-z])', r'\1: \2', text)
    text = re.sub(r'([a-zA-Z0-9\)]),([A-Za-z])', r'\1, \2', text)
    text = re.sub(r'([a-zA-Z0-9\)]);([A-Za-z])', r'\1; \2', text)
    return text

def parse_rich_text(line: str, annotations: Dict[str, bool] = None) -> List[Dict[str, Any]]:
    """
    Converts a Markdown line into Notion rich_text objects.
    Recursively handles nested formatting:
      - `code` -> rich_text with code annotation
      - $$formula$$ / $formula$ -> inline equation object (even inside bold or italic)
      - ***bold italic*** -> rich_text with bold and italic annotations (recursive)
      - **bold** -> rich_text with bold annotation (recursive)
      - *italic* -> rich_text with italic annotation (recursive)
      - plain text -> text object
    Normalizes punctuation spacing and truncates individual segments to NOTION_MAX_BLOCK_CHARS.
    """
    if annotations is None:
        line = normalize_sentence_spacing(line)
        annotations = {}

    parts: List[Dict[str, Any]] = []
    pattern = re.compile(
        r'(`([^`]+)`)'
        r'|(\$\$([^\$]+)\$\$)'
        r'|(\$(?!\$)([^\$]+?)(?<!\$)\$)'
        r'|(\*\*\*(.+?)\*\*\*)'
        r'|(\*\*(.+?)\*\*)'
        r'|((?<!\*)\*(?!\s|\*)(.+?)(?<!\s|\*)\*(?!\*))'
    )
    cursor = 0

    for m in pattern.finditer(line):
        if m.start() > cursor:
            seg = line[cursor:m.start()][:NOTION_MAX_BLOCK_CHARS]
            if seg:
                item: Dict[str, Any] = {"type": "text", "text": {"content": seg}}
                if annotations:
                    item["annotations"] = dict(annotations)
                parts.append(item)

        # 1: Code `...` -> Group 2
        if m.group(2) is not None:
            seg = m.group(2)[:NOTION_MAX_BLOCK_CHARS]
            code_ann = dict(annotations)
            code_ann["code"] = True
            parts.append({
                "type": "text",
                "text": {"content": seg},
                "annotations": code_ann,
            })
        # 2: $$...$$ -> Group 4
        elif m.group(4) is not None:
            expr = m.group(4).strip()[:NOTION_MAX_BLOCK_CHARS]
            eq_item: Dict[str, Any] = {"type": "equation", "equation": {"expression": expr}}
            if annotations:
                eq_item["annotations"] = dict(annotations)
            parts.append(eq_item)
        # 3: $...$ -> Group 6
        elif m.group(6) is not None:
            expr = m.group(6).strip()[:NOTION_MAX_BLOCK_CHARS]
            eq_item = {"type": "equation", "equation": {"expression": expr}}
            if annotations:
                eq_item["annotations"] = dict(annotations)
            parts.append(eq_item)
        # 4: ***...*** -> Group 8
        elif m.group(8) is not None:
            sub_ann = dict(annotations)
            sub_ann["bold"] = True
            sub_ann["italic"] = True
            parts.extend(parse_rich_text(m.group(8), sub_ann))
        # 5: **...** -> Group 10
        elif m.group(10) is not None:
            sub_ann = dict(annotations)
            sub_ann["bold"] = True
            parts.extend(parse_rich_text(m.group(10), sub_ann))
        # 6: *...* -> Group 12
        elif m.group(12) is not None:
            sub_ann = dict(annotations)
            sub_ann["italic"] = True
            parts.extend(parse_rich_text(m.group(12), sub_ann))

        cursor = m.end()

    if cursor < len(line):
        seg = line[cursor:][:NOTION_MAX_BLOCK_CHARS]
        if seg:
            item = {"type": "text", "text": {"content": seg}}
            if annotations:
                item["annotations"] = dict(annotations)
            parts.append(item)

    return parts or [{"type": "text", "text": {"content": ""}}]


def split_table_row(line: str) -> List[str]:
    """
    Estrae le singole celle da una riga di tabella Markdown delimitata da pipe.
    Gestisce pipe escapati (\\|) per evitare split incorretti su formule matematiche.
    """
    content = line.strip()
    if content.startswith("|"):
        content = content[1:]
    if content.endswith("|"):
        content = content[:-1]

    # PERFORMANCE: Preserviamo i pipe escapati tramite placeholder temporaneo
    placeholder = "___ESCAPED_PIPE___"
    content = content.replace(r"\|", placeholder)
    return [c.replace(placeholder, "|").strip() for c in content.split("|")]

def is_table_separator(line: str) -> bool:
    """
    Verifica se una riga corrisponde alla riga separatore della tabella Markdown GFM
    (composta da caratteri '-', ':', spazi e delimitatori pipe).
    """
    cells = split_table_row(line)
    if not cells:
        return False
    return all(
        ("-" in c) and (set(c.strip()) <= {"-", ":", " "})
        for c in cells
    )


def sanitize_mermaid_mindmap(content: str) -> str:
    """
    Sanitizza il codice Mermaid mindmap per evitare errori di parsing in Notion e client web.
    # ARCHITETTURA: La grammatica Mermaid mindmap interpreta le parentesi (), quadre [],
    # apici e operatori (->, :) come token di forma o transizione. Se presenti nel testo dei nodi
    # senza racchiuderli in ["..."], il tokenizer di Mermaid solleva eccezioni sintattiche
    # e Notion disabilita il rendering grafico visualizzando un blocco d'errore o testo grezzo.
    # PERFORMANCE: Normalizziamo caratteri speciali e sequenze non-ASCII (es. \\ufffd o em-dash)
    # a trattini ASCII canonici (' - ') per evitare mismatch di codifica UTF-8/CP1252 tra OS.
    """
    # TRADE-OFF: Sostituzione preventiva di caratteri di rimpiazzo e spazi non separabili
    content = content.replace("\ufffd", " - ").replace("\u00a0", " ")
    lines = content.splitlines()
    sanitized_lines = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            sanitized_lines.append(line)
            continue

        if stripped.lower() == "mindmap":
            sanitized_lines.append(line)
            continue

        indent = len(line) - len(line.lstrip(" "))
        indent_str = " " * indent

        # Nodo radice: root((...)) senza apici annidati
        if stripped.startswith("root((") and stripped.endswith("))"):
            raw_inner = stripped[6:-2].strip().strip("\"'").replace('"', "").replace("'", "")
            sanitized_lines.append(f'{indent_str}root(("{raw_inner}"))')
            continue

        # Già formattato con delimitatori espliciti sicuri racchiusi da apici
        is_bracketed = (
            (stripped.startswith('["') and stripped.endswith('"]')) or
            (stripped.startswith('("') and stripped.endswith('")')) or
            (stripped.startswith('(("') and stripped.endswith('"))'))
        )
        if is_bracketed:
            # Sostituisce eventuali frecce -> o em-dash con trattino standard
            clean_line = re.sub(r'\s*(?:->|—)\s*', ' - ', line)
            sanitized_lines.append(clean_line)
            continue

        # Forme composte con testo prefisso: es. Moore's Law((N_T(t) ...))
        m_shape = re.match(r"^(.*?)\(\((.*?)\)\)$", stripped)
        if m_shape:
            prefix, inner = m_shape.group(1).strip(), m_shape.group(2).strip()
            clean_text = f"{prefix}: {inner}" if prefix else inner
            clean_text = clean_text.replace('"', "'")
            clean_text = re.sub(r'\s*(?:->|—)\s*', ' - ', clean_text)
            sanitized_lines.append(f'{indent_str}["{clean_text}"]')
            continue

        # Se il nodo contiene parentesi, operatori o punteggiatura, racchiudi in ["..."]
        if any(c in stripped for c in "()[]:\"->,;"):
            clean_text = stripped.strip("\"'").replace('"', "'")
            clean_text = re.sub(r'\s*(?:->|—)\s*', ' - ', clean_text)
            sanitized_lines.append(f'{indent_str}["{clean_text}"]')
        else:
            sanitized_lines.append(line)

    return "\n".join(sanitized_lines)


def sanitize_mermaid_flowchart(content: str) -> str:
    """
    Sanitizza diagrammi di flusso Mermaid (graph TD / flowchart TD) per Notion e renderer web.
    # ARCHITETTURA: Nei flowchart Mermaid elaborati con motore ELK (Eclipse Layout Kernel,
    # usato internamente da Notion e dai moderni renderer per layout gerarchici), si verificano due
    # crash critici 'TypeError: Cannot read properties of null (reading \'re\')':
    # 1. Dichiarazione di subgraph senza ID alfanumerico esplicito (es. 'subgraph MapReduce Word Count'):
    #    il parser ELK perde la risoluzione del genitore nell'AST e fallisce il lookup shape;
    # 2. Parentesi quadre annidate o apici spaiati dentro label quotate (es. 'Bear:[1,1]' o '\"\'Deer\'\"'):
    #    la regex del tokenizer Mermaid si interrompe prematuramente lasciando nodi orfani.
    # Normalizziamo deterministicamente subgraphs e nodi a sintassi pienamente conforme.
    """
    content = content.replace("\ufffd", " - ").replace("\u00a0", " ")
    lines = content.splitlines()

    # ARCHITETTURA: Identificazione preventiva di tutti i subgraph e del rispettivo primo nodo membro.
    # Se un arco punta direttamente all'ID di un subgraph (es. 'ROOT --> BDF' o 'BDF --> NEXT'),
    # l'engine ELK fallisce la risoluzione del vertice sollevando 'Cannot read properties of null (reading re)'.
    # Ridirigiamo deterministicamente tali archi al primo nodo effettivo del cluster.
    subgraph_map: Dict[str, Optional[str]] = {}
    current_sg: Optional[str] = None

    for line in lines:
        stripped = line.strip()
        m_sub = re.match(r'^subgraph\s+([A-Za-z0-9_]+)', stripped, re.IGNORECASE)
        if m_sub:
            current_sg = m_sub.group(1)
            if current_sg not in subgraph_map:
                subgraph_map[current_sg] = None
            continue
        if stripped.lower() == 'end':
            current_sg = None
            continue
        if current_sg and subgraph_map[current_sg] is None:
            m_node = re.match(r'^([A-Za-z0-9_]+)\s*[\(\[\{]', stripped)
            if m_node:
                subgraph_map[current_sg] = m_node.group(1)

    sanitized_lines = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            sanitized_lines.append(line)
            continue

        indent = len(line) - len(line.lstrip(" "))
        indent_str = " " * indent

        # 1. Rimuove punto e virgola finale ridondante a fine riga
        line_clean = re.sub(r';\s*$', '', stripped)

        # 2. Normalizzazione Subgraph (risoluzione root cause 'reading re' in ELK)
        m_sub = re.match(r'^subgraph\s+(.+)$', line_clean, re.IGNORECASE)
        if m_sub:
            sub_body = m_sub.group(1).strip()
            # Caso a: già valido con ID e titolo quotato (es. 'subgraph MR ["Word Count"]')
            if re.match(r'^[A-Za-z0-9_]+\s*\["[^"]+"\]$', sub_body):
                sanitized_lines.append(f"{indent_str}subgraph {sub_body}")
                continue
            # Caso b: ID con titolo in quadre ma non quotato (es. 'subgraph MR [Word Count]')
            m_id_bracket = re.match(r'^([A-Za-z0-9_]+)\s*\[([^"\]]+)\]$', sub_body)
            if m_id_bracket:
                sid, stitle = m_id_bracket.group(1), m_id_bracket.group(2).strip()
                sanitized_lines.append(f'{indent_str}subgraph {sid} ["{stitle}"]')
                continue
            # Caso c: solo titolo tra virgolette senza ID (es. 'subgraph "Word Count"')
            m_quoted_only = re.match(r'^"([^"]+)"$', sub_body)
            if m_quoted_only:
                stitle = m_quoted_only.group(1).strip()
                slug = "sg_" + re.sub(r'[^A-Za-z0-9_]+', '_', stitle).strip('_')
                sanitized_lines.append(f'{indent_str}subgraph {slug} ["{stitle}"]')
                continue
            # Caso d: singolo identificatore alfanumerico (es. 'subgraph MR')
            if re.match(r'^[A-Za-z0-9_]+$', sub_body):
                sanitized_lines.append(f"{indent_str}subgraph {sub_body}")
                continue
            # Caso e: titolo con parole multiple non quotato (es. 'subgraph MapReduce Word Count Example')
            stitle = sub_body.strip("\"'")
            slug = "sg_" + re.sub(r'[^A-Za-z0-9_]+', '_', stitle).strip('_')
            sanitized_lines.append(f'{indent_str}subgraph {slug} ["{stitle}"]')
            continue

        # 3. Normalizzazione stile subgraph: impedisce fill opachi o chiari (es. fill:#f8fafc) che in Notion Dark Mode
        # causano contrasto inverso bianco-su-bianco ('white on white') per i titoli dei cluster.
        # Imponiamo deterministico fill:none e stroke adattivo neutro (#64748b).
        m_style_sg = re.match(r'^style\s+([A-Za-z0-9_]+)\s+(.+)$', line_clean, re.IGNORECASE)
        if m_style_sg:
            sg_id = m_style_sg.group(1)
            style_props = m_style_sg.group(2)
            if sg_id in subgraph_map:
                style_props = re.sub(r'fill:[^,;]+', 'fill:none', style_props)
                style_props = re.sub(r'stroke:(?:#94a3b8|#cbd5e1|#e2e8f0)', 'stroke:#64748b', style_props)
                sanitized_lines.append(f"{indent_str}style {sg_id} {style_props}")
                continue

        # 4. Normalizzazione sicura dei nodi rettangolari [ ... ] e rombi { ... }
        # ARCHITETTURA: Un regex greedy su [ ... ] o { ... } ingloba frecce come '-->'
        # e nodi successivi sulla stessa riga (es. 'A[L1] --> B[L2]'), distruggendo la topologia
        # e generando un blocco non valido che manda in crash il layout ELK.
        # Splittiamo deterministicamente sui token freccia per processare ciascun nodo isolatamente.
        arrow_pattern = r'(\s*(?:-->|---|-.->|-.-|==>|==)(?:\|[^|\n]+\|)?\s*)'
        parts = re.split(arrow_pattern, line_clean)
        cleaned_parts = []

        for part in parts:
            if re.match(r'^\s*(?:-->|---|-.->|-.-|==>|==)', part):
                cleaned_parts.append(part)
                continue

            semicolon = ";" if part.rstrip().endswith(";") else ""
            clean_part = part.rstrip().rstrip(";").strip()

            m_bracket = re.match(r'^([A-Za-z0-9_]+)\[(.*)\]$', clean_part)
            m_rhombus = re.match(r'^([A-Za-z0-9_]+)\{(.*)\}$', clean_part)

            if m_bracket:
                nid = m_bracket.group(1)
                content = m_bracket.group(2).strip()
                if (content.startswith('"') and content.endswith('"')) or (content.startswith("'") and content.endswith("'")):
                    content = content[1:-1].strip()
                content = content.replace('"', "")
                content = re.sub(r"(^'|'$|(?<=[\s,])'|'(?=[\s,]))", "", content)
                content = re.sub(r'\[([^\]]*)\]', r'(\1)', content)
                content = re.sub(r'\s*->\s*', ' - ', content)
                part = f'{nid}["{content}"]{semicolon}'
            elif m_rhombus:
                nid = m_rhombus.group(1)
                content = m_rhombus.group(2).strip()
                if (content.startswith('"') and content.endswith('"')) or (content.startswith("'") and content.endswith("'")):
                    content = content[1:-1].strip()
                content = content.replace('"', "")
                content = re.sub(r"(^'|'$|(?<=[\s,])'|'(?=[\s,]))", "", content)
                content = re.sub(r'\[([^\]]*)\]', r'(\1)', content)
                content = re.sub(r'\s*->\s*', ' - ', content)
                part = f'{nid}{{"{content}"}}{semicolon}'

            cleaned_parts.append(part)

        line_clean = "".join(cleaned_parts)

        # 4. Re-indirizzamento archi che puntano a subgraph ID invece che a nodi
        for sg_id, first_node in subgraph_map.items():
            if first_node:
                line_clean = re.sub(rf'\b{sg_id}\s*(-->|---|-.->|==>)\s*', f'{first_node} \\1 ', line_clean)
                line_clean = re.sub(rf'\s*(-->|---|-.->|==>)\s*{sg_id}\b', f' \\1 {first_node}', line_clean)

        sanitized_lines.append(f"{indent_str}{line_clean}")

    return "\n".join(sanitized_lines)


def build_notion_blocks(markdown_text: str) -> List[Dict[str, Any]]:
    """
    Parses full Markdown text into a list of Notion-compliant block dictionaries.
    Supports:
      - Multiline and single-line LaTeX display equations ($$...$$)
      - Fenced code blocks (```lang ... ```)
      - GFM Tables (| header | ... |) rendered to native Notion table blocks
      - Blockquotes (> ...)
      - Headings (H1, H2, H3) with automatic dividers
      - Bulleted and numbered lists
      - Horizontal dividers (---)
      - Standard paragraphs with rich_text formatting
    """
    blocks: List[Dict[str, Any]] = []
    lines = markdown_text.splitlines()

    in_display_math = False
    display_math_buf: List[str] = []

    in_code_block = False
    code_block_lang = "plain text"
    code_block_buf: List[str] = []

    table_buf: List[str] = []

    # ARCHITETTURA: Stack di indentazione per preservare la gerarchia ad albero dei bullet points
    # e delle liste numerate verso Notion. Notion accetta 'children' annidati all'interno del blocco genitore.
    list_root_blocks: List[Dict[str, Any]] = []
    list_stack: List[Dict[str, Any]] = [
        {"indent": -1, "type": "root", "payload": None, "children": list_root_blocks}
    ]

    def flush_list() -> None:
        nonlocal list_root_blocks, list_stack
        if list_root_blocks:
            blocks.extend(list_root_blocks)
            list_root_blocks = []
        list_stack = [
            {"indent": -1, "type": "root", "payload": None, "children": list_root_blocks}
        ]

    def flush_table() -> None:
        nonlocal table_buf
        if not table_buf:
            return

        # ARCHITETTURA: Conformità alle specifiche Notion API per il blocco 'table'.
        # Richiede table_width costante e ogni riga table_row con lista di celle corrispondente.
        if len(table_buf) >= 2 and is_table_separator(table_buf[1]):
            headers = split_table_row(table_buf[0])
            table_width = len(headers)
            if table_width > 0:
                header_cells = [parse_rich_text(c) if c else [] for c in headers]
                row_children = [
                    {
                        "type": "table_row",
                        "table_row": {"cells": header_cells}
                    }
                ]
                for row_line in table_buf[2:]:
                    if is_table_separator(row_line):
                        continue
                    cells = split_table_row(row_line)
                    # TRADE-OFF: Normalizzazione difensiva della larghezza per prevenire
                    # HTTP 400 da Notion API in caso di righe con colonne disallineate.
                    if len(cells) < table_width:
                        cells.extend([""] * (table_width - len(cells)))
                    else:
                        cells = cells[:table_width]
                    row_cells = [parse_rich_text(c) if c else [] for c in cells]
                    row_children.append({
                        "type": "table_row",
                        "table_row": {"cells": row_cells}
                    })

                blocks.append({
                    "object": "block",
                    "type": "table",
                    "table": {
                        "table_width": table_width,
                        "has_column_header": True,
                        "has_row_header": False,
                        "children": row_children
                    }
                })
                table_buf = []
                return

        # TRADE-OFF: Se la struttura non è una tabella GFM valida, degrada a paragrafi
        # individuali preservando l'integrità del testo originale senza scartare contenuti.
        for raw_line in table_buf:
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": parse_rich_text(raw_line)},
            })
        table_buf = []

    for line_idx, line in enumerate(lines):
        s = line.strip()

        # ── Code Block Handling ──────────────────────────────────────────────
        if s.startswith("```"):
            flush_table()
            flush_list()
            if in_code_block:
                # Close code block
                full_code = "\n".join(code_block_buf)
                if code_block_lang == "mermaid":
                    if "mindmap" in full_code:
                        full_code = sanitize_mermaid_mindmap(full_code)
                    elif "graph" in full_code or "flowchart" in full_code:
                        full_code = sanitize_mermaid_flowchart(full_code)

                # ARCHITETTURA: Notion API supporta fino a 100 elementi rich_text (ciascuno max 2000 chars)
                # all'interno dello STESSO blocco code (capienza complessiva fino a 200.000 caratteri).
                # Chunkare su blocchi multipli spezza irrimediabilmente la continuità di script e diagrammi Mermaid.
                # Raggruppiamo i chunk nella lista rich_text di un singolo blocco code.
                rich_text_chunks: List[Dict[str, Any]] = []
                while full_code:
                    chunk = full_code[:NOTION_MAX_BLOCK_CHARS]
                    full_code = full_code[NOTION_MAX_BLOCK_CHARS:]
                    rich_text_chunks.append({"type": "text", "text": {"content": chunk}})
                    if len(rich_text_chunks) == 100:
                        blocks.append({
                            "object": "block",
                            "type": "code",
                            "code": {
                                "language": code_block_lang,
                                "rich_text": rich_text_chunks,
                            },
                        })
                        rich_text_chunks = []

                if rich_text_chunks:
                    blocks.append({
                        "object": "block",
                        "type": "code",
                        "code": {
                            "language": code_block_lang,
                            "rich_text": rich_text_chunks,
                        },
                    })

                code_block_buf = []
                in_code_block = False
                continue
            else:
                # Open code block
                raw_lang = s[3:].strip().lower()
                code_block_lang = raw_lang if raw_lang in NOTION_SUPPORTED_LANGUAGES else "plain text"
                if raw_lang == "py":
                    code_block_lang = "python"
                elif raw_lang in ("sh", "zsh"):
                    code_block_lang = "shell"
                in_code_block = True
                code_block_buf = []
                continue

        if in_code_block:
            code_block_buf.append(line)  # Preserve original indentation
            continue

        # ── Display Math ($$...$$) ──────────────────────────────────────────
        if s == "$$":
            flush_table()
            flush_list()
            if in_display_math:
                expr = "\n".join(display_math_buf).strip()
                blocks.append({
                    "object": "block",
                    "type": "equation",
                    "equation": {"expression": expr[:NOTION_MAX_BLOCK_CHARS]},
                })
                display_math_buf = []
                in_display_math = False
            else:
                in_display_math = True
            continue

        if in_display_math:
            display_math_buf.append(s)
            continue

        # Single line $$equation$$
        if s.startswith("$$") and s.endswith("$$") and len(s) > 4:
            flush_table()
            flush_list()
            expr = s[2:-2].strip()
            blocks.append({
                "object": "block",
                "type": "equation",
                "equation": {"expression": expr[:NOTION_MAX_BLOCK_CHARS]},
            })
            continue

        # ── Blank Line Handling ──────────────────────────────────────────────
        if not s or s.isspace():
            if table_buf:
                # TOLERANCE: Se stiamo parsando una tabella, controlliamo se la prossima
                # riga non vuota è ancora parte della tabella (es. newline accidentali tra righe).
                next_non_empty = None
                for peek_line in lines[line_idx + 1:]:
                    peek_s = peek_line.strip()
                    if peek_s:
                        next_non_empty = peek_s
                        break
                if next_non_empty and next_non_empty.startswith("|") and "|" in next_non_empty[1:]:
                    continue
                else:
                    flush_table()
            continue

        # ── Markdown Table Lines (| ... |) ───────────────────────────────────
        if s.startswith("|") and "|" in s[1:]:
            flush_list()
            table_buf.append(s)
            continue
        else:
            flush_table()

        # ── Horizontal Divider ──────────────────────────────────────────────
        if s == "---":
            flush_list()
            if blocks and blocks[-1]["type"] != "divider":
                blocks.append({"object": "block", "type": "divider", "divider": {}})
            continue

        # ── Blockquote ──────────────────────────────────────────────────────
        if s.startswith(">"):
            flush_list()
            content = s[1:].strip()
            if content:
                blocks.append({
                    "object": "block",
                    "type": "quote",
                    "quote": {"rich_text": parse_rich_text(content)},
                })
            continue

        # ── Headings with Dividers ──────────────────────────────────────────
        if s.startswith("# ") and not s.startswith("## "):
            flush_list()
            if blocks and blocks[-1]["type"] != "divider":
                blocks.append({"object": "block", "type": "divider", "divider": {}})
            content = s[2:].strip()
            blocks.append({
                "object": "block",
                "type": "heading_1",
                "heading_1": {"rich_text": parse_rich_text(content[:NOTION_MAX_BLOCK_CHARS])},
            })
            continue

        if s.startswith("## ") and not s.startswith("### "):
            flush_list()
            if blocks and blocks[-1]["type"] != "divider":
                blocks.append({"object": "block", "type": "divider", "divider": {}})
            content = s[3:].strip()
            blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": parse_rich_text(content[:NOTION_MAX_BLOCK_CHARS])},
            })
            continue

        if s.startswith("### "):
            flush_list()
            content = s[4:].strip()
            blocks.append({
                "object": "block",
                "type": "heading_3",
                "heading_3": {"rich_text": parse_rich_text(content[:NOTION_MAX_BLOCK_CHARS])},
            })
            continue

        # Fallback for H4 (Notion does not have heading_4; downgrade to heading_3)
        if s.startswith("#### "):
            flush_list()
            content = s[5:].strip()
            blocks.append({
                "object": "block",
                "type": "heading_3",
                "heading_3": {"rich_text": parse_rich_text(content[:NOTION_MAX_BLOCK_CHARS])},
            })
            continue

        # ── Lists & Indented Hierarchy ──────────────────────────────────────
        expanded = line.expandtabs(4)
        l_stripped = expanded.lstrip(" ")
        indent = len(expanded) - len(l_stripped)

        bullet_match = re.match(r"^[-*+]\s+(.*)$", l_stripped)
        num_match = re.match(r"^(\d+[.)])\s+(.*)$", l_stripped)

        if bullet_match or num_match:
            flush_table()
            item_type = "bulleted_list_item" if bullet_match else "numbered_list_item"
            content = bullet_match.group(1).strip() if bullet_match else num_match.group(2).strip()
            new_block = {
                "object": "block",
                "type": item_type,
                item_type: {
                    "rich_text": parse_rich_text(content)
                }
            }

            # ARCHITETTURA: Gestione della gerarchia ad albero tramite stack di indentazione.
            # Riavvolge lo stack finché l'indentazione dell'elemento in cima è strettamente minore
            # di quella della riga corrente, identificando il corretto nodo genitore.
            while len(list_stack) > 1 and indent <= list_stack[-1]["indent"]:
                list_stack.pop()

            parent = list_stack[-1]
            if parent["payload"] is not None and "children" not in parent["payload"]:
                parent["payload"]["children"] = parent["children"]

            parent["children"].append(new_block)

            # TRADE-OFF: Notion API impone un vincolo rigido di massimo 2 livelli di nidificazione
            # all'interno di una singola chiamata 'append block children' (radice -> figli -> nipoti).
            # Limitando la profondità dello stack a 2 (len(list_stack) < 3), qualsiasi ulteriore sotto-livello
            # viene posizionato come elemento affine evitando errori HTTP 400 (validation_error).
            if len(list_stack) < 3:
                list_stack.append({
                    "indent": indent,
                    "type": item_type,
                    "payload": new_block[item_type],
                    "children": []
                })
            continue

        # ── List Continuation Handling ──────────────────────────────────────
        # Se una riga di testo è indentata (>= 2 spazi) e segue un elemento di lista attivo,
        # la accorpiamo all'elemento corrente per preservare la numerazione e il flusso logico.
        if len(list_stack) > 1 and indent >= 2 and not s.startswith(("#", "```", "$$", ">", "|", "---", "![")):
            parent = list_stack[-1]
            if parent["payload"] is not None:
                parent["payload"]["rich_text"].append({"type": "text", "text": {"content": " "}})
                parent["payload"]["rich_text"].extend(parse_rich_text(s))
                continue

        # ── Images ──────────────────────────────────────────────────────────
        img_match = re.match(r'^!\[([^\]]*)\]\((https?://[^\)]+)\)$', s)
        if img_match:
            flush_list()
            img_url = img_match.group(2)
            blocks.append({
                "object": "block",
                "type": "image",
                "image": {
                    "type": "external",
                    "external": {"url": img_url}
                }
            })
            continue

        # ── Paragraph ───────────────────────────────────────────────────────
        flush_list()
        blocks.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {"rich_text": parse_rich_text(s)},
        })

    flush_table()
    flush_list()
    return blocks
