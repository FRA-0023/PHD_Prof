import pytest
from src.adapters.outbound.notion_block_builder import (
    parse_rich_text,
    build_notion_blocks,
    NOTION_MAX_BLOCK_CHARS,
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
