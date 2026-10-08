import pytest
from src.adapters.outbound.notion_block_builder import (
    parse_rich_text,
    build_notion_blocks,
    NOTION_MAX_BLOCK_CHARS,
    normalize_sentence_spacing,
    sanitize_mermaid_mindmap,
)

def test_parse_rich_text_plain():
    parts = parse_rich_text("Hello world")
    assert len(parts) == 1
    assert parts[0]["type"] == "text"
    assert parts[0]["text"]["content"] == "Hello world"

def test_parse_rich_text_bold():
    parts = parse_rich_text("This is **critical** concept.")
    assert len(parts) == 3
    assert parts[0]["text"]["content"] == "This is "
    assert parts[1]["text"]["content"] == "critical"
    assert parts[1]["annotations"]["bold"] is True
    assert parts[2]["text"]["content"] == " concept."

def test_parse_rich_text_inline_math():
    parts = parse_rich_text("Given the formula $E=mc^2$, we deduce...")
    assert len(parts) == 3
    assert parts[0]["text"]["content"] == "Given the formula "
    assert parts[1]["type"] == "equation"
    assert parts[1]["equation"]["expression"] == "E=mc^2"
    assert parts[2]["text"]["content"] == ", we deduce..."

def test_parse_rich_text_truncation():
    long_str = "a" * (NOTION_MAX_BLOCK_CHARS + 500)
    parts = parse_rich_text(long_str)
    assert len(parts[0]["text"]["content"]) <= NOTION_MAX_BLOCK_CHARS

def test_build_notion_blocks_headings_and_dividers():
    md = "# Main Title\nSome introduction.\n## Section Title\nDetailed analysis."
    blocks = build_notion_blocks(md)
    # H1 is first -> no divider before it
    assert blocks[0]["type"] == "heading_1"
    assert blocks[0]["heading_1"]["rich_text"][0]["text"]["content"] == "Main Title"
    # Paragraph
    assert blocks[1]["type"] == "paragraph"
    # Divider before H2
    assert blocks[2]["type"] == "divider"
    assert blocks[3]["type"] == "heading_2"
    assert blocks[3]["heading_2"]["rich_text"][0]["text"]["content"] == "Section Title"

def test_build_notion_blocks_code_block():
    md = "Here is the implementation:\n```python\ndef solve():\n    return 42\n```\nDone."
    blocks = build_notion_blocks(md)
    code_blocks = [b for b in blocks if b["type"] == "code"]
    assert len(code_blocks) == 1
    assert code_blocks[0]["code"]["language"] == "python"
    assert "def solve():" in code_blocks[0]["code"]["rich_text"][0]["text"]["content"]

def test_build_notion_blocks_display_math():
    md = "$$\n\\hat{y} = \\sigma(Wx + b)\n$$\n$$E = mc^2$$"
    blocks = build_notion_blocks(md)
    eq_blocks = [b for b in blocks if b["type"] == "equation"]
    assert len(eq_blocks) == 2
    assert "\\hat{y} = \\sigma(Wx + b)" in eq_blocks[0]["equation"]["expression"]
    assert eq_blocks[1]["equation"]["expression"] == "E = mc^2"

def test_build_notion_blocks_blockquote():
    md = "> Important theorem statement"
    blocks = build_notion_blocks(md)
    assert blocks[0]["type"] == "quote"
    assert blocks[0]["quote"]["rich_text"][0]["text"]["content"] == "Important theorem statement"

def test_build_notion_blocks_h4_fallback():
    md = "#### Sub-sub heading"
    blocks = build_notion_blocks(md)
    # Notion does not support H4; downgraded to heading_3
    assert blocks[0]["type"] == "heading_3"

def test_normalize_sentence_spacing():
    assert normalize_sentence_spacing("concept.Next") == "concept. Next"
    assert normalize_sentence_spacing("value:Key") == "value: Key"
    assert normalize_sentence_spacing("first,second") == "first, second"
    assert normalize_sentence_spacing("clause;another") == "clause; another"
    assert normalize_sentence_spacing("pi is 3.14 approx") == "pi is 3.14 approx"
    assert normalize_sentence_spacing("already separated. Words.") == "already separated. Words."

def test_no_duplicate_dividers():
    md = "### Previous H3\nSome text\n---\n## Next Section\nMore text"
    blocks = build_notion_blocks(md)
    # Filter only divider blocks
    dividers = [b for b in blocks if b["type"] == "divider"]
    assert len(dividers) == 1

def test_no_divider_before_h3():
    md = "# Main Title\nIntroductory text\n## Section\nSome text\n### Subsection\nMore text"
    blocks = build_notion_blocks(md)
    # Divider before H2, but NO divider before H3
    dividers = [b for b in blocks if b["type"] == "divider"]
    assert len(dividers) == 1
    # Check types sequence: heading_1, paragraph, divider, heading_2, paragraph, heading_3, paragraph
    types = [b["type"] for b in blocks]
    assert types == ["heading_1", "paragraph", "divider", "heading_2", "paragraph", "heading_3", "paragraph"]

def test_parse_rich_text_italic():
    parts = parse_rich_text("This is *italicized* thought.")
    assert len(parts) == 3
    assert parts[1]["text"]["content"] == "italicized"
    assert parts[1]["annotations"]["italic"] is True

def test_parse_rich_text_bold_italic():
    parts = parse_rich_text("This is ***crucial premise*** here.")
    assert len(parts) == 3
    assert parts[1]["text"]["content"] == "crucial premise"
    assert parts[1]["annotations"]["bold"] is True
    assert parts[1]["annotations"]["italic"] is True

def test_parse_rich_text_code():
    parts = parse_rich_text("Call the `evaluate()` function.")
    assert len(parts) == 3
    assert parts[1]["text"]["content"] == "evaluate()"
    assert parts[1]["annotations"]["code"] is True

def test_parse_rich_text_example_pattern():
    parts = parse_rich_text("**Example:** *In banking monoliths, decoupling starts with strangler fig.*")
    assert parts[0]["text"]["content"] == "Example:"
    assert parts[0]["annotations"]["bold"] is True
    assert parts[1]["text"]["content"] == " "
    assert "banking monoliths" in parts[2]["text"]["content"]
    assert parts[2]["annotations"]["italic"] is True

def test_build_notion_blocks_blockquote_with_formatting():
    md = "> **Core Insight:** Loose coupling minimizes systemic fragility."
    blocks = build_notion_blocks(md)
    assert len(blocks) == 1
    assert blocks[0]["type"] == "quote"
    rich_text = blocks[0]["quote"]["rich_text"]
    assert rich_text[0]["text"]["content"] == "Core Insight:"
    assert rich_text[0]["annotations"]["bold"] is True
    assert "Loose coupling" in rich_text[1]["text"]["content"]

def test_parse_rich_text_italic_with_nested_bold():
    line = "**Example:** *Consider a **stationary series** before shock.*"
    parts = parse_rich_text(line)
    # Check Example: is bold
    assert parts[0]["text"]["content"] == "Example:"
    assert parts[0]["annotations"]["bold"] is True
    # Check italic prefix
    italic_prefix = next(p for p in parts if "Consider a " in p["text"]["content"])
    assert italic_prefix["annotations"]["italic"] is True
    # Check bold+italic nested text
    nested_bold = next(p for p in parts if p["text"]["content"] == "stationary series")
    assert nested_bold["annotations"]["bold"] is True
    assert nested_bold["annotations"]["italic"] is True

def test_parse_rich_text_formula_inside_bold():
    line = "**Sample size ($T=100$):** critical baseline."
    parts = parse_rich_text(line)
    eq_parts = [p for p in parts if p.get("type") == "equation"]
    assert len(eq_parts) == 1
    assert eq_parts[0]["equation"]["expression"] == "T=100"
    assert eq_parts[0]["annotations"]["bold"] is True

def test_parse_rich_text_formula_inside_italic():
    line = "**Example:** *Simulated white noise with $T=100$ observations.*"
    parts = parse_rich_text(line)
    eq_parts = [p for p in parts if p.get("type") == "equation"]
    assert len(eq_parts) == 1
    assert eq_parts[0]["equation"]["expression"] == "T=100"
    assert eq_parts[0]["annotations"]["italic"] is True

def test_build_notion_blocks_bullet_with_equation():
    md = "- $$n_i = |F_i|$$"
    blocks = build_notion_blocks(md)
    assert len(blocks) == 1
    assert blocks[0]["type"] == "bulleted_list_item"
    rich_text = blocks[0]["bulleted_list_item"]["rich_text"]
    assert any(r.get("type") == "equation" and r["equation"]["expression"] == "n_i = |F_i|" for r in rich_text)


def test_build_notion_blocks_standard_table():
    md = (
        "| Feature | CPU | GPU |\n"
        "| :--- | :--- | :--- |\n"
        "| **Role** | Expert | Workers |\n"
        "| **Cores** | 4-128 | 10,000+ |"
    )
    blocks = build_notion_blocks(md)
    assert len(blocks) == 1
    assert blocks[0]["type"] == "table"
    table = blocks[0]["table"]
    assert table["table_width"] == 3
    assert table["has_column_header"] is True
    assert len(table["children"]) == 3  # 1 header + 2 rows

    # Header verification
    header_row = table["children"][0]["table_row"]["cells"]
    assert len(header_row) == 3
    assert header_row[0][0]["text"]["content"] == "Feature"
    assert header_row[1][0]["text"]["content"] == "CPU"
    assert header_row[2][0]["text"]["content"] == "GPU"

    # Data row with formatting
    row1 = table["children"][1]["table_row"]["cells"]
    assert row1[0][0]["text"]["content"] == "Role"
    assert row1[0][0]["annotations"]["bold"] is True
    assert row1[1][0]["text"]["content"] == "Expert"


def test_build_notion_blocks_table_with_blank_lines():
    # Tollera righe vuote accidentali tra le righe della tabella
    md = (
        "| Feature | CPU | GPU |\n\n"
        "| :--- | :--- | :--- |\n\n"
        "| **Role** | Expert | Workers |\n\n"
        "| **Cores** | 4-128 | 10,000+ |\n"
    )
    blocks = build_notion_blocks(md)
    assert len(blocks) == 1
    assert blocks[0]["type"] == "table"
    table = blocks[0]["table"]
    assert table["table_width"] == 3
    assert len(table["children"]) == 3


def test_build_notion_blocks_table_with_escaped_pipe():
    md = (
        "| Expression | Meaning |\n"
        "| :--- | :--- |\n"
        "| $P(A \\| B)$ | Conditional probability |"
    )
    blocks = build_notion_blocks(md)
    assert len(blocks) == 1
    assert blocks[0]["type"] == "table"
    table = blocks[0]["table"]
    assert table["table_width"] == 2
    assert len(table["children"]) == 2


def test_build_notion_blocks_nested_bullet_points():
    md = (
        "* **Mapping (List(K2, V2)):** Each chunk is processed by a map function.\n"
        "    * Chunk 1: (Deer, 1)\n"
        "    * Chunk 2: (Car, 1)\n"
        "* **Shuffling (K2, List(V2)):** All pairs grouped by word."
    )
    blocks = build_notion_blocks(md)
    # Only 2 root blocks: Mapping and Shuffling
    assert len(blocks) == 2
    assert blocks[0]["type"] == "bulleted_list_item"
    assert blocks[1]["type"] == "bulleted_list_item"

    # Mapping must contain 2 nested children
    mapping_payload = blocks[0]["bulleted_list_item"]
    assert "children" in mapping_payload
    assert len(mapping_payload["children"]) == 2
    assert mapping_payload["children"][0]["type"] == "bulleted_list_item"
    assert mapping_payload["children"][1]["type"] == "bulleted_list_item"
    assert "Chunk 1" in mapping_payload["children"][0]["bulleted_list_item"]["rich_text"][0]["text"]["content"]
    assert "Chunk 2" in mapping_payload["children"][1]["bulleted_list_item"]["rich_text"][0]["text"]["content"]

    # Leaf children must NEVER contain an empty 'children' key (Notion API rejects empty children with 400)
    assert "children" not in mapping_payload["children"][0]["bulleted_list_item"]
    assert "children" not in mapping_payload["children"][1]["bulleted_list_item"]

    # Shuffling has no children -> no 'children' key
    assert "children" not in blocks[1]["bulleted_list_item"]


def test_build_notion_blocks_mixed_nested_lists():
    md = (
        "1. Primary Phase\n"
        "    - Sub-bullet A\n"
        "    - Sub-bullet B\n"
        "2. Secondary Phase"
    )
    blocks = build_notion_blocks(md)
    assert len(blocks) == 2
    assert blocks[0]["type"] == "numbered_list_item"
    assert blocks[1]["type"] == "numbered_list_item"

    p1 = blocks[0]["numbered_list_item"]
    assert "children" in p1
    assert len(p1["children"]) == 2
    assert p1["children"][0]["type"] == "bulleted_list_item"
    assert p1["children"][1]["type"] == "bulleted_list_item"


def test_build_notion_blocks_list_continuation():
    md = (
        "1. **Training MSE:** For this specific model, residuals are zero.\n"
        "    Consequently, the training MSE will be exactly 0.\n"
        "2. **Test MSE:** High variance expected."
    )
    blocks = build_notion_blocks(md)
    assert len(blocks) == 2
    assert blocks[0]["type"] == "numbered_list_item"
    assert blocks[1]["type"] == "numbered_list_item"

    # Continuation text is merged into the first item's rich_text
    full_text = " ".join(
        t["text"]["content"] for t in blocks[0]["numbered_list_item"]["rich_text"] if "text" in t
    )
    assert "residuals are zero" in full_text
    assert "Consequently, the training MSE will be exactly 0" in full_text


def test_build_notion_blocks_max_depth_safety():
    # Notion API limits nesting to 2 levels in batch append
    md = (
        "- Level 0\n"
        "    - Level 1\n"
        "        - Level 2\n"
        "            - Level 3 (should be capped at level 2 without error)"
    )
    blocks = build_notion_blocks(md)
    assert len(blocks) == 1
    lvl0 = blocks[0]["bulleted_list_item"]
    assert len(lvl0["children"]) == 1
    lvl1 = lvl0["children"][0]["bulleted_list_item"]
    assert len(lvl1["children"]) == 2  # Level 2 and Level 3 both placed under Level 1 as siblings
    lvl2 = lvl1["children"][0]["bulleted_list_item"]
    assert "children" not in lvl2  # Not deeply nested beyond level 2


def test_sanitize_mermaid_mindmap_escapes_parentheses_and_operators():
    raw_mermaid = (
        "mindmap\n"
        "  root((Big Data Systems))\n"
        "    Architecture\n"
        "      Scale (KB to YB)\n"
        "      Moore's Law((N_T(t) proportional to 2^(t/tau)))\n"
        "      Consistency (C)\n"
        "      LLM Wall (m=1) -> Bandwidth Bound\n"
        "      Clean Leaf Node\n"
        '      ["Already Quoted Node"]\n'
    )
    sanitized = sanitize_mermaid_mindmap(raw_mermaid)
    lines = sanitized.splitlines()

    assert lines[0] == "mindmap"
    assert lines[1] == '  root(("Big Data Systems"))'
    assert lines[2] == "    Architecture"
    assert lines[3] == '      ["Scale (KB to YB)"]'
    assert lines[4] == '      ["Moore\'s Law: N_T(t) proportional to 2^(t/tau)"]'
    assert lines[5] == '      ["Consistency (C)"]'
    assert lines[6] == '      ["LLM Wall (m=1) -> Bandwidth Bound"]'
    assert lines[7] == "      Clean Leaf Node"
    assert lines[8] == '      ["Already Quoted Node"]'


def test_build_notion_blocks_large_code_block_preserves_single_block_integrity():
    # Code block larger than NOTION_MAX_BLOCK_CHARS (e.g. 4500 chars)
    # Must NOT be sliced into multiple code blocks, but kept in 1 block with multiple rich_text chunks
    long_code = "print('hello world')\n" * 250  # ~5250 chars
    md = f"```python\n{long_code}```"

    blocks = build_notion_blocks(md)
    code_blocks = [b for b in blocks if b["type"] == "code"]

    # Critical invariant: 1 block only!
    assert len(code_blocks) == 1
    assert code_blocks[0]["code"]["language"] == "python"

    rich_text = code_blocks[0]["code"]["rich_text"]
    assert len(rich_text) > 1  # multiple chunks
    total_reconstructed = "".join(chunk["text"]["content"] for chunk in rich_text)
    assert total_reconstructed == long_code.strip()






