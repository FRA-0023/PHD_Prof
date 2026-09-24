import pytest
from src.adapters.outbound.notion_block_builder import (
    parse_rich_text,
    build_notion_blocks,
    NOTION_MAX_BLOCK_CHARS,
    normalize_sentence_spacing,
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



