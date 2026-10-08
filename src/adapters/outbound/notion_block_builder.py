import re
from typing import List, Dict, Any

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
            if in_code_block:
                # Close code block
                full_code = "\n".join(code_block_buf)
                # If code is larger than Notion block limit, chunk safely
                while full_code:
                    chunk = full_code[:NOTION_MAX_BLOCK_CHARS]
                    full_code = full_code[NOTION_MAX_BLOCK_CHARS:]
                    blocks.append({
                        "object": "block",
                        "type": "code",
                        "code": {
                            "language": code_block_lang,
                            "rich_text": [{"type": "text", "text": {"content": chunk}}],
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
            table_buf.append(s)
            continue
        else:
            flush_table()

        # ── Horizontal Divider ──────────────────────────────────────────────
        if s == "---":
            if blocks and blocks[-1]["type"] != "divider":
                blocks.append({"object": "block", "type": "divider", "divider": {}})
            continue

        # ── Blockquote ──────────────────────────────────────────────────────
        if s.startswith(">"):
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
            content = s[4:].strip()
            blocks.append({
                "object": "block",
                "type": "heading_3",
                "heading_3": {"rich_text": parse_rich_text(content[:NOTION_MAX_BLOCK_CHARS])},
            })
            continue

        # Fallback for H4 (Notion does not have heading_4; downgrade to heading_3)
        if s.startswith("#### "):
            content = s[5:].strip()
            blocks.append({
                "object": "block",
                "type": "heading_3",
                "heading_3": {"rich_text": parse_rich_text(content[:NOTION_MAX_BLOCK_CHARS])},
            })
            continue

        # ── Lists ───────────────────────────────────────────────────────────
        if s.startswith(("- ", "* ")):
            content = s[2:].strip()
            blocks.append({
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": parse_rich_text(content)},
            })
            continue

        if len(s) > 2 and s[0].isdigit() and s[1] in ".)" and s[2] == " ":
            content = s[3:].strip()
            blocks.append({
                "object": "block",
                "type": "numbered_list_item",
                "numbered_list_item": {"rich_text": parse_rich_text(content)},
            })
            continue

        # ── Images ──────────────────────────────────────────────────────────
        import re
        img_match = re.match(r'^!\[([^\]]*)\]\((https?://[^\)]+)\)$', s)
        if img_match:
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
        blocks.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {"rich_text": parse_rich_text(s)},
        })

    flush_table()
    return blocks
