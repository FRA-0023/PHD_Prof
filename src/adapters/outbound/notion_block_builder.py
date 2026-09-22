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

def parse_rich_text(line: str) -> List[Dict[str, Any]]:
    """
    Converts a Markdown line into Notion rich_text objects.
    Handles:
      - **bold** -> rich_text with bold annotation
      - $formula$ -> inline equation object
      - plain text -> text object
    Truncates individual segments to NOTION_MAX_BLOCK_CHARS.
    """
    parts: List[Dict[str, Any]] = []
    pattern = re.compile(r'(\*\*(.+?)\*\*|\$(?!\$)(.+?)(?<!\$)\$)')
    cursor = 0

    for m in pattern.finditer(line):
        if m.start() > cursor:
            seg = line[cursor:m.start()][:NOTION_MAX_BLOCK_CHARS]
            if seg:
                parts.append({"type": "text", "text": {"content": seg}})
        if m.group(0).startswith("**"):
            seg = m.group(2)[:NOTION_MAX_BLOCK_CHARS]
            parts.append({
                "type": "text",
                "text": {"content": seg},
                "annotations": {"bold": True},
            })
        else:
            expr = m.group(3)[:NOTION_MAX_BLOCK_CHARS]
            parts.append({"type": "equation", "equation": {"expression": expr}})
        cursor = m.end()

    if cursor < len(line):
        seg = line[cursor:][:NOTION_MAX_BLOCK_CHARS]
        if seg:
            parts.append({"type": "text", "text": {"content": seg}})

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
            blocks.append({"object": "block", "type": "divider", "divider": {}})
            continue

        # ── Blockquote ──────────────────────────────────────────────────────
        if s.startswith("> "):
            content = s[2:].strip()
            blocks.append({
                "object": "block",
                "type": "quote",
                "quote": {"rich_text": parse_rich_text(content)},
            })
            continue

        # ── Headings with Dividers ──────────────────────────────────────────
        if s.startswith("# ") and not s.startswith("## "):
            if blocks:
                blocks.append({"object": "block", "type": "divider", "divider": {}})
            content = s[2:].strip()
            blocks.append({
                "object": "block",
                "type": "heading_1",
                "heading_1": {"rich_text": parse_rich_text(content[:NOTION_MAX_BLOCK_CHARS])},
            })
            continue

        if s.startswith("## ") and not s.startswith("### "):
            if blocks:
                blocks.append({"object": "block", "type": "divider", "divider": {}})
            content = s[3:].strip()
            blocks.append({
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": parse_rich_text(content[:NOTION_MAX_BLOCK_CHARS])},
            })
            continue

        if s.startswith("### "):
            if blocks:
                blocks.append({"object": "block", "type": "divider", "divider": {}})
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
