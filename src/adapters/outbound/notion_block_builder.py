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


def build_notion_blocks(markdown_text: str) -> List[Dict[str, Any]]:
    """
    Parses full Markdown text into a list of Notion-compliant block dictionaries.
    Supports:
      - Multiline and single-line LaTeX display equations ($$...$$)
      - Fenced code blocks (```lang ... ```)
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

    for line in lines:
        s = line.strip()

        # ── Code Block Handling ──────────────────────────────────────────────
        if s.startswith("```"):
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
            expr = s[2:-2].strip()
            blocks.append({
                "object": "block",
                "type": "equation",
                "equation": {"expression": expr[:NOTION_MAX_BLOCK_CHARS]},
            })
            continue

        if not s or s.isspace():
            continue

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

        # ── Paragraph ───────────────────────────────────────────────────────
        blocks.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {"rich_text": parse_rich_text(s)},
        })

    return blocks
